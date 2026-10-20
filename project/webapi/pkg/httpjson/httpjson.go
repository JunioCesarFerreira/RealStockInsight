// Package httpjson reúne utilitários de leitura e escrita de JSON nos handlers HTTP.
package httpjson

import (
	"encoding/json"
	"log"
	"net/http"
)

// Tamanho máximo aceito para o corpo das requisições
const maxBodyBytes = 64 * 1024

// Decode lê o corpo JSON da requisição em v
func Decode(w http.ResponseWriter, r *http.Request, v any) error {
	r.Body = http.MaxBytesReader(w, r.Body, maxBodyBytes)
	return json.NewDecoder(r.Body).Decode(v)
}

// Write responde v em JSON com o status informado
func Write(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Println("encode error:", err)
	}
}

// Error responde uma mensagem de erro no formato {"error": "..."}
func Error(w http.ResponseWriter, status int, message string) {
	Write(w, status, map[string]string{"error": message})
}
