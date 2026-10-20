"""Cliente do mercado descentralizado simulado (endpoints /market e /stocks da webapi).

Saldo e carteira de cada investidor ficam no mercado, que valida e executa as ordens ao preço
de referência mais recente. O bot apenas decide e envia ordens.
"""
import requests


class MarketNotReady(Exception):
    """O mercado ainda não pode atender o pedido (ex.: sem preço de referência para algum ativo)."""


class OrderRejected(Exception):
    """Ordem recusada por regra de negócio (saldo ou posição insuficiente)."""


class MarketClient:
    """Cliente HTTP do mercado. Use uma instância por thread (requests.Session não é thread-safe)."""

    def __init__(self, base_url, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def open_account(self, trader_id, initial_cash, initial_holdings):
        """Abre a conta do investidor; se já existir, retorna a conta atual (operação idempotente)."""
        response = self.session.post(f"{self.base_url}/market/accounts", timeout=self.timeout, json={
            "trader_id": trader_id,
            "initial_cash": initial_cash,
            "initial_holdings": initial_holdings,
        })
        if response.status_code == 409:
            raise MarketNotReady(_error_message(response))
        response.raise_for_status()
        return response.json()

    def account(self, trader_id):
        """Conta do investidor: caixa, carteira e patrimônio avaliado ao preço mais recente."""
        response = self.session.get(f"{self.base_url}/market/accounts/{trader_id}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def buy(self, trader_id, ticker, amount):
        return self._order("buy", trader_id, ticker, amount)

    def sell(self, trader_id, ticker, amount):
        return self._order("sell", trader_id, ticker, amount)

    def _order(self, side, trader_id, ticker, amount):
        response = self.session.post(f"{self.base_url}/stocks/{side}", timeout=self.timeout, json={
            "trader_id": trader_id,
            "ticker": ticker,
            "amount": amount,
        })
        if response.status_code in (409, 422):
            raise OrderRejected(_error_message(response))
        response.raise_for_status()
        return response.json()


def _error_message(response):
    try:
        return response.json().get("error", response.text)
    except ValueError:
        return response.text
