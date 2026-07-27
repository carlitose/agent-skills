"""Deterministic ticket-autopilot kernel."""

from .ticket_contract import CONTRACT_VERSION
from .ledger import LEDGER_VERSION

__all__ = ["CONTRACT_VERSION", "LEDGER_VERSION"]
