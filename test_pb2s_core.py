#!/usr/bin/env python3
"""
PB2S_Core Integration Test

Demonstrates the recursive contradiction-audit and cause-effect reasoning scaffold
embedded in our multi-agent system.
"""

import asyncio
import sys
from pathlib import Path

# Add the pb2s_twin path to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from pb2s_twin.core.pb2s_core import pb2s_core_engine, PB2SCoreState

async def test_pb2s_core_cycle():
    """Test a complete PB2S_Core reasoning cycle."""
    
    print("🧠 PB2S_Core Integration Test")
    print("=" * 50)
    
    # Example input with contradictions and knowledge gaps
    initial_draft = """
    Climate change is always caused by human activities. 
    Natural climate variations have never occurred in Earth's history.
    Therefore, all warming is due to fossil fuel emissions.
    However, ice ages happened naturally in the past.
    The evidence for human impact is unclear in some regions.
    """
    
    print("📝 INITIAL DRAFT:")
    print(initial_draft.strip())
    print()
    
    # Create cycle state
    cycle_state = pb2s_core_engine.create_cycle_state("test_001", initial_draft)
    
    # Execute DRAFT step
    print("🔄 EXECUTING DRAFT STEP...")
    cycle_state = await pb2s_core_engine.execute_draft_step(cycle_state, initial_draft)
    print(f"   - Knowledge chains identified: {len(cycle_state.knowledge_chains)}")
    print()
    
    # Execute REFLECT step
    print("🔍 EXECUTING REFLECT STEP...")
    cycle_state = await pb2s_core_engine.execute_reflect_step(cycle_state)
    print(f"   - Contradictions detected: {len(cycle_state.contradictions)}")
    print(f"   - Knowledge gaps identified: {len(cycle_state.gaps)}")
    
    # Show detected contradictions
    for i, contradiction in enumerate(cycle_state.contradictions):
        print(f"   📛 Contradiction {i+1}: {contradiction.description}")
        print(f"      Statement 1: '{contradiction.source_statement}'")
        print(f"      Statement 2: '{contradiction.conflicting_statement}'")
    print()
    
    # Execute REVISE step
    print("✏️ EXECUTING REVISE STEP...")
    cycle_state = await pb2s_core_engine.execute_revise_step(cycle_state)
    resolved_count = len([c for c in cycle_state.contradictions if c.resolved])
    print(f"   - Contradictions resolved: {resolved_count}/{len(cycle_state.contradictions)}")
    print()
    
    # Execute LEARNED step
    print("🎯 EXECUTING LEARNED STEP...")
    cycle_state = await pb2s_core_engine.execute_learned_step(cycle_state)
    print(f"   - Learned rules extracted: {len(cycle_state.learned_rules)}")
    for rule in cycle_state.learned_rules:
        print(f"     💡 {rule}")
    print()
    
    # Check termination condition
    should_terminate, reason = pb2s_core_engine.should_terminate_cycle(cycle_state)
    print(f"🏁 TERMINATION CHECK: {should_terminate} ({reason})")
    print()
    
    # Generate cycle summary
    summary = pb2s_core_engine.get_cycle_summary(cycle_state)
    print("📊 CYCLE SUMMARY:")
    print(f"   - Cycle ID: {summary['cycle_id']}")
    print(f"   - Iterations: {summary['iterations']}")
    print(f"   - Contradictions: {summary['contradictions_detected']} detected, {summary['contradictions_resolved']} resolved")
    print(f"   - Knowledge Chains: {summary['knowledge_chains_created']} created, {summary['knowledge_chains_verified']} verified")
    print(f"   - Gaps Identified: {summary['gaps_identified']}")
    print(f"   - PB2S_Core Compliance: {summary['pb2s_core_compliance']['principles_followed']}")
    print()
    
    print("✅ PB2S_Core integration test completed!")
    print()
    print("🔬 KEY BENEFITS DEMONSTRATED:")
    print("   1. Contradictions are explicitly detected and flagged")
    print("   2. Knowledge gaps are marked instead of hidden")
    print("   3. Cause→effect chains are tracked and verified")
    print("   4. Learning rules are extracted for future cycles")
    print("   5. Termination based on contradiction resolution")

if __name__ == "__main__":
    asyncio.run(test_pb2s_core_cycle())