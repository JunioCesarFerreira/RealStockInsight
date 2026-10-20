// Package market implementa o mercado descentralizado simulado: contas dos investidores,
// execução de ordens de compra e venda e o registro encadeado (ledger) das negociações.
//
// As ordens são executadas ao preço de referência mais recente do ativo (último preço do feed,
// tabela TRENDS), tendo como contraparte o pool de liquidez do mercado (MarketID). Cada negociação
// é anexada ao ledger com o hash do registro anterior, o que torna qualquer alteração no histórico
// detectável (GET /market/ledger/verify).
package market

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"main.go/pkg/httpjson"
)

// MarketID identifica o pool de liquidez, contraparte de todas as ordens
const MarketID = "00000000-0000-0000-0000-000000000000"

const (
	currency = "USD"
	// Chave do lock que serializa as escritas no ledger (a cadeia de hashes exige ordem total)
	ledgerLockKey = 7061
	// Limite de quantidade por ordem
	maxOrderAmount = 1_000_000
)

var uuidPattern = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)

// Handler agrupa os endpoints do mercado
type Handler struct {
	DB *sql.DB
}

// apiError é um erro de regra de negócio com o status HTTP correspondente
type apiError struct {
	status  int
	message string
}

func (e *apiError) Error() string { return e.message }

func reject(status int, format string, args ...any) error {
	return &apiError{status: status, message: fmt.Sprintf(format, args...)}
}

// fail responde o erro com o status adequado; erros inesperados viram 500
func fail(w http.ResponseWriter, err error) {
	var apiErr *apiError
	if errors.As(err, &apiErr) {
		httpjson.Error(w, apiErr.status, apiErr.message)
		return
	}
	log.Println("market error:", err)
	httpjson.Error(w, http.StatusInternalServerError, "internal error")
}

// Account é a posição de um investidor, avaliada ao preço de referência mais recente
type Account struct {
	TraderID        string         `json:"trader_id"`
	Name            string         `json:"name"`
	Cash            json.Number    `json:"cash"`
	InitialCash     json.Number    `json:"initial_cash"`
	StocksValue     json.Number    `json:"stocks_value"`
	NetWorth        json.Number    `json:"net_worth"`
	InitialNetWorth json.Number    `json:"initial_net_worth"`
	BuyAndHoldValue json.Number    `json:"buy_and_hold_value"`
	Result          json.Number    `json:"result"`
	ResultPct       float64        `json:"result_pct"`
	Buys            int            `json:"buys"`
	Sells           int            `json:"sells"`
	LastTradeAt     *time.Time     `json:"last_trade_at"`
	OpenedAt        time.Time      `json:"opened_at"`
	Holdings        map[string]int `json:"holdings,omitempty"`
}

type openAccountRequest struct {
	TraderID        string         `json:"trader_id"`
	InitialCash     json.Number    `json:"initial_cash"`
	InitialHoldings map[string]int `json:"initial_holdings"`
}

type orderRequest struct {
	TraderID string `json:"trader_id"`
	Ticker   string `json:"ticker"`
	Amount   int    `json:"amount"`
}

type orderResult struct {
	Side    string      `json:"side"`
	Trade   Trade       `json:"trade"`
	Cash    json.Number `json:"cash"`
	Holding int         `json:"holding"`
}

// Accounts lista as contas (GET) ou abre uma conta (POST)
func (h *Handler) Accounts(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		accounts, err := h.accounts(r.Context(), "")
		if err != nil {
			fail(w, err)
			return
		}
		httpjson.Write(w, http.StatusOK, accounts)
	case http.MethodPost:
		h.openAccount(w, r)
	default:
		httpjson.Error(w, http.StatusMethodNotAllowed, "method not allowed")
	}
}

