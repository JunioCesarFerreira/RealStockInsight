import React, { useCallback, useEffect, useState } from 'react';
import { API_BASE } from '../config';
import { duration, money, shortHash, signClass, signedMoney, signedPct } from '../format';
import './Monitor.css';

const POLL_MS = 5000;

const Market = () => {
  const [accounts, setAccounts] = useState([]);
  const [ledger, setLedger] = useState(null);
  const [trades, setTrades] = useState([]);
  const [error, setError] = useState(null);
  const [verification, setVerification] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [, setTick] = useState(0);

  const ago = iso => (iso ? `${duration((Date.now() - Date.parse(iso)) / 1000)} ago` : '—');

  const load = useCallback(async () => {
    try {
      const [accountsRes, ledgerRes, tradesRes] = await Promise.all([
        fetch(`${API_BASE}/market/accounts`),
        fetch(`${API_BASE}/market/ledger`),
        fetch(`${API_BASE}/market/trades?limit=25`),
      ]);
      for (const res of [accountsRes, ledgerRes, tradesRes]) {
        if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
      }
      setAccounts(await accountsRes.json());
      setLedger(await ledgerRes.json());
      setTrades(await tradesRes.json());
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const verify = useCallback(async () => {
    setVerifying(true);
    try {
      const res = await fetch(`${API_BASE}/market/ledger/verify`);
      if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
      setVerification(await res.json());
    } catch (err) {
      setVerification({ valid: false, error: err.message, verified_at: new Date().toISOString() });
    } finally {
      setVerifying(false);
    }
  }, []);

  useEffect(() => {
    load();
    verify();
    const poll = setInterval(load, POLL_MS);
    return () => clearInterval(poll);
  }, [load, verify]);

  // Atualiza os tempos relativos a cada segundo
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const totalNetWorth = accounts.reduce((sum, a) => sum + Number(a.net_worth), 0);
  const totalInitial = accounts.reduce((sum, a) => sum + Number(a.initial_net_worth), 0);

  return (
    <div className="monitor">
      <div className="monitor-head">
        <div>
          <h1>Decentralized market</h1>
          <p className="muted">
            Investor bots trade on a simulated decentralized market. Orders are settled at the latest reference price
            from the market feed against the market liquidity pool, and every trade is appended to a hash-chained ledger.
          </p>
        </div>
      </div>

      {error && <div className="banner banner-down">Cannot reach the market API: {error}</div>}

      <section aria-label="Market summary">
        <div className="cards cards-compact">
          <article className="card">
            <header className="card-head"><h3>Trades</h3></header>
            <p className="stat">{ledger ? ledger.records.toLocaleString() : '—'}</p>
            <p className="hint">Last trade {ledger ? ago(ledger.last_trade_at) : '—'}</p>
          </article>
          <article className="card">
            <header className="card-head"><h3>Volume traded</h3></header>
            <p className="stat">{ledger ? money(ledger.volume) : '—'}</p>
            <p className="hint">Sum of price × amount of every settled trade</p>
          </article>
          <article className="card">
            <header className="card-head"><h3>Investors' net worth</h3></header>
            <p className="stat">{accounts.length ? money(totalNetWorth) : '—'}</p>
            <p className={`hint ${signClass(totalNetWorth - totalInitial)}`}>
              {accounts.length ? `${signedMoney(totalNetWorth - totalInitial)} since the accounts were opened` : 'No account opened yet'}
            </p>
          </article>
          <article className="card">
            <header className="card-head">
              <h3>Ledger integrity</h3>
              {verification && (
                <span className={`badge ${verification.valid ? 'badge-ok' : 'badge-error'}`}>
                  <span className={`dot ${verification.valid ? 'dot-ok' : 'dot-error'}`} aria-hidden="true" />
                  {verification.valid ? 'Verified' : 'Broken'}
                </span>
              )}
            </header>
            <p className="card-role">
              Each record stores the hash of the previous one, so changing, removing or reordering any past trade breaks the chain.
            </p>
            {verification && (
              <p className="card-state">
                {verification.valid
                  ? `${verification.verified.toLocaleString()} records verified ${ago(verification.verified_at)}.`
                  : `Verification failed: ${verification.error}`}
              </p>
            )}
            <div className="verify">
              <button onClick={verify} disabled={verifying}>{verifying ? 'Verifying…' : 'Verify now'}</button>
              {ledger && <span className="muted mono" title={ledger.head_hash}>head {shortHash(ledger.head_hash)}</span>}
            </div>
          </article>
        </div>
      </section>

      <section>
        <h2>Portfolios</h2>
        {accounts.length === 0 ? (
          <p className="muted">No account yet. Each bot opens its account on its first cycle, once prices are available.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th><th>Investor</th>
                  <th className="num">Cash</th><th className="num">Stocks</th><th className="num">Net worth</th>
                  <th className="num" title="Net worth minus the value of the initial endowment at the opening prices">Result</th>
                  <th className="num" title="Net worth minus what the initial endowment would be worth today without trading">vs. buy &amp; hold</th>
                  <th className="num">Buys</th><th className="num">Sells</th><th>Last trade</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a, i) => {
                  const vsHold = Number(a.net_worth) - Number(a.buy_and_hold_value);
                  return (
                    <tr key={a.trader_id}>
                      <td className="muted">{i + 1}</td>
                      <td><strong>{a.name}</strong></td>
                      <td className="num">{money(a.cash)}</td>
                      <td className="num">{money(a.stocks_value)}</td>
                      <td className="num"><strong>{money(a.net_worth)}</strong></td>
                      <td className={`num nowrap ${signClass(a.result)}`}>
                        {signedMoney(a.result)}<div className="cell-sub">{signedPct(a.result_pct)}</div>
                      </td>
                      <td className={`num nowrap ${signClass(vsHold)}`}>{signedMoney(vsHold)}</td>
                      <td className="num">{a.buys}</td>
                      <td className="num">{a.sells}</td>
                      <td className="nowrap">{ago(a.last_trade_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <p className="hint">
          Net worth = cash + stocks valued at the latest reference price. Result compares it with the initial endowment
          valued at the prices of the day the account was opened; "vs. buy &amp; hold" compares it with simply keeping
          the initial endowment.
        </p>
      </section>

      <section>
        <h2>Recent trades</h2>
        {trades.length === 0 ? (
          <p className="muted">No trade yet.</p>
        ) : (
          <div className="table-wrap events">
            <table className="table">
              <thead>
                <tr>
                  <th className="num">#</th><th>Time</th><th>Seller → buyer</th><th>Ticker</th>
                  <th className="num">Amount</th><th className="num">Price</th><th className="num">Total</th><th>Hash</th>
                </tr>
              </thead>
              <tbody>
                {trades.map(t => (
                  <tr key={t.seq}>
                    <td className="num muted">{t.seq}</td>
                    <td className="nowrap" title={t.timestamp}>{new Date(t.timestamp).toLocaleTimeString()}</td>
                    <td className="nowrap">{t.seller} → {t.buyer}</td>
                    <td><strong>{t.ticker}</strong></td>
                    <td className="num">{t.amount}</td>
                    <td className="num">{money(t.price)}</td>
                    <td className="num">{money(t.total)}</td>
                    <td className="mono muted" title={`hash ${t.hash}\nprevious ${t.prev_hash}`}>{shortHash(t.hash)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default Market;
