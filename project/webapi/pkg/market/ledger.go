package market

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"
)

// Hash anterior ao primeiro registro da cadeia
const genesisHash = "0000000000000000000000000000000000000000000000000000000000000000"

// Formato do timestamp no conteúdo do hash (precisão de microssegundos, como no PostgreSQL)
const hashTimeLayout = "2006-01-02T15:04:05.000000Z"

// Trade é uma negociação registrada no ledger (tabela STOCK_EXCHANGES)
type Trade struct {
	Seq        int64       `json:"seq"`
	Timestamp  time.Time   `json:"timestamp"`
	Ticker     string      `json:"ticker"`
	Amount     int         `json:"amount"`
	Price      json.Number `json:"price"`
	Total      json.Number `json:"total,omitempty"`
	Currency   string      `json:"currency"`
	SellerID   string      `json:"seller_id"`
	SellerName string      `json:"seller,omitempty"`
	BuyerID    string      `json:"buyer_id"`
	BuyerName  string      `json:"buyer,omitempty"`
	PrevHash   string      `json:"prev_hash"`
	Hash       string      `json:"hash"`
}

// blockHash calcula o hash SHA-256 do registro, encadeado ao hash do registro anterior.
// Price deve estar no formato textual do NUMERIC(10,2) (ex.: "123.40") e os IDs no formato canônico de UUID.
func blockHash(t Trade) string {
	payload := strings.Join([]string{
		t.PrevHash,
		t.Timestamp.UTC().Format(hashTimeLayout),
		t.Ticker,
		t.Price.String(),
		t.Currency,
		strconv.Itoa(t.Amount),
		t.SellerID,
		t.BuyerID,
	}, "|")
	sum := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(sum[:])
}

// chainVerifier confere, em ordem, se cada registro aponta para o anterior e se seu hash confere com o conteúdo
type chainVerifier struct {
	prev   string
	blocks int64
}

func newChainVerifier() *chainVerifier {
	return &chainVerifier{prev: genesisHash}
}

// add verifica o próximo registro da cadeia
func (v *chainVerifier) add(t Trade) error {
	if t.PrevHash != v.prev {
		return fmt.Errorf("record %d does not point to the previous record (prev_hash mismatch)", t.Seq)
	}
	if expected := blockHash(t); t.Hash != expected {
		return fmt.Errorf("record %d content does not match its hash", t.Seq)
	}
	v.prev = t.Hash
	v.blocks++
	return nil
}
