#!/usr/bin/env python3
"""
Basic usage example for PB2S+Twin system.
"""

import asyncio
from pb2s_twin.core.orchestrator import PB2SOrchestrator
from pb2s_twin.twin.sandbox import VirtualTwin
from pb2s_twin.safety.suit_engine import SuitEngine
from pb2s_twin.ledger.audit_trail import SafetyLedger


async def basic_example():
    """Basic PB2S+Twin example."""
    print("🏭 PB2S+Twin Basic Example")
    print("=" * 30)
    
    # Initialize components
    print("Initializing components...")
    ledger = SafetyLedger()
    suit_engine = SuitEngine(mode="balanced")
    twin = VirtualTwin(ledger=ledger)
    orchestrator = PB2SOrchestrator(
        twin=twin,
        suit_engine=suit_engine,
        ledger=ledger
    )
    
    # Create mock input
    input_contract = {
        "goal": "Generate educational content about renewable energy",
        "inputs": [
            {
                "modality": "text",
                "content": "Solar and wind power are clean energy sources",
                "consent": True
            }
        ]
    }
    
    print(f"Goal: {input_contract['goal']}")
    print(f"Inputs: {len(input_contract['inputs'])} items")
    
    # Execute cycle
    print("\nExecuting PB2S cycle...")
    result = await orchestrator.execute_cycle(input_contract)
    
    print(f"✅ Cycle completed: {result['success']}")
    print(f"📄 Cycle ID: {result['cycle_id']}")
    print(f"📊 Artifacts: {len(result.get('artifacts', []))}")
    
    # Show ledger stats
    stats = await ledger.get_stats()
    print(f"📚 Ledger entries: {stats['total_entries']}")
    
    print("\n🎉 Basic example completed successfully!")


def main():
    """Run the basic example."""
    try:
        asyncio.run(basic_example())
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()