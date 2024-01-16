package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	_ "github.com/lib/pq"
	"main.go/configs"
	"main.go/pkg/graph"
	"main.go/pkg/trend"
)

var db *sql.DB

// Inicialização
func init() {
	log.Println("waiting...")
	time.Sleep(10 * time.Second)
	var err error
	connectionString := configs.ConnectionString
	log.Println("opening db connection...")
	db, err = sql.Open("postgres", connectionString)
	if err != nil {
		log.Fatal(err)
	}
	if err = db.Ping(); err != nil {
		log.Fatal(err)
	}
}

// Rotina principal
func main() {
	port := ":5002"
	http.HandleFunc("/graph", graphHandler)
	http.HandleFunc("/trend", trendHandler)
	http.HandleFunc("/stocks/sell", sellHandler)
	http.HandleFunc("/stocks/buy", buyHandler)
	fmt.Println("Server listening on " + port)
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal(err)
	}
}

// Manipulador de acesso ao grafo da rede complexa
func graphHandler(w http.ResponseWriter, r *http.Request) {
	log.Println("get graph endpoint reached")
	enableCors(&w)

	if r.Method == "OPTIONS" {
		return
	}

	var jsonData string

	query := "SELECT graph_json FROM COMPLEX_NETWORK_GRAPHS ORDER BY id DESC LIMIT 1"

	if err := db.QueryRow(query).Scan(&jsonData); err != nil {
		errorLog(err)
	}
	log.Println("JsonData: ", jsonData)

	// Decode JSON data into a Graph struct
	var graphData graph.Graph
	if err := graphData.Load(jsonData); err != nil {
		errorLog(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(graphData); err != nil {
		errorLog(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	log.Println("Success")
}

// Manipulador de acesso à tabela de tendências
func trendHandler(w http.ResponseWriter, r *http.Request) {
	log.Println("get trend endpoint reached")
	enableCors(&w)

	if r.Method == "OPTIONS" {
		return
	}

	var trends []trend.Trend

	query := "SELECT DISTINCT ON (TICKER) " +
		"TICKER, TREND, PRICE " +
		"FROM TRENDS ORDER BY TICKER, TIMESTAMP DESC"

	rows, err := db.Query(query)
	if err != nil {
		errorLog(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	for rows.Next() {
		var t trend.Trend
		if err := rows.Scan(&t.Ticker, &t.Trend, &t.Price); err != nil {
			errorLog(err)
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		trends = append(trends, t)
	}

	if err := rows.Err(); err != nil {
		errorLog(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Println(trends)

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(trends); err != nil {
		errorLog(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Println("Success")
}

func sellHandler(w http.ResponseWriter, r *http.Request) {
}

func buyHandler(w http.ResponseWriter, r *http.Request) {
}

func errorLog(err error) {
	log.Println("Error!")
	log.Println(err.Error())
}

// Habilita CORs
func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}
