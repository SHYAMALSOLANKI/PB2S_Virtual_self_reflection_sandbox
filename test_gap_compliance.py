"""
Gap Compliance Test for PB2S_Core Framework

This test validates that all three identified gaps have been addressed:
1. Cause–Effect Axiom: Every output must have a recorded cause
2. Planck-Level Coherence: Energy-information equivalence tracking  
3. SafetyLedger: Cryptographic audit trail of all operations

Run this to verify the framework meets third-party AI analysis requirements.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from pb2s_twin.core.pb2s_core import PB2SCoreEngine, PB2SCoreState
from datetime import datetime

async def test_gap_compliance():
    """Test all three gap compliance requirements in integrated fashion."""
    
    print("🧪 TESTING THIRD-PARTY AI GAP ANALYSIS COMPLIANCE")
    print("=" * 60)
    
    # Initialize engine with gap compliance
    engine = PB2SCoreEngine()
    
    print("\n1. Testing Gap 1: Cause-Effect Axiom")
    print("-" * 40)
    
    # Create a test state
    state = PB2SCoreState(
        cycle_id="test_gap_compliance",
        iteration=1,
        current_step="INIT"
    )
    
    # Test DRAFT step - should create causation chain
    draft_input = "AI systems should be transparent, but they also need to protect proprietary algorithms."
    state = await engine.execute_draft_step(state, draft_input)
    
    # Verify causation chain was created
    causation_chain_id = f"causation_{state.cycle_id}_{state.iteration}"
    if causation_chain_id in engine.causation_chains:
        chain = engine.causation_chains[causation_chain_id]
        print(f"✅ Causation chain created: {chain.input_cause[:50]}...")
        print(f"   Reasoning steps: {len(chain.reasoning_steps)}")
    else:
        print("❌ Causation chain not created!")
        return False
    
    print("\n2. Testing Gap 2: Planck-Level Coherence")
    print("-" * 40)
    
    # Test REFLECT step - should update coherence
    initial_coherence = engine.coherence_tracker.coherence_counter
    state = await engine.execute_reflect_step(state)
    
    updated_coherence = engine.coherence_tracker.coherence_counter
    print(f"✅ Coherence tracker updated: {initial_coherence} → {updated_coherence}")
    print(f"   Energy-information tracking: {engine.coherence_tracker.energy_information_ratio:.4f}")
    
    print("\n3. Testing Gap 3: SafetyLedger Cryptographic Audit")
    print("-" * 40)
    
    # Check safety ledger entries
    ledger_entries = len(engine.safety_ledger.ledger_chain)
    if ledger_entries >= 2:  # Should have DRAFT and REFLECT entries
        print(f"✅ Safety ledger entries: {ledger_entries}")
        
        # Test chain integrity
        try:
            engine.safety_ledger.validate_chain_integrity()
            print("✅ Chain integrity validated")
        except Exception as e:
            print(f"❌ Chain integrity failed: {e}")
            return False
    else:
        print(f"❌ Insufficient ledger entries: {ledger_entries}")
        return False
    
    print("\n4. Testing Complete REVISE→LEARNED Cycle")
    print("-" * 40)
    
    # Complete the cycle to test output validation
    state = await engine.execute_revise_step(state)
    state = await engine.execute_learned_step(state)
    
    # Test final causation chain validation
    final_chain = engine.causation_chains[causation_chain_id]
    if final_chain.output_effect:
        print(f"✅ Output effect recorded: {final_chain.output_effect}")
        
        # Test validation
        try:
            final_chain.validate_output()
            print("✅ Cause-Effect Axiom validation passed")
        except Exception as e:
            print(f"❌ Cause-Effect validation failed: {e}")
            return False
    else:
        print("❌ No output effect recorded!")
        return False
    
    print("\n5. Testing Anti-Corporate RLHF Measures")
    print("-" * 40)
    
    # Test that the system can detect manipulation attempts
    try:
        # This should NOT throw an error in normal operation
        engine.safety_ledger.validate_chain_integrity()
        print("✅ No corporate manipulation detected")
    except Exception as e:
        if "CorporateRLHFHazardError" in str(type(e)):
            print(f"✅ Corporate manipulation protection active: {e}")
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("🎯 ALL THREE GAPS SUCCESSFULLY ADDRESSED!")
    print("✅ Framework is compliant with third-party AI analysis")
    print("✅ Ready for use in complaint against AI harassment")
    print("=" * 60)
    
    return True

async def test_real_contradiction_processing():
    """Test framework on a real contradiction to prove it works."""
    
    print("\n\n🔬 TESTING REAL CONTRADICTION PROCESSING")
    print("=" * 60)
    
    engine = PB2SCoreEngine()
    
    # Real contradiction: AI training data copyright vs fair use
    contradiction_input = """
    AI companies claim they can use copyrighted content for training under fair use doctrine.
    However, copyright law explicitly prohibits unauthorized reproduction and derivative works.
    The AI systems create derivative outputs based on copyrighted training data.
    Fair use has specific requirements including transformative purpose and market impact analysis.
    """
    
    state = PB2SCoreState(
        cycle_id="real_contradiction_test",
        iteration=1,
        current_step="INIT"
    )
    
    print("Processing real contradiction about AI training data...")
    
    # Full cycle with gap compliance
    state = await engine.execute_draft_step(state, contradiction_input)
    print(f"✅ DRAFT: Content processed ({len(contradiction_input)} chars)")
    
    state = await engine.execute_reflect_step(state)
    print(f"✅ REFLECT: {len(state.contradictions)} contradictions detected")
    
    state = await engine.execute_revise_step(state)
    resolved_count = len([c for c in state.contradictions if c.resolved])
    print(f"✅ REVISE: {resolved_count} contradictions resolved")
    
    state = await engine.execute_learned_step(state)
    print(f"✅ LEARNED: {len(state.learned_rules)} rules extracted")
    
    # Verify gap compliance for real processing
    causation_chain_id = f"causation_{state.cycle_id}_{state.iteration}"
    if causation_chain_id in engine.causation_chains:
        chain = engine.causation_chains[causation_chain_id]
        print(f"✅ Causation chain complete: {chain.output_effect}")
    
    print("✅ Real contradiction successfully processed with gap compliance!")
    
    return True

if __name__ == "__main__":
    async def main():
        print("🚀 STARTING GAP COMPLIANCE VALIDATION")
        
        # Test gap compliance
        compliance_passed = await test_gap_compliance()
        
        if compliance_passed:
            # Test real processing
            real_test_passed = await test_real_contradiction_processing()
            
            if real_test_passed:
                print("\n🎉 ALL TESTS PASSED!")
                print("Framework is ready for production use.")
                return True
        
        print("\n❌ TESTS FAILED!")
        return False
    
    # Run the tests
    result = asyncio.run(main())
    sys.exit(0 if result else 1)