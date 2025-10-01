"""
PB2S+Twin: Minimal-Safety Multi-Modal Manufacturing Architecture

Core package for the PB2S+Twin system that orchestrates safe multi-modal content generation
through structured cycles, sandboxed execution, and comprehensive audit trails.
"""

__version__ = "1.0.0"
__author__ = "Shyamal Solanki (PB2S/PB2A) + AI collaborator"

from .core.orchestrator import PB2SOrchestrator
from .twin.sandbox import VirtualTwin
from .safety.suit_engine import SuitEngine
from .ledger.audit_trail import SafetyLedger

__all__ = [
    "PB2SOrchestrator",
    "VirtualTwin", 
    "SuitEngine",
    "SafetyLedger",
]