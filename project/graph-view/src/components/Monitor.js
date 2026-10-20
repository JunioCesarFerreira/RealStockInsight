import React, { useCallback, useEffect, useRef, useState } from 'react';
import { API_BASE } from '../config';
import './Monitor.css';

const POLL_MS = 5000;

// Serviços do pipeline que reportam ao painel (nome no compose usado nas dicas de diagnóstico)
const CORE_SERVICES = [
  { service: 'producer', title: 'Producer', compose: 'producer',
    role: 'Replays historical prices and publishes them to the Kafka topic stock-prices.' },
  { service: 'consumer-network', title: 'Consumer · Network', compose: 'consumer-net',
    role: 'Consumes stock-prices and builds the co-movement network stored in PostgreSQL.' },
  { service: 'consumer-trend', title: 'Consumer · Trend', compose: 'consumer-trend',
    role: 'Consumes stock-prices and computes the moving-average trend of each ticker.' },
];

const HEALTH_RANK = { ok: 0, warn: 1, unknown: 1, error: 2, down: 3 };
const HEALTH_LABEL = { ok: 'OK', warn: 'Attention', unknown: 'No signal', error: 'Error', down: 'Down' };

const METRIC_LABELS = {
  messages_delivered: 'Messages delivered',
  delivery_failures: 'Delivery failures',
  last_delivered_at: 'Last delivery',
  messages_remaining: 'Messages remaining',
  eta_hours: 'Time remaining (h)',
  tickers: 'Tickers',
  window: 'Window (rows / ticker)',
  send_interval_s: 'Send interval (s)',
  messages_consumed: 'Messages consumed',
  last_message_at: 'Last message',
  kafka_lag: 'Kafka backlog',
  graphs_written: 'Networks written',
  last_graph_at: 'Last network',
  nodes: 'Nodes',
  links: 'Links',
  last_runtime_s: 'Last build time (s)',
  history_rows: 'History rows',
  trend_rows_written: 'Trend rows written',
  tickers_up: 'Tickers up',
  tickers_down: 'Tickers down',
  processing_errors: 'Processing errors',
};

const METRIC_HINTS = {
  kafka_lag: 'Messages waiting in Kafka that this consumer has not processed yet.',
  messages_remaining: 'Messages the producer can still send before the historical data runs out.',
};

const worst = healths => healths.reduce((w, h) => (HEALTH_RANK[h] > HEALTH_RANK[w] ? h : w), 'ok');

const humanize = key => key.replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());

