package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

type Vertex struct {
	ID    string `json:"id"`
	Label string `json:"label"`
}

type Edge struct {
	Source string  `json:"source"`
	Target string  `json:"target"`
	Weight float64 `json:"weight"`
}

type Graph struct {
	Vertices []*Vertex `json:"vertices"`
	Edges    []*Edge   `json:"edges"`
}

type GraphContainer struct {
	Graph *Graph `json:"graph"`
}

func readJSONFile(filename string) (*GraphContainer, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var graphData GraphContainer
	err = json.Unmarshal(data, &graphData)
	if err != nil {
		return nil, err
	}

	return &graphData, nil
}

func graphHandler(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)

	if r.Method == "OPTIONS" {
		return
	}

	graphData, err := readJSONFile("api/graph.json")
	if err != nil {
		http.Error(w, "Failed to read JSON file", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(graphData)
}

func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}

func main() {
	http.HandleFunc("/graph", graphHandler)

	log.Println("Server started on :5001")
	http.ListenAndServe(":5001", nil)
}
