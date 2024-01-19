import json
import psycopg2
import sqlite3

conn_postgres = psycopg2.connect(
    host="localhost",
    port="5432",
    database="database",
    user="userDb",
    password="password1234",
)
conn_sqlite = sqlite3.connect("bot_log.db")

cursor_postgres = conn_postgres.cursor()

# Pega lista de investidores
cursor_postgres.execute("SELECT * FROM TRADERS")
traders_table = cursor_postgres.fetchall()

# Pega valor final dos ativos
cursor_postgres.execute(
    """
    SELECT
        t1.ticker,
        t1.trend,
        t1.price,
        t1.timestamp
    FROM TRENDS t1
    INNER JOIN (
        SELECT ticker, MAX(timestamp) AS max_timestamp
        FROM TRENDS
        GROUP BY ticker
    ) t2 ON t1.ticker = t2.ticker AND t1.timestamp = t2.max_timestamp;
    """
)
trends_final_results = cursor_postgres.fetchall()

# Pega valor inicial dos ativos
cursor_postgres.execute(
    """
    SELECT
        t1.ticker,
        t1.trend,
        t1.price,
        t1.timestamp
    FROM TRENDS t1
    INNER JOIN (
        SELECT ticker, MIN(timestamp) AS min_timestamp
        FROM TRENDS
        GROUP BY ticker
    ) t2 ON t1.ticker = t2.ticker AND t1.timestamp = t2.min_timestamp;
    """
)
trends_initial_values = cursor_postgres.fetchall()

# Variáveis com condições iniciais da simulação
init_net_worth = 0
init_resource = 50000
for row in trends_initial_values:
    init_net_worth += 10 * float(row[2])
        
print(f"Initial net worth: {init_net_worth}")
    

final_traders = {} # Para uso futuro.

# Iterando sobre os IDs na tabela TRADERS
for row in traders_table:
    trader_id = row[0]

    # Selecionando a última transação da tabela log_table
    cursor_sqlite = conn_sqlite.cursor()
    cursor_sqlite.execute(
        "SELECT * FROM log_table WHERE bot_id = ? ORDER BY time_stamp DESC LIMIT 1",
        (trader_id,),
    )
    last_transaction = cursor_sqlite.fetchone()

    # Deserializando a coluna assets
    if last_transaction is not None:
        assets = json.loads(last_transaction[7])
        resource = last_transaction[6]
        
        #print(f"Ativos: {assets}")
        net_worth = 0
        for ticker, quantity in assets.items():
            # Find the current price for the ticker
            for trend_row in trends_final_results:
                if trend_row[0] == ticker:
                    current_price = trend_row[2]
                    break

            net_worth += current_price * quantity
            
        net_worth = float(net_worth)
        final_traders[trader_id] = { # Para uso futuro.
            "resource": resource,
            "net_worth": net_worth
        }
        a = net_worth + resource
        b = init_net_worth + init_resource
        # Apresenta resultados
        print(f"{trader_id} : {net_worth} | {resource} | {a - b}")
        #print(f"Patrimônio líquido: {final_traders[trader_id]}")
    else:
        print("Nenhuma transação encontrada")

conn_postgres.close()
conn_sqlite.close()
