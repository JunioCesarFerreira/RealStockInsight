package market

import (
	"testing"
	"time"
)

func sampleChain() []Trade {
	ts := time.Date(2024, 1, 2, 3, 4, 5, 123456000, time.UTC)
	trades := []Trade{
		{Seq: 1, Timestamp: ts, Ticker: "AAPL", Amount: 3, Price: "185.64", Currency: "USD",
			SellerID: MarketID, BuyerID: "201264f3-3148-4d2d-a1f5-fdb01f4eeaad"},
		{Seq: 2, Timestamp: ts.Add(time.Second), Ticker: "MSFT", Amount: 10, Price: "370.60", Currency: "USD",
			SellerID: "7ac0dbbe-f296-47f3-85f6-345891197df6", BuyerID: MarketID},
		{Seq: 3, Timestamp: ts.Add(2 * time.Second), Ticker: "AAPL", Amount: 1, Price: "186.00", Currency: "USD",
			SellerID: MarketID, BuyerID: "7ac0dbbe-f296-47f3-85f6-345891197df6"},
	}
	prev := genesisHash
	for i := range trades {
		trades[i].PrevHash = prev
		trades[i].Hash = blockHash(trades[i])
		prev = trades[i].Hash
	}
	return trades
}

func verify(trades []Trade) error {
	v := newChainVerifier()
	for _, t := range trades {
		if err := v.add(t); err != nil {
			return err
		}
	}
	return nil
}

func TestBlockHashIsDeterministic(t *testing.T) {
	trade := sampleChain()[0]
	if blockHash(trade) != blockHash(trade) {
		t.Fatal("hash must be deterministic")
	}
	if len(trade.Hash) != 64 {
		t.Fatalf("expected SHA-256 hex digest, got %q", trade.Hash)
	}
}

func TestValidChainVerifies(t *testing.T) {
	if err := verify(sampleChain()); err != nil {
		t.Fatalf("valid chain rejected: %v", err)
	}
}

func TestTamperedContentIsDetected(t *testing.T) {
	trades := sampleChain()
	trades[1].Amount = 1000 // altera uma negociação já registrada
	if err := verify(trades); err == nil {
		t.Fatal("tampered amount was not detected")
	}
}

func TestRewrittenRecordIsDetected(t *testing.T) {
	trades := sampleChain()
	// Altera o preço e recalcula o próprio hash: o registro seguinte deixa de apontar para ele
	trades[0].Price = "1.00"
	trades[0].Hash = blockHash(trades[0])
	if err := verify(trades); err == nil {
		t.Fatal("rewritten record was not detected")
	}
}

func TestRemovedRecordIsDetected(t *testing.T) {
	trades := sampleChain()
	if err := verify([]Trade{trades[0], trades[2]}); err == nil {
		t.Fatal("removed record was not detected")
	}
}
