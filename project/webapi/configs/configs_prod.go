//go:build prod
// +build prod

package configs

import (
	"fmt"
	"os"
)

// Senha do banco vem da variavel de ambiente DB_PASSWORD
var ConnectionString = fmt.Sprintf("host=rsi-db user=userDb password=%s dbname=database sslmode=disable", os.Getenv("DB_PASSWORD"))
