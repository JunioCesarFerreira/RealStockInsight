//go:build !prod
// +build !prod

package configs

import (
	"fmt"
	"os"
)

// Senha do banco vem da variavel de ambiente DB_PASSWORD
var ConnectionString = fmt.Sprintf("host=localhost user=userDb password=%s dbname=database sslmode=disable", os.Getenv("DB_PASSWORD"))

// Endereços verificados pelo painel de monitoramento
var KafkaAddr = "localhost:29092"
var KafkaUIAddr = "localhost:8080"
