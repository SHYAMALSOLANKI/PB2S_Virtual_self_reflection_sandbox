"""Ledger package for audit trail."""

class SafetyLedger:
    """Placeholder Safety Ledger."""
    def __init__(self, ledger_path="./ledger.jsonl"):
        self.ledger_path = ledger_path
        self.version = "1.0.0"

__all__ = ["SafetyLedger"]