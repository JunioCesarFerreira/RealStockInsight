package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/gocql/gocql"
	"main.go/pkg/graph"
)

var cluster *gocql.ClusterConfig

func init() {
	cluster = gocql.NewCluster("localhost")
	cluster.Keyspace = "graph_keyspace"
}

func graphHandler(w http.ResponseWriter, r *http.Request) {
	log.Println("get graph endpoint reached")
	enableCors(&w)

	if r.Method == "OPTIONS" {
		return
	}

	log.Println("Create Cassandra Session")
	session, err := cluster.CreateSession()
	if err != nil {
		log.Fatal(err)
	}
	defer session.Close()

	var jsonData string

	query := "SELECT json_data FROM graph_table WHERE dummy_partition_key = 1 LIMIT 1"
	if err := session.Query(query).Consistency(gocql.One).Scan(&jsonData); err != nil {
		log.Fatal(err)
	}
	log.Println("JsonData: ", jsonData)

	// Decode JSON data into a Graph struct
	var graphData graph.Graph
	if err := graphData.Load(jsonData); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(graphData); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}

func main() {
	port := ":5002"
	http.HandleFunc("/graph", graphHandler)
	fmt.Println("Server listening on " + port)
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal(err)
	}
}