// Account retorna uma conta com a carteira detalhada (GET /market/accounts/{trader_id})
func (h *Handler) Account(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpjson.Error(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	traderID := strings.TrimPrefix(r.URL.Path, "/market/accounts/")
	if !uuidPattern.MatchString(traderID) {
		httpjson.Error(w, http.StatusBadRequest, "invalid trader id")
		return
	}
	account, err := h.account(r.Context(), traderID)
	if err != nil {
		fail(w, err)
		return
	}
	httpjson.Write(w, http.StatusOK, account)
}

// openAccount abre a conta de um investidor cadastrado em TRADERS. A operação é idempotente:
// se a conta já existir, ela é retornada sem alterações (200); caso contrário, é criada (201).
func (h *Handler) openAccount(w http.ResponseWriter, r *http.Request) {
	var req openAccountRequest
	if err := httpjson.Decode(w, r, &req); err != nil {
		httpjson.Error(w, http.StatusBadRequest, "invalid JSON body: "+err.Error())
		return
	}
	if !uuidPattern.MatchString(req.TraderID) {
		httpjson.Error(w, http.StatusBadRequest, "invalid trader id")
		return
	}
	if cash, err := req.InitialCash.Float64(); err != nil || cash < 0 {
		httpjson.Error(w, http.StatusBadRequest, "initial_cash must be a non-negative number")
		return
	}
	for ticker, amount := range req.InitialHoldings {
		if amount < 0 || strings.TrimSpace(ticker) == "" {
			httpjson.Error(w, http.StatusBadRequest, "initial_holdings must map tickers to non-negative amounts")
			return
		}
	}

	created, err := h.createAccount(r.Context(), req)
	if err != nil {
		fail(w, err)
		return
	}
	account, err := h.account(r.Context(), strings.ToLower(req.TraderID))
	if err != nil {
		fail(w, err)
		return
	}
	status := http.StatusOK
	if created {
		status = http.StatusCreated
	}
	httpjson.Write(w, status, account)
}

func (h *Handler) createAccount(ctx context.Context, req openAccountRequest) (bool, error) {
	tx, err := h.DB.BeginTx(ctx, nil)
	if err != nil {
		return false, err
	}
	defer tx.Rollback()

	var exists bool
	if err := tx.QueryRowContext(ctx, "SELECT EXISTS (SELECT 1 FROM TRADERS WHERE id = $1)", req.TraderID).Scan(&exists); err != nil {
		return false, err
	}
	if !exists {
		return false, reject(http.StatusNotFound, "trader %s is not registered", req.TraderID)
	}
	if strings.EqualFold(req.TraderID, MarketID) {
		return false, reject(http.StatusBadRequest, "the market liquidity pool cannot open an account")
	}

	res, err := tx.ExecContext(ctx, `INSERT INTO ACCOUNTS (trader_id, cash, initial_cash) VALUES ($1, $2::numeric, $2::numeric)
		ON CONFLICT (trader_id) DO NOTHING`, req.TraderID, req.InitialCash.String())
	if err != nil {
		return false, err
	}
	if n, _ := res.RowsAffected(); n == 0 {
		return false, nil // conta já existente
	}

	for ticker, amount := range req.InitialHoldings {
		ticker = normalizeTicker(ticker)
		price, err := latestPrice(ctx, tx, ticker)
		if err != nil {
			return false, err
		}
		_, err = tx.ExecContext(ctx, `INSERT INTO HOLDINGS (trader_id, ticker, amount, initial_amount, initial_price)
			VALUES ($1, $2, $3, $3, $4::numeric)`, req.TraderID, ticker, amount, price)
		if err != nil {
			return false, err
		}
	}
	return true, tx.Commit()
}

// Buy executa uma ordem de compra (POST /stocks/buy)
func (h *Handler) Buy(w http.ResponseWriter, r *http.Request) { h.order(w, r, "buy") }

// Sell executa uma ordem de venda (POST /stocks/sell)
func (h *Handler) Sell(w http.ResponseWriter, r *http.Request) { h.order(w, r, "sell") }

func (h *Handler) order(w http.ResponseWriter, r *http.Request, side string) {
	if r.Method != http.MethodPost {
		httpjson.Error(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	var req orderRequest
	if err := httpjson.Decode(w, r, &req); err != nil {
		httpjson.Error(w, http.StatusBadRequest, "invalid JSON body: "+err.Error())
		return
	}
	req.Ticker = normalizeTicker(req.Ticker)
	switch {
	case !uuidPattern.MatchString(req.TraderID):
		httpjson.Error(w, http.StatusBadRequest, "invalid trader id")
		return
	case req.Ticker == "":
		httpjson.Error(w, http.StatusBadRequest, "ticker is required")
		return
	case req.Amount < 1 || req.Amount > maxOrderAmount:
		httpjson.Error(w, http.StatusBadRequest, fmt.Sprintf("amount must be between 1 and %d", maxOrderAmount))
		return
	}

	result, err := h.execute(r.Context(), side, req)
	if err != nil {
		fail(w, err)
		return
	}
	httpjson.Write(w, http.StatusOK, result)
}

// execute liquida a ordem atomicamente: atualiza caixa e carteira e anexa a negociação ao ledger
func (h *Handler) execute(ctx context.Context, side string, req orderRequest) (*orderResult, error) {
	tx, err := h.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()

	// Serializa as negociações: o ledger encadeado exige ordem total
	if _, err := tx.ExecContext(ctx, "SELECT pg_advisory_xact_lock($1)", ledgerLockKey); err != nil {
		return nil, err
	}

	var traderID string
	err = tx.QueryRowContext(ctx, "SELECT trader_id::text FROM ACCOUNTS WHERE trader_id = $1", req.TraderID).Scan(&traderID)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, reject(http.StatusNotFound, "account %s not found: open it with POST /market/accounts", req.TraderID)
	}
	if err != nil {
		return nil, err
	}

	price, err := latestPrice(ctx, tx, req.Ticker)
	if err != nil {
		return nil, err
	}
	var total string
	if err := tx.QueryRowContext(ctx, "SELECT ($1::numeric * $2)::numeric(14,2)::text", price, req.Amount).Scan(&total); err != nil {
		return nil, err
	}

	now := time.Now().UTC().Truncate(time.Microsecond)
	result := &orderResult{Side: side}
	var cash string
	var seller, buyer string

	if side == "buy" {
		err = tx.QueryRowContext(ctx, `UPDATE ACCOUNTS SET cash = cash - $2::numeric, trades_buy = trades_buy + 1, last_trade_at = $3
			WHERE trader_id = $1 AND cash >= $2::numeric RETURNING cash::text`, traderID, total, now).Scan(&cash)
		if errors.Is(err, sql.ErrNoRows) {
			return nil, reject(http.StatusUnprocessableEntity, "insufficient funds: %d %s cost %s", req.Amount, req.Ticker, total)
		}
		if err != nil {
			return nil, err
		}
		err = tx.QueryRowContext(ctx, `INSERT INTO HOLDINGS (trader_id, ticker, amount) VALUES ($1, $2, $3)
			ON CONFLICT (trader_id, ticker) DO UPDATE SET amount = HOLDINGS.amount + EXCLUDED.amount
			RETURNING amount`, traderID, req.Ticker, req.Amount).Scan(&result.Holding)
		if err != nil {
			return nil, err
		}
		seller, buyer = MarketID, traderID
	} else {
		err = tx.QueryRowContext(ctx, `UPDATE HOLDINGS SET amount = amount - $3
			WHERE trader_id = $1 AND ticker = $2 AND amount >= $3 RETURNING amount`, traderID, req.Ticker, req.Amount).Scan(&result.Holding)
		if errors.Is(err, sql.ErrNoRows) {
			return nil, reject(http.StatusUnprocessableEntity, "insufficient holdings: cannot sell %d %s", req.Amount, req.Ticker)
		}
		if err != nil {
			return nil, err
		}
		err = tx.QueryRowContext(ctx, `UPDATE ACCOUNTS SET cash = cash + $2::numeric, trades_sell = trades_sell + 1, last_trade_at = $3
			WHERE trader_id = $1 RETURNING cash::text`, traderID, total, now).Scan(&cash)
		if err != nil {
			return nil, err
		}
		seller, buyer = traderID, MarketID
	}

	trade, err := appendTrade(ctx, tx, Trade{
		Timestamp: now,
		Ticker:    req.Ticker,
		Amount:    req.Amount,
		Price:     json.Number(price),
		Currency:  currency,
		SellerID:  seller,
		BuyerID:   buyer,
	})
	if err != nil {
		return nil, err
	}
	if err := tx.Commit(); err != nil {
		return nil, err
	}

	trade.Total = json.Number(total)
	result.Trade = trade
	result.Cash = json.Number(cash)
	return result, nil
}

// appendTrade encadeia a negociação ao último registro do ledger e a grava. Deve ser chamada
// dentro da transação que detém o lock do ledger.
func appendTrade(ctx context.Context, tx *sql.Tx, t Trade) (Trade, error) {
	t.PrevHash = genesisHash
	err := tx.QueryRowContext(ctx, "SELECT hash FROM STOCK_EXCHANGES ORDER BY seq DESC LIMIT 1").Scan(&t.PrevHash)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return t, err
	}
	t.Hash = blockHash(t)
	err = tx.QueryRowContext(ctx, `INSERT INTO STOCK_EXCHANGES
		(timestamp, ticker, price, currency, amount, seller_id, buyer_id, prev_hash, hash)
		VALUES ($1, $2, $3::numeric, $4, $5, $6, $7, $8, $9) RETURNING seq`,
		t.Timestamp, t.Ticker, t.Price.String(), t.Currency, t.Amount, t.SellerID, t.BuyerID, t.PrevHash, t.Hash).Scan(&t.Seq)
	return t, err
}

// latestPrice retorna o preço de referência mais recente do ativo, no formato textual do NUMERIC
func latestPrice(ctx context.Context, tx *sql.Tx, ticker string) (string, error) {
	var price string
	err := tx.QueryRowContext(ctx, "SELECT price::text FROM TRENDS WHERE ticker = $1 ORDER BY timestamp DESC, id DESC LIMIT 1",
		ticker).Scan(&price)
	if errors.Is(err, sql.ErrNoRows) {
		return "", reject(http.StatusConflict, "no reference price for %s yet", ticker)
	}
	return price, err
}

// Trades lista as negociações mais recentes, opcionalmente de um investidor (GET /market/trades)
func (h *Handler) Trades(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpjson.Error(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	limit, err := strconv.Atoi(r.URL.Query().Get("limit"))
	if err != nil || limit <= 0 || limit > 500 {
		limit = 50
	}
	traderID := r.URL.Query().Get("trader_id")
	if traderID != "" && !uuidPattern.MatchString(traderID) {
		httpjson.Error(w, http.StatusBadRequest, "invalid trader id")
		return
	}

	rows, err := h.DB.QueryContext(r.Context(), `SELECT e.seq, e.timestamp, e.ticker, e.amount, e.price::text,
			(e.price * e.amount)::numeric(14,2)::text, e.currency, e.seller_id::text, s.first_name,
			e.buyer_id::text, b.first_name, e.prev_hash, e.hash
		FROM STOCK_EXCHANGES e
		JOIN TRADERS s ON s.id = e.seller_id
		JOIN TRADERS b ON b.id = e.buyer_id
		WHERE ($1 = '' OR e.seller_id::text = $1 OR e.buyer_id::text = $1)
		ORDER BY e.seq DESC LIMIT $2`, strings.ToLower(traderID), limit)
	if err != nil {
		fail(w, err)
		return
	}
	defer rows.Close()

	trades := []Trade{}
	for rows.Next() {
		var t Trade
		var price, total string
		if err := rows.Scan(&t.Seq, &t.Timestamp, &t.Ticker, &t.Amount, &price, &total, &t.Currency,
			&t.SellerID, &t.SellerName, &t.BuyerID, &t.BuyerName, &t.PrevHash, &t.Hash); err != nil {
			fail(w, err)
			return
		}
		t.Price, t.Total = json.Number(price), json.Number(total)
		trades = append(trades, t)
	}
	if err := rows.Err(); err != nil {
		fail(w, err)
		return
	}
	httpjson.Write(w, http.StatusOK, trades)
}

// Ledger resume o ledger: quantidade de registros, volume negociado e hash do último registro (GET /market/ledger)
func (h *Handler) Ledger(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpjson.Error(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	var summary struct {
		Records     int64       `json:"records"`
		Volume      json.Number `json:"volume"`
		Currency    string      `json:"currency"`
		LastTradeAt *time.Time  `json:"last_trade_at"`
		HeadSeq     int64       `json:"head_seq"`
		HeadHash    string      `json:"head_hash"`
	}
	var volume string
	var lastTrade sql.NullTime
	err := h.DB.QueryRowContext(r.Context(), `SELECT COUNT(*), COALESCE(SUM(price * amount), 0)::numeric(16,2)::text, MAX(timestamp)
		FROM STOCK_EXCHANGES`).Scan(&summary.Records, &volume, &lastTrade)
	if err != nil {
		fail(w, err)
		return
	}
	summary.Volume, summary.Currency, summary.HeadHash = json.Number(volume), currency, genesisHash
	if lastTrade.Valid {
		summary.LastTradeAt = &lastTrade.Time
		err = h.DB.QueryRowContext(r.Context(), "SELECT seq, hash FROM STOCK_EXCHANGES ORDER BY seq DESC LIMIT 1").
			Scan(&summary.HeadSeq, &summary.HeadHash)
		if err != nil {
			fail(w, err)
			return
		}
	}
	httpjson.Write(w, http.StatusOK, summary)
}

// VerifyLedger percorre todo o ledger recalculando a cadeia de hashes (GET /market/ledger/verify)
func (h *Handler) VerifyLedger(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpjson.Error(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	rows, err := h.DB.QueryContext(r.Context(), `SELECT seq, timestamp, ticker, amount, price::text, currency,
			seller_id::text, buyer_id::text, prev_hash, hash
		FROM STOCK_EXCHANGES ORDER BY seq`)
	if err != nil {
		fail(w, err)
		return
	}
	defer rows.Close()

	verifier := newChainVerifier()
	var invalid error
	for rows.Next() && invalid == nil {
		var t Trade
		var price string
		if err := rows.Scan(&t.Seq, &t.Timestamp, &t.Ticker, &t.Amount, &price, &t.Currency,
			&t.SellerID, &t.BuyerID, &t.PrevHash, &t.Hash); err != nil {
			fail(w, err)
			return
		}
		t.Price = json.Number(price)
		invalid = verifier.add(t)
	}
	if err := rows.Err(); err != nil {
		fail(w, err)
		return
	}

	response := map[string]any{
		"valid":       invalid == nil,
		"verified":    verifier.blocks,
		"head_hash":   verifier.prev,
		"verified_at": time.Now().UTC(),
	}
	if invalid != nil {
		response["error"] = invalid.Error()
	}
	httpjson.Write(w, http.StatusOK, response)
}

// accounts consulta as contas avaliadas ao preço mais recente; traderID vazio retorna todas
func (h *Handler) accounts(ctx context.Context, traderID string) ([]Account, error) {
	rows, err := h.DB.QueryContext(ctx, `
		WITH latest AS (
			SELECT DISTINCT ON (ticker) ticker, price FROM TRENDS ORDER BY ticker, timestamp DESC, id DESC
		), valuation AS (
			SELECT h.trader_id,
			       COALESCE(SUM(h.amount * l.price), 0)                 AS stocks_value,
			       COALESCE(SUM(h.initial_amount * h.initial_price), 0) AS initial_stocks_value,
			       COALESCE(SUM(h.initial_amount * l.price), 0)         AS hold_stocks_value
			FROM HOLDINGS h LEFT JOIN latest l ON l.ticker = h.ticker
			GROUP BY h.trader_id
		), position AS (
			SELECT a.*, t.first_name,
			       COALESCE(v.stocks_value, 0)                         AS stocks_value,
			       a.cash + COALESCE(v.stocks_value, 0)                AS net_worth,
			       a.initial_cash + COALESCE(v.initial_stocks_value, 0) AS initial_net_worth,
			       a.initial_cash + COALESCE(v.hold_stocks_value, 0)    AS hold_value
			FROM ACCOUNTS a
			JOIN TRADERS t ON t.id = a.trader_id
			LEFT JOIN valuation v ON v.trader_id = a.trader_id
			WHERE ($1 = '' OR a.trader_id::text = $1)
		)
		SELECT trader_id::text, first_name, cash::text, initial_cash::text,
		       ROUND(stocks_value, 2)::text, ROUND(net_worth, 2)::text, ROUND(initial_net_worth, 2)::text,
		       ROUND(hold_value, 2)::text, ROUND(net_worth - initial_net_worth, 2)::text,
		       COALESCE((net_worth - initial_net_worth) / NULLIF(initial_net_worth, 0) * 100, 0)::float8,
		       trades_buy, trades_sell, last_trade_at, created_at
		FROM position
		ORDER BY net_worth DESC`, traderID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	accounts := []Account{}
	for rows.Next() {
		var a Account
		var cash, initialCash, stocks, netWorth, initialNetWorth, hold, result string
		var lastTrade sql.NullTime
		if err := rows.Scan(&a.TraderID, &a.Name, &cash, &initialCash, &stocks, &netWorth, &initialNetWorth,
			&hold, &result, &a.ResultPct, &a.Buys, &a.Sells, &lastTrade, &a.OpenedAt); err != nil {
			return nil, err
		}
		a.Cash, a.InitialCash, a.StocksValue = json.Number(cash), json.Number(initialCash), json.Number(stocks)
		a.NetWorth, a.InitialNetWorth = json.Number(netWorth), json.Number(initialNetWorth)
		a.BuyAndHoldValue, a.Result = json.Number(hold), json.Number(result)
		if lastTrade.Valid {
			a.LastTradeAt = &lastTrade.Time
		}
		accounts = append(accounts, a)
	}
	return accounts, rows.Err()
}

// account retorna uma conta com a carteira detalhada
func (h *Handler) account(ctx context.Context, traderID string) (*Account, error) {
	accounts, err := h.accounts(ctx, strings.ToLower(traderID))
	if err != nil {
		return nil, err
	}
	if len(accounts) == 0 {
		return nil, reject(http.StatusNotFound, "account %s not found", traderID)
	}
	account := accounts[0]

	rows, err := h.DB.QueryContext(ctx, "SELECT ticker, amount FROM HOLDINGS WHERE trader_id = $1 AND amount > 0 ORDER BY ticker", account.TraderID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	account.Holdings = map[string]int{}
	for rows.Next() {
		var ticker string
		var amount int
		if err := rows.Scan(&ticker, &amount); err != nil {
			return nil, err
		}
		account.Holdings[ticker] = amount
	}
	return &account, rows.Err()
}

func normalizeTicker(ticker string) string {
	return strings.ToUpper(strings.TrimSpace(ticker))
}
