// Package monitor recebe o status reportado pelos serviços (producer, consumers e bots)
// e o expõe para o painel de monitoramento da UI.
package monitor

import (
	"database/sql"
	"encoding/json"
	"log"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"
)

// Quantidade máxima de eventos mantidos no banco
const maxEvents = 2000

// Schema das tabelas de monitoramento (criadas na inicialização da API)
const schema = `
CREATE TABLE IF NOT EXISTS SERVICE_STATUS
(
    service    TEXT NOT NULL,
    instance   TEXT NOT NULL,
    state      TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '',
    interval_s INTEGER NOT NULL DEFAULT 10,
    metrics    TEXT NOT NULL DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (service, instance)
);

CREATE TABLE IF NOT EXISTS SERVICE_EVENTS
(
    id        BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service   TEXT NOT NULL,
    instance  TEXT NOT NULL,
    level     TEXT NOT NULL,
    message   TEXT NOT NULL
);`

// Probe é um componente de infraestrutura verificado por conexão TCP
type Probe struct {
	Name string
	Addr string
}

// Handler agrupa as dependências dos endpoints de monitoramento
type Handler struct {
	DB     *sql.DB
	Probes []Probe
}

type heartbeat struct {
	Service   string          `json:"service"`
	Instance  string          `json:"instance"`
	State     string          `json:"state"`
	Detail    string          `json:"detail"`
	Interval  int             `json:"interval_s"`
	StartedAt float64         `json:"started_at"`
	Metrics   json.RawMessage `json:"metrics"`
}

type serviceStatus struct {
	Service    string          `json:"service"`
	Instance   string          `json:"instance"`
	State      string          `json:"state"`
	Health     string          `json:"health"`
	Detail     string          `json:"detail"`
	Interval   int             `json:"interval_s"`
	Metrics    json.RawMessage `json:"metrics"`
	StartedAt  time.Time       `json:"started_at"`
	LastSeen   time.Time       `json:"last_seen"`
	SecondsAgo float64         `json:"seconds_ago"`
}

type infraStatus struct {
	Name   string `json:"name"`
	OK     bool   `json:"ok"`
	Detail string `json:"detail"`
}

type dataStatus struct {
	Graphs         int64      `json:"graphs"`
	LastGraphAt    *time.Time `json:"last_graph_at"`
	LastGraphNodes int64      `json:"last_graph_nodes"`
	LastGraphLinks int64      `json:"last_graph_links"`
	TrendRows      int64      `json:"trend_rows"`
	LastTrendAt    *time.Time `json:"last_trend_at"`
	TrendsUp       int64      `json:"trends_up"`
	TrendsDown     int64      `json:"trends_down"`
}

