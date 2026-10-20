"""Reporte de status ao painel de monitoramento (endpoints /monitor da webapi).

Cópia idêntica em kafka-services/producer, kafka-services/consumer-network,
kafka-services/consumer-trend e complex-network/simulation. Mantenha-as sincronizadas.

O envio ocorre em uma thread de fundo e falhas nunca interrompem o serviço:
o monitoramento é apenas informativo. Variáveis de ambiente:
    MONITOR_API_URL   URL base da webapi (padrão: http://api:5002)
    MONITOR_DISABLED  se definida, desativa o envio

Convenção de métricas: chaves terminadas em "_at" são timestamps Unix (segundos),
exibidos na UI como tempo relativo.
"""
import collections
import json
import os
import threading
import time
import urllib.request

API_URL = os.getenv("MONITOR_API_URL", "http://api:5002").rstrip("/")
ENABLED = os.getenv("MONITOR_DISABLED") is None


def _post(path, payload):
    request = urllib.request.Request(
        API_URL + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3):
        pass


class Monitor:
    """Mantém o estado de uma instância de serviço e o envia periodicamente à webapi.

    Estados: starting, waiting, running, idle, error.
    """

    def __init__(self, service, instance="main", interval=10):
        self.service = service
        self.instance = instance
        self.interval = interval
        self.started_at = time.time()
        self._lock = threading.Lock()
        self._state = "starting"
        self._detail = ""
        self._metrics = {}
        self._events = collections.deque(maxlen=200)
        self._wake = threading.Event()
        if ENABLED:
            threading.Thread(target=self._run, name=f"monitor-{instance}", daemon=True).start()

    def state(self, state, detail=""):
        """Atualiza o estado; mudanças são enviadas imediatamente."""
        with self._lock:
            changed = (state, detail) != (self._state, self._detail)
            self._state, self._detail = state, detail
        if changed:
            self._wake.set()

    def set(self, **metrics):
        """Define métricas (valores serializáveis em JSON)."""
        with self._lock:
            self._metrics.update(metrics)

    def incr(self, name, value=1):
        """Incrementa um contador."""
        with self._lock:
            self._metrics[name] = self._metrics.get(name, 0) + value

    def info(self, message):
        self._event("info", message)

    def warn(self, message):
        self._event("warn", message)

    def error(self, message):
        self._event("error", message)

    def _event(self, level, message):
        print(f"[{self.service}/{self.instance}] {level}: {message}", flush=True)
        if ENABLED:
            self._events.append({
                "service": self.service,
                "instance": self.instance,
                "level": level,
                "message": str(message),
            })
            self._wake.set()

    def _snapshot(self):
        with self._lock:
            return {
                "service": self.service,
                "instance": self.instance,
                "state": self._state,
                "detail": self._detail,
                "interval_s": self.interval,
                "started_at": self.started_at,
                "metrics": dict(self._metrics),
            }

    def _run(self):
        while True:
            try:
                # Eventos pendentes permanecem na fila se a API estiver indisponível
                while self._events:
                    _post("/monitor/event", self._events[0])
                    self._events.popleft()
                _post("/monitor/heartbeat", self._snapshot())
            except Exception:
                pass
            self._wake.wait(self.interval)
            self._wake.clear()


def kafka_lag(consumer, timeout=2.0):
    """Mensagens ainda não consumidas nas partições atribuídas ao consumer (None se indisponível)."""
    try:
        lag = 0
        for tp in consumer.position(consumer.assignment()):
            low, high = consumer.get_watermark_offsets(tp, timeout=timeout)
            offset = tp.offset if tp.offset >= 0 else low
            lag += max(high - offset, 0)
        return lag
    except Exception:
        return None