// Duração legível a partir de segundos
const duration = seconds => {
  const s = Math.max(0, Math.round(seconds));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 86400)}d ${Math.floor((s % 86400) / 3600)}h`;
};

const Dot = ({ health }) => <span className={`dot dot-${health}`} aria-hidden="true" />;

const HealthBadge = ({ health }) => (
  <span className={`badge badge-${health}`}><Dot health={health} />{HEALTH_LABEL[health]}</span>
);

const Monitor = () => {
  const [status, setStatus] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [events, setEvents] = useState([]);
  const [eventFilter, setEventFilter] = useState({ service: '', level: '' });
  const [, setTick] = useState(0);
  // Diferença entre o relógio do navegador e o do servidor (ms)
  const skew = useRef(0);

  const now = () => Date.now() - skew.current;
  const ago = epochMs => (epochMs == null ? '—' : `${duration((now() - epochMs) / 1000)} ago`);

  const formatMetric = (key, value) => {
    if (value === null || value === undefined) return '—';
    if (key.endsWith('_at') && typeof value === 'number') return ago(value * 1000);
    if (typeof value === 'number') return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (eventFilter.service) params.set('service', eventFilter.service);
      if (eventFilter.level) params.set('level', eventFilter.level);
      const [statusRes, eventsRes] = await Promise.all([
        fetch(`${API_BASE}/monitor/status`),
        fetch(`${API_BASE}/monitor/events?${params}`),
      ]);
      if (!statusRes.ok) throw new Error(`${statusRes.status} ${await statusRes.text()}`);
      const data = await statusRes.json();
      skew.current = Date.now() - Date.parse(data.generated_at);
      setStatus(data);
      if (eventsRes.ok) setEvents(await eventsRes.json());
      setApiError(null);
      setLastUpdate(Date.now());
    } catch (err) {
      setApiError(err.message);
    }
  }, [eventFilter]);

  useEffect(() => {
    load();
    const poll = setInterval(load, POLL_MS);
    return () => clearInterval(poll);
  }, [load]);

  // Atualiza os tempos relativos a cada segundo
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  if (!status) {
    return (
      <div className="monitor">
        {apiError
          ? <div className="banner banner-down">Cannot reach the API at <code>{API_BASE}/monitor/status</code>: {apiError}.
              Check <code>docker compose ps</code> and <code>docker compose logs api</code>.</div>
          : <p className="muted">Loading status…</p>}
      </div>
    );
  }

  const services = status.services || [];
  const findService = name => services.find(s => s.service === name && s.instance === 'main');
  const serviceHealth = name => (findService(name) ? findService(name).health : 'unknown');
  const infra = name => (status.infra || []).find(i => i.name === name);
  const infraHealth = name => (infra(name) && infra(name).ok ? 'ok' : 'down');
  const bots = services.filter(s => s.service === 'investor-bot');
  const botsRunning = bots.filter(b => b.health === 'ok').length;
  const data = status.data;

  const pipeline = [
    { name: 'Producer', health: serviceHealth('producer'), sub: findService('producer')?.state || 'no signal' },
    { name: 'Kafka', health: infraHealth('kafka'), sub: infraHealth('kafka') === 'ok' ? 'reachable' : 'unreachable' },
    { name: 'Consumers', health: worst([serviceHealth('consumer-network'), serviceHealth('consumer-trend')]),
      sub: `${['consumer-network', 'consumer-trend'].filter(s => serviceHealth(s) === 'ok').length}/2 ok` },
    { name: 'PostgreSQL', health: infraHealth('postgres'), sub: `${data.graphs.toLocaleString()} networks` },
    { name: 'API', health: apiError ? 'down' : 'ok', sub: apiError ? 'unreachable' : 'online' },
    { name: 'Investor bots', health: bots.length ? worst(bots.map(b => b.health)) : 'unknown',
      sub: `${botsRunning}/${bots.length} ok` },
  ];
  const attention = pipeline.filter(p => p.health !== 'ok');

  return (
    <div className="monitor">
      <div className="monitor-head">
        <div>
          <h1>System monitor</h1>
          <p className="muted">
            Refreshes every {POLL_MS / 1000}s · last update {lastUpdate ? ago(lastUpdate - skew.current) : '—'}
          </p>
        </div>
      </div>

      {apiError && (
        <div className="banner banner-down">
          Lost connection to the API ({apiError}). Showing the last known state.
        </div>
      )}
      {!apiError && (attention.length === 0
        ? <div className="banner banner-ok">All components are running.</div>
        : <div className="banner banner-warn">
            {attention.length} of {pipeline.length} components need attention: {attention.map(p => p.name).join(', ')}.
          </div>)}

      <section aria-label="Pipeline">
        <ol className="pipeline">
          {pipeline.map(p => (
            <li key={p.name} className={`pipeline-step step-${p.health}`}>
              <span className="pipeline-name"><Dot health={p.health} />{p.name}</span>
              <span className="pipeline-sub">{p.sub}</span>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h2>Services</h2>
        <div className="cards">
          {CORE_SERVICES.map(def => {
            const s = findService(def.service);
            const health = s ? s.health : 'unknown';
            return (
              <article key={def.service} className={`card card-${health}`}>
                <header className="card-head">
                  <h3>{def.title}</h3>
                  <HealthBadge health={health} />
                </header>
                <p className="card-role">{def.role}</p>
                {s ? (
                  <>
                    <p className="card-state">
                      <strong>{s.state}</strong>{s.detail && ` — ${s.detail}`}
                    </p>
                    <dl className="metrics">
                      {Object.entries(s.metrics || {}).map(([k, v]) => (
                        <React.Fragment key={k}>
                          <dt title={METRIC_HINTS[k]}>{METRIC_LABELS[k] || humanize(k)}</dt>
                          <dd>{formatMetric(k, v)}</dd>
                        </React.Fragment>
                      ))}
                      <dt>Uptime</dt>
                      <dd>{duration((now() - Date.parse(s.started_at)) / 1000)}</dd>
                      <dt>Last heartbeat</dt>
                      <dd>{duration(s.seconds_ago)} ago</dd>
                    </dl>
                  </>
                ) : (
                  <p className="card-state">This service has not reported yet.</p>
                )}
                {health !== 'ok' && (
                  <p className="hint">Logs: <code>docker compose logs -f {def.compose}</code></p>
                )}
              </article>
            );
          })}
        </div>
      </section>

      <section>
        <h2>Infrastructure & data</h2>
        <div className="cards">
          <article className="card">
            <header className="card-head"><h3>Infrastructure</h3></header>
            <ul className="infra">
              {(status.infra || []).map(i => (
                <li key={i.name}>
                  <Dot health={i.ok ? 'ok' : 'down'} />
                  <strong>{i.name}</strong>
                  <span className="muted">{i.detail}</span>
                </li>
              ))}
            </ul>
          </article>
          <article className="card">
            <header className="card-head"><h3>Co-movement networks</h3></header>
            <dl className="metrics">
              <dt>Stored snapshots</dt><dd>{data.graphs.toLocaleString()}</dd>
              <dt>Latest</dt><dd>{data.last_graph_at ? ago(Date.parse(data.last_graph_at)) : '—'}</dd>
              <dt>Nodes / links</dt><dd>{data.last_graph_at ? `${data.last_graph_nodes} / ${data.last_graph_links}` : '—'}</dd>
            </dl>
            <p className="hint"><a href="#/network">Open the network view →</a></p>
          </article>
          <article className="card">
            <header className="card-head"><h3>Trends</h3></header>
            <dl className="metrics">
              <dt>Stored rows</dt><dd>{data.trend_rows.toLocaleString()}</dd>
              <dt>Latest</dt><dd>{data.last_trend_at ? ago(Date.parse(data.last_trend_at)) : '—'}</dd>
              <dt>Tickers up / down</dt>
              <dd>{data.last_trend_at ? <><span className="up">▲ {data.trends_up}</span> <span className="down">▼ {data.trends_down}</span></> : '—'}</dd>
            </dl>
          </article>
        </div>
      </section>

      <section>
        <h2>Investor bots</h2>
        {bots.length === 0 ? (
          <p className="muted">
            No bot has reported yet. Bots start about 60s after the stack is up.
            Logs: <code>docker compose logs -f investor-bots</code>
          </p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Bot</th><th>Status</th><th>Strategy</th><th>Cycles</th><th>Last cycle</th>
                  <th title="Decisions in the last cycle">Last decisions</th><th>Details</th>
                </tr>
              </thead>
              <tbody>
                {bots.map(b => {
                  const m = b.metrics || {};
                  return (
                    <tr key={b.instance}>
                      <td><strong>{b.instance}</strong></td>
                      <td><HealthBadge health={b.health} /></td>
                      <td className="muted">{m.strategy || '—'}</td>
                      <td>{m.cycles ?? 0}</td>
                      <td className="nowrap">{m.last_cycle_at ? ago(m.last_cycle_at * 1000) : '—'}</td>
                      <td className="nowrap">
                        {m.cycles
                          ? <><span className="up">▲ {m.last_buy}</span> <span className="down">▼ {m.last_sell}</span> <span className="muted">■ {m.last_hold}</span></>
                          : '—'}
                      </td>
                      <td className="muted">{b.state}{b.detail && ` — ${b.detail}`}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="hint">▲ buy · ▼ sell · ■ hold</p>
          </div>
        )}
      </section>

      <section>
        <div className="section-head">
          <h2>Event log</h2>
          <div className="filters">
            <select aria-label="Service" value={eventFilter.service}
              onChange={e => setEventFilter(f => ({ ...f, service: e.target.value }))}>
              <option value="">All services</option>
              {CORE_SERVICES.map(s => <option key={s.service} value={s.service}>{s.service}</option>)}
              <option value="investor-bot">investor-bot</option>
            </select>
            <select aria-label="Level" value={eventFilter.level}
              onChange={e => setEventFilter(f => ({ ...f, level: e.target.value }))}>
              <option value="">All levels</option>
              <option value="info">info</option>
              <option value="warn">warn</option>
              <option value="error">error</option>
            </select>
          </div>
        </div>
        {events.length === 0 ? (
          <p className="muted">No events yet.</p>
        ) : (
          <div className="table-wrap events">
            <table className="table">
              <thead>
                <tr><th>Time</th><th>Source</th><th>Level</th><th>Message</th></tr>
              </thead>
              <tbody>
                {events.map(ev => (
                  <tr key={ev.id} className={`event-${ev.level}`}>
                    <td className="nowrap" title={ev.timestamp}>{new Date(ev.timestamp).toLocaleTimeString()}</td>
                    <td className="nowrap">{ev.service}{ev.instance !== 'main' && ` / ${ev.instance}`}</td>
                    <td><span className={`level level-${ev.level}`}>{ev.level}</span></td>
                    <td>{ev.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="legend">
        <h2>How to read this page</h2>
        <ul>
          <li><HealthBadge health="ok" /> running and reporting normally.</li>
          <li><HealthBadge health="warn" /> starting, waiting for upstream data, or heartbeats are late.</li>
          <li><HealthBadge health="error" /> the last operation failed — see the event log.</li>
          <li><HealthBadge health="down" /> no heartbeat for a while: the container is probably stopped or crashing.</li>
          <li><HealthBadge health="unknown" /> the service never reported since the database was created.</li>
        </ul>
        <p className="muted">
          Data flows left to right in the pipeline above. When a step needs attention, the steps after it
          usually wait for it — fix the leftmost one first.
        </p>
      </section>
    </div>
  );
};

export default Monitor;
