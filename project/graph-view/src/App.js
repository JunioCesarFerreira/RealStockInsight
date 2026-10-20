import React, { useState, useEffect } from 'react';
import Market from './components/Market';
import Monitor from './components/Monitor';
import NetworkView from './components/NetworkView';
import { KAFKA_UI_URL } from './config';
import './App.css';

const TABS = [
  { id: 'monitor', label: 'Monitor' },
  { id: 'network', label: 'Network' },
  { id: 'market', label: 'Market' },
];

const VIEWS = { monitor: Monitor, network: NetworkView, market: Market };

// Aba atual a partir do hash da URL (#/monitor, #/network, #/market)
const tabFromHash = () => {
  const id = window.location.hash.replace('#/', '');
  return TABS.some(t => t.id === id) ? id : 'monitor';
};

const App = () => {
  const [tab, setTab] = useState(tabFromHash);
  const View = VIEWS[tab];

  useEffect(() => {
    const onHashChange = () => setTab(tabFromHash());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-brand">RealStockInsight</span>
        <nav className="app-nav">
          {TABS.map(t => (
            <a key={t.id} href={`#/${t.id}`} className={tab === t.id ? 'active' : ''}>{t.label}</a>
          ))}
          <a href={KAFKA_UI_URL} target="_blank" rel="noreferrer">Kafka UI ↗</a>
        </nav>
      </header>
      <main>
        <View />
      </main>
    </div>
  );
};

export default App;
