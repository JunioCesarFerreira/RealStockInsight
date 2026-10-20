# Investor Bot

Each bot (defined in `config.json`) runs in its own thread. Every `interval` seconds it:

1. Fetches the co-movement network and the trends from the WebAPI.
2. Computes the enabled centrality measures and decides, for each ticker, whether to buy, sell or hold (`investment_strategy`).
3. Sends the orders to the decentralized market (`market.py`): a buy decision buys 15% of the available cash in the ticker and a sell decision sells the whole position.

On its first cycle the bot opens its market account with `initialMoney` and `initial_assets.json`. Cash and holdings are kept by the market; the bot reads its account on each cycle. Every decision is also logged to the SQLite file `bot_log.db`, used by `../results-analysis/analysis.py`.

Recovering log database:

```bash
docker cp rsi-investor-bot:/usr/src/app/bot_log.db .
```
