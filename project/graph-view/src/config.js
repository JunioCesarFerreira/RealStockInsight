// URL base da webapi. Em produção a UI é servida pelo proxy reverso, que encaminha /api para a webapi.
// Em desenvolvimento (npm start), use: REACT_APP_API_BASE=http://localhost:5002 npm start
export const API_BASE = (process.env.REACT_APP_API_BASE || '/api').replace(/\/$/, '');

// Kafka UI, também exposta pelo proxy reverso
export const KAFKA_UI_URL = process.env.REACT_APP_KAFKA_UI_URL || '/kafka-ui/';
