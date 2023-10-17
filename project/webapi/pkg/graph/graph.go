package graph

import (
	"encoding/json"
)

type Node struct {
	ID    int    `json:"id"`
	Label string `json:"label"`
}

type Link struct {
	Source int     `json:"source"`
	Target int     `json:"target"`
	Weight float64 `json:"weight"`
}

type Graph struct {
	Nodes []*Node `json:"nodes"`
	Links []*Link `json:"links"`
}

func (g *Graph) Load(textData string) error {
	// Decodifica o texto JSON em um objeto GraphContainer
	err := json.Unmarshal([]byte(textData), g)
	if err != nil {
		return err
	}
	return nil
}