type event struct {
	ID        int64     `json:"id"`
	Timestamp time.Time `json:"timestamp"`
	Service   string    `json:"service"`
	Instance  string    `json:"instance"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
}

// EnsureSchema cria as tabelas de monitoramento, se necessário
func EnsureSchema(db *sql.DB) error {
	_, err := db.Exec(schema)
	return err
}

// Health responde se a API está no ar e com acesso ao banco
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	if err := h.DB.Ping(); err != nil {
		http.Error(w, "database unavailable: "+err.Error(), http.StatusServiceUnavailable)
		return
	}
	writeJSON(w, map[string]string{"status": "ok"})
}

// Heartbeat registra o estado atual de uma instância de serviço (POST)
func (h *Handler) Heartbeat(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var hb heartbeat
	if err := decodeBody(w, r, &hb); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if hb.Service == "" || hb.Instance == "" || hb.State == "" {
		http.Error(w, "service, instance and state are required", http.StatusBadRequest)
		return
	}
	metrics := "{}"
	if len(hb.Metrics) > 0 && json.Valid(hb.Metrics) {
		metrics = string(hb.Metrics)
	}
	startedAt := hb.StartedAt
	if startedAt <= 0 {
		startedAt = float64(time.Now().Unix())
	}

	query := `INSERT INTO SERVICE_STATUS (service, instance, state, detail, interval_s, metrics, started_at, last_seen)
		VALUES ($1, $2, $3, $4, $5, $6, to_timestamp($7), NOW())
		ON CONFLICT (service, instance) DO UPDATE SET
			state = EXCLUDED.state, detail = EXCLUDED.detail, interval_s = EXCLUDED.interval_s,
			metrics = EXCLUDED.metrics, started_at = EXCLUDED.started_at, last_seen = NOW()`
	_, err := h.DB.Exec(query, limit(hb.Service, 64), limit(hb.Instance, 64), limit(hb.State, 32),
		limit(hb.Detail, 500), hb.Interval, metrics, startedAt)
	if err != nil {
		log.Println("heartbeat error:", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

// Event registra um evento de log de um serviço (POST)
func (h *Handler) Event(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var ev event
	if err := decodeBody(w, r, &ev); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if ev.Service == "" || ev.Message == "" {
		http.Error(w, "service and message are required", http.StatusBadRequest)
		return
	}
	if ev.Instance == "" {
		ev.Instance = "main"
	}
	switch ev.Level {
	case "info", "warn", "error":
	default:
		ev.Level = "info"
	}

	_, err := h.DB.Exec("INSERT INTO SERVICE_EVENTS (service, instance, level, message) VALUES ($1, $2, $3, $4)",
		limit(ev.Service, 64), limit(ev.Instance, 64), ev.Level, limit(ev.Message, 2000))
	if err != nil {
		log.Println("event error:", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	// Mantém apenas os eventos mais recentes
	_, _ = h.DB.Exec("DELETE FROM SERVICE_EVENTS WHERE id <= (SELECT MAX(id) FROM SERVICE_EVENTS) - $1", maxEvents)
	w.WriteHeader(http.StatusNoContent)
}

// Status retorna o estado de todos os serviços, da infraestrutura e dos dados (GET)
func (h *Handler) Status(w http.ResponseWriter, r *http.Request) {
	services, err := h.services()
	if err != nil {
		log.Println("status error:", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data, err := h.data()
	if err != nil {
		log.Println("status error:", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, map[string]any{
		"generated_at": time.Now().UTC(),
		"infra":        h.infra(),
		"services":     services,
		"data":         data,
	})
}

// Events retorna os eventos mais recentes, opcionalmente filtrados por serviço e nível (GET)
func (h *Handler) Events(w http.ResponseWriter, r *http.Request) {
	n, err := strconv.Atoi(r.URL.Query().Get("limit"))
	if err != nil || n <= 0 || n > 500 {
		n = 100
	}
	service := r.URL.Query().Get("service")
	level := r.URL.Query().Get("level")

	rows, err := h.DB.Query(`SELECT id, timestamp, service, instance, level, message FROM SERVICE_EVENTS
		WHERE ($1 = '' OR service = $1) AND ($2 = '' OR level = $2)
		ORDER BY id DESC LIMIT $3`, service, level, n)
	if err != nil {
		log.Println("events error:", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	events := []event{}
	for rows.Next() {
		var ev event
		if err := rows.Scan(&ev.ID, &ev.Timestamp, &ev.Service, &ev.Instance, &ev.Level, &ev.Message); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		events = append(events, ev)
	}
	writeJSON(w, events)
}

func (h *Handler) services() ([]serviceStatus, error) {
	rows, err := h.DB.Query(`SELECT service, instance, state, detail, interval_s, metrics, started_at, last_seen
		FROM SERVICE_STATUS ORDER BY service, instance`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	now := time.Now()
	services := []serviceStatus{}
	for rows.Next() {
		var s serviceStatus
		var metrics string
		if err := rows.Scan(&s.Service, &s.Instance, &s.State, &s.Detail, &s.Interval, &metrics, &s.StartedAt, &s.LastSeen); err != nil {
			return nil, err
		}
		s.Metrics = json.RawMessage(metrics)
		age := now.Sub(s.LastSeen)
		s.SecondsAgo = age.Seconds()
		s.Health = health(s.State, age, s.Interval)
		services = append(services, s)
	}
	return services, rows.Err()
}

// health classifica a instância em ok, warn, error ou down conforme o estado e a idade do último heartbeat
func health(state string, age time.Duration, intervalS int) string {
	if intervalS < 5 {
		intervalS = 5
	}
	interval := time.Duration(intervalS) * time.Second
	switch {
	case age > 6*interval:
		return "down"
	case state == "error":
		return "error"
	case age > 3*interval, state == "starting", state == "waiting":
		return "warn"
	default:
		return "ok"
	}
}

func (h *Handler) infra() []infraStatus {
	result := []infraStatus{}
	if err := h.DB.Ping(); err != nil {
		result = append(result, infraStatus{Name: "postgres", OK: false, Detail: err.Error()})
	} else {
		result = append(result, infraStatus{Name: "postgres", OK: true, Detail: "connected"})
	}
	for _, p := range h.Probes {
		conn, err := net.DialTimeout("tcp", p.Addr, 2*time.Second)
		if err != nil {
			result = append(result, infraStatus{Name: p.Name, OK: false, Detail: err.Error()})
			continue
		}
		conn.Close()
		result = append(result, infraStatus{Name: p.Name, OK: true, Detail: "reachable at " + p.Addr})
	}
	return result
}

func (h *Handler) data() (dataStatus, error) {
	var d dataStatus
	var lastGraph, lastTrend sql.NullTime

	if err := h.DB.QueryRow("SELECT COUNT(*), MAX(timestamp) FROM COMPLEX_NETWORK_GRAPHS").Scan(&d.Graphs, &lastGraph); err != nil {
		return d, err
	}
	if lastGraph.Valid {
		d.LastGraphAt = &lastGraph.Time
		err := h.DB.QueryRow(`SELECT json_array_length(graph_json::json->'nodes'), json_array_length(graph_json::json->'links')
			FROM COMPLEX_NETWORK_GRAPHS ORDER BY id DESC LIMIT 1`).Scan(&d.LastGraphNodes, &d.LastGraphLinks)
		if err != nil {
			return d, err
		}
	}

	if err := h.DB.QueryRow("SELECT COUNT(*), MAX(timestamp) FROM TRENDS").Scan(&d.TrendRows, &lastTrend); err != nil {
		return d, err
	}
	if lastTrend.Valid {
		d.LastTrendAt = &lastTrend.Time
		rows, err := h.DB.Query(`SELECT trend, COUNT(*) FROM
			(SELECT DISTINCT ON (ticker) ticker, trend FROM TRENDS ORDER BY ticker, timestamp DESC) t
			GROUP BY trend`)
		if err != nil {
			return d, err
		}
		defer rows.Close()
		for rows.Next() {
			var trend string
			var count int64
			if err := rows.Scan(&trend, &count); err != nil {
				return d, err
			}
			if trend == "up" {
				d.TrendsUp = count
			} else {
				d.TrendsDown += count
			}
		}
	}
	return d, nil
}

func decodeBody(w http.ResponseWriter, r *http.Request, v any) error {
	r.Body = http.MaxBytesReader(w, r.Body, 64*1024)
	return json.NewDecoder(r.Body).Decode(v)
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Println("encode error:", err)
	}
}

func limit(s string, n int) string {
	s = strings.TrimSpace(s)
	if r := []rune(s); len(r) > n {
		return string(r[:n])
	}
	return s
}
