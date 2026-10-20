// Formatadores compartilhados pelas telas

// Duração legível a partir de segundos
export const duration = seconds => {
  const s = Math.max(0, Math.round(seconds));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 86400)}d ${Math.floor((s % 86400) / 3600)}h`;
};

const moneyFormat = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });

// Valor monetário em dólares (a API envia valores decimais exatos como números JSON)
export const money = value => (value === null || value === undefined ? '—' : moneyFormat.format(Number(value)));

// Valor com sinal explícito, para resultados
export const signedMoney = value => {
  if (value === null || value === undefined) return '—';
  const n = Number(value);
  return `${n > 0 ? '+' : ''}${moneyFormat.format(n)}`;
};

export const signedPct = value => {
  if (value === null || value === undefined) return '—';
  return `${value > 0 ? '+' : ''}${Number(value).toFixed(2)}%`;
};

// Classe CSS conforme o sinal do valor
export const signClass = value => (Number(value) > 0 ? 'up' : Number(value) < 0 ? 'down' : 'muted');

// Hash abreviado para exibição
export const shortHash = hash => (hash ? `${hash.slice(0, 8)}…${hash.slice(-6)}` : '—');
