package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/gocql/gocql"
)

var cluster *gocql.ClusterConfig

type JsonData struct {
	Graph string `json:"graph"`
}

func init() {
	cluster = gocql.NewCluster("localhost")
	cluster.Keyspace = "graph_keyspace"
}

func getDataHandler(w http.ResponseWriter, r *http.Request) {
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

	response := JsonData{Graph: jsonData}

	jsonResponse, err := json.Marshal(response)
	if err != nil {
		log.Fatal(err)
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if _, err := w.Write(jsonResponse); err != nil {
		log.Fatal(err)
	}
}

func main() {
	port := ":5000"
	http.HandleFunc("/getdata", getDataHandler)
	fmt.Println("Server listening on " + port)
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal(err)
	}
}
