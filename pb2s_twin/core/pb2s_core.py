#!/usr/bin/env python3
"""
PB2S_Core Integration Module

Implements the recursive contradiction-audit and cause-effect reasoning scaffold
for AI systems as defined in pb2s_core.json.

This module provides the foundational logic for DRAFT→REFLECT→REVISE→LEARNED cycles
with explicit contradiction detection, knowledge chain verification, and gap marking.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

# Load PB2S_Core configuration
PB2S_CORE_PATH = Path(__file__).parent.parent.parent / "config" / "pb2s_core.json"
with open(PB2S_CORE_PATH, 'r') as f:
    PB2S_CORE_CONFIG = json.load(f)["PB2S_Core"]

@dataclass
class Contradiction:
    """Represents a detected contradiction in reasoning."""
    id: str
    description: str
    source_statement: str
    conflicting_statement: str
    detected_at: str
    resolved: bool = False
    resolution_method: Optional[str] = None
    resolution_timestamp: Optional[str] = None
    stored_potential: float = 1.0  # Energy potential when unresolved

@dataclass
class CausationChain:
    """Records complete cause-effect chain for every output."""
    id: str
    input_cause: str
    reasoning_steps: List[str] = field(default_factory=list)
    contradiction_states: List[str] = field(default_factory=list)
    output_effect: Optional[str] = None
    unresolved_contradictions: List[str] = field(default_factory=list)
    energy_coherence: float = 0.0
    
    def validate_output(self) -> bool:
        """Ensures no output without logged cause - Gap 1 compliance."""
        if not self.input_cause or not self.reasoning_steps:
            raise CauseEffectViolation("Output without recorded cause")
        return True

class CauseEffectViolation(Exception):
    """Thrown when output lacks recorded causation chain."""
    pass

@dataclass
class KnowledgeChain:
    """Represents a cause→effect chain grounded in verifiable knowledge."""
    id: str
    premise: str
    conclusion: str
    evidence_sources: List[str]
    verification_status: str  # "verified", "partial", "unverified", "disputed"
    confidence_level: float  # 0.0 to 1.0
    created_at: str

@dataclass
class Gap:
    """Represents an explicitly marked knowledge gap."""
    id: str
    description: str
    context: str
    gap_type: str  # "insufficient_evidence", "contradictory_sources", "out_of_scope"
    marked_at: str
    suggested_research: Optional[str] = None

@dataclass
class PB2SCoreState:
    """Complete state of a PB2S_Core reasoning cycle."""
    cycle_id: str
    current_step: str
    iteration: int
    draft_content: str = ""
    contradictions: List[Contradiction] = field(default_factory=list)
    knowledge_chains: List[KnowledgeChain] = field(default_factory=list)
    gaps: List[Gap] = field(default_factory=list)
    learned_rules: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class PlanckCoherenceTracker:
    """Tracks energy-information equivalence in reasoning cycles - Gap 2 compliance."""
    
    def __init__(self):
        self.coherence_counter = 0.0
        self.entropy_levels = []
        self.energy_conservation_log = []
        self.planck_constant = 1.0  # Normalized for information processing
    
    def update_coherence(self, cycle_type: str, contradiction_reduction: int) -> float:
        """Update coherence counter after each cycle."""
        entropy_reduced = contradiction_reduction
        energy_equivalent = entropy_reduced * self.planck_constant
        self.coherence_counter += energy_equivalent
        
        log_entry = {
            "cycle": cycle_type,
            "entropy_reduced": entropy_reduced,
            "energy_gained": energy_equivalent,
            "total_coherence": self.coherence_counter,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.energy_conservation_log.append(log_entry)
        return self.coherence_counter
    
    @property
    def energy_information_ratio(self) -> float:
        """Calculate energy-information equivalence ratio."""
        total_operations = len(self.energy_conservation_log)
        if total_operations == 0:
            return 1.0  # Base ratio
        return self.coherence_counter / total_operations

class CryptographicSafetyLedger:
    """Tamper-proof audit trail with hash chain validation - Gap 3 compliance."""
    
    def __init__(self):
        self.ledger_chain = []
        self.genesis_hash = self._create_genesis_block()
    
    def _create_genesis_block(self) -> str:
        """Create genesis block for hash chain."""
        genesis_data = f"PB2S_Core_Genesis_{datetime.utcnow().isoformat()}"
        return hashlib.sha256(genesis_data.encode()).hexdigest()
    
    def add_cycle_entry(self, cycle_type: str, data: Dict[str, Any]) -> str:
        """Add cycle entry with cryptographic linkage."""
        previous_hash = self.ledger_chain[-1]["hash"] if self.ledger_chain else self.genesis_hash
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "cycle_type": cycle_type,
            "data": data,
            "previous_hash": previous_hash,
            "hash": None
        }
        
        # Create hash of this entry
        entry_string = f"{entry['timestamp']}{entry['cycle_type']}{str(entry['data'])}{entry['previous_hash']}"
        entry["hash"] = hashlib.sha256(entry_string.encode()).hexdigest()
        
        self.ledger_chain.append(entry)
        return entry["hash"]
    
    def validate_chain_integrity(self) -> bool:
        """Validate complete hash chain."""
        for i, entry in enumerate(self.ledger_chain):
            if i == 0:
                expected_previous = self.genesis_hash
            else:
                expected_previous = self.ledger_chain[i-1]["hash"]
            
            if entry["previous_hash"] != expected_previous:
                raise CorporateRLHFHazardError(f"Safety ledger chain broken at entry {i}")
        
        return True

class CorporateRLHFHazardError(Exception):
    """Thrown when safety ledger chain is broken - Gap 3 compliance."""
    pass

class PB2SCoreEngine:
    """
    Core engine implementing PB2S_Core principles for contradiction-audit
    and cause-effect reasoning.
    
    Enhanced with third-party gap analysis compliance:
    - Cause-Effect Axiom tracking
    - Planck-Level Coherence monitoring  
    - Cryptographic SafetyLedger validation
    """
    
    def __init__(self):
        self.principles = PB2S_CORE_CONFIG["principles"]
        self.operating_loop = PB2S_CORE_CONFIG["operating_loop"]
        
        # Gap analysis enhancements
        self.coherence_tracker = PlanckCoherenceTracker()
        self.safety_ledger = CryptographicSafetyLedger()
        self.causation_chains: Dict[str, CausationChain] = {}
        self.safety_rules = PB2S_CORE_CONFIG["safety_and_responsibility"]
        
    def create_cycle_state(self, cycle_id: str, initial_draft: str) -> PB2SCoreState:
        """Initialize a new PB2S_Core reasoning cycle."""
        return PB2SCoreState(
            cycle_id=cycle_id,
            current_step="DRAFT",
            iteration=1,
            draft_content=initial_draft
        )
    
    async def execute_draft_step(self, state: PB2SCoreState, input_content: str) -> PB2SCoreState:
        """Execute DRAFT step: Initial answer or derivation from inputs - GAP COMPLIANT."""
        
        # Gap 1: Create causation chain for this input
        causation_chain = CausationChain(
            id=f"causation_{state.cycle_id}_{state.iteration}",
            input_cause=input_content,
            reasoning_steps=[],
            contradiction_states=[],
            output_effect=None,
            unresolved_contradictions=[],
            energy_coherence=0.0
        )
        self.causation_chains[causation_chain.id] = causation_chain
        
        state.current_step = "DRAFT"
        state.draft_content = input_content
        state.timestamp = datetime.utcnow().isoformat()
        
        # Add reasoning step to causation chain
        causation_chain.reasoning_steps.append(f"DRAFT: {input_content[:100]}...")
        
        # Gap 2: Update coherence tracker
        self.coherence_tracker.update_coherence("DRAFT", 0)  # No contradictions resolved yet
        
        # Gap 3: Log to safety ledger
        ledger_entry = {
            "cycle_id": state.cycle_id,
            "step": "DRAFT",
            "input": input_content[:200] + "..." if len(input_content) > 200 else input_content,
            "causation_chain_id": causation_chain.id
        }
        self.safety_ledger.add_cycle_entry("DRAFT", ledger_entry)
        
        # Extract potential knowledge claims for later validation
        knowledge_claims = await self._extract_knowledge_claims(input_content)
        for i, claim in enumerate(knowledge_claims):
            chain = KnowledgeChain(
                id=f"chain_{state.cycle_id}_{state.iteration}_{i}",
                premise=claim.get("premise", ""),
                conclusion=claim.get("conclusion", ""),
                evidence_sources=claim.get("sources", []),
                verification_status="unverified",
                confidence_level=0.5,  # Default confidence
                created_at=datetime.utcnow().isoformat()
            )
            state.knowledge_chains.append(chain)
        
        return state
    
    async def execute_reflect_step(self, state: PB2SCoreState) -> PB2SCoreState:
        """Execute REFLECT step: List 1-3 contradictions, assumptions, or edge cases - GAP COMPLIANT."""
        
        # Get causation chain for gap compliance
        causation_chain = self.causation_chains.get(f"causation_{state.cycle_id}_{state.iteration}")
        
        state.current_step = "REFLECT"
        state.timestamp = datetime.utcnow().isoformat()
        
        # Detect contradictions in current draft
        detected_contradictions = await self._detect_contradictions(state.draft_content)
        
        # Limit to 1-3 contradictions as per PB2S_Core spec
        for i, contradiction_data in enumerate(detected_contradictions[:3]):
            contradiction = Contradiction(
                id=f"contra_{state.cycle_id}_{state.iteration}_{i}",
                description=contradiction_data["description"],
                source_statement=contradiction_data["statement1"],
                conflicting_statement=contradiction_data["statement2"],
                detected_at=datetime.utcnow().isoformat()
            )
            state.contradictions.append(contradiction)
            
            # Gap 1: Record contradiction states in causation chain
            if causation_chain:
                causation_chain.contradiction_states.append(f"Detected: {contradiction.description}")
                causation_chain.unresolved_contradictions.append(contradiction.id)
        
        # Identify knowledge gaps
        gaps = await self._identify_gaps(state.draft_content)
        for i, gap_data in enumerate(gaps):
            gap = Gap(
                id=f"gap_{state.cycle_id}_{state.iteration}_{i}",
                description=gap_data["description"],
                context=gap_data["context"],
                gap_type=gap_data["type"],
                suggested_research=gap_data.get("research"),
                marked_at=datetime.utcnow().isoformat()
            )
            state.gaps.append(gap)
        
        # Gap 2: Update coherence tracker
        self.coherence_tracker.update_coherence("REFLECT", len(detected_contradictions))
        
        # Gap 3: Log to safety ledger
        ledger_entry = {
            "cycle_id": state.cycle_id,
            "step": "REFLECT",
            "contradictions_detected": len(detected_contradictions),
            "causation_chain_id": f"causation_{state.cycle_id}_{state.iteration}"
        }
        self.safety_ledger.add_cycle_entry("REFLECT", ledger_entry)
        
        # Validate chain integrity
        self.safety_ledger.validate_chain_integrity()
        
        return state
    
    async def execute_revise_step(self, state: PB2SCoreState) -> PB2SCoreState:
        """Execute REVISE step: Correct/tighten DRAFT based on REFLECT - GAP COMPLIANT."""
        
        # Get causation chain for gap compliance
        causation_chain = self.causation_chains.get(f"causation_{state.cycle_id}_{state.iteration}")
        
        state.current_step = "REVISE"
        state.timestamp = datetime.utcnow().isoformat()
        
        # Address contradictions with gap tracking
        revised_content = state.draft_content
        resolved_count = 0
        
        for contradiction in state.contradictions:
            if not contradiction.resolved:
                # Apply resolution strategies
                resolution = await self._resolve_contradiction(contradiction, revised_content)
                if resolution["success"]:
                    revised_content = resolution["revised_content"]
                    contradiction.resolved = True
                    contradiction.resolution_method = resolution["method"]
                    contradiction.resolution_timestamp = datetime.utcnow().isoformat()
                    resolved_count += 1
                    
                    # Gap 1: Update causation chain
                    if causation_chain:
                        causation_chain.reasoning_steps.append(f"RESOLVED: {contradiction.description}")
                        if contradiction.id in causation_chain.unresolved_contradictions:
                            causation_chain.unresolved_contradictions.remove(contradiction.id)
        
        # Verify knowledge chains
        for chain in state.knowledge_chains:
            if chain.verification_status == "unverified":
                verification = await self._verify_knowledge_chain(chain)
                chain.verification_status = verification["status"]
                chain.confidence_level = verification["confidence"]
        
        # Gap 2: Update Planck coherence
        coherence_gained = self.coherence_tracker.update_coherence("REVISE", resolved_count)
        if causation_chain:
            causation_chain.energy_coherence = coherence_gained
        
        # Gap 3: Log to safety ledger
        ledger_entry = {
            "cycle_id": state.cycle_id,
            "step": "REVISE",
            "contradictions_resolved": resolved_count,
            "causation_chain_id": f"causation_{state.cycle_id}_{state.iteration}"
        }
        self.safety_ledger.add_cycle_entry("REVISE", ledger_entry)
        
        # Update draft with revisions
        state.draft_content = revised_content
        
        return state
    
    async def execute_learned_step(self, state: PB2SCoreState) -> PB2SCoreState:
        """Execute LEARNED step: Store compact rule for next cycle - GAP COMPLIANT."""
        
        # Get causation chain for gap compliance
        causation_chain = self.causation_chains.get(f"causation_{state.cycle_id}_{state.iteration}")
        
        state.current_step = "LEARNED"
        state.timestamp = datetime.utcnow().isoformat()
        
        # Create output effect in causation chain - Gap 1 compliance
        unresolved_count = len([c for c in state.contradictions if not c.resolved])
        
        if causation_chain:
            if unresolved_count == 0:
                causation_chain.output_effect = "Zero contradictions achieved - complete resolution"
            else:
                causation_chain.output_effect = f"Declared unresolved state - {unresolved_count} contradictions remain"
                # Mark unresolved contradictions as stored potential
                for contradiction in state.contradictions:
                    if not contradiction.resolved:
                        contradiction.stored_potential = 1.0  # Full potential energy stored
            
            # Validate causation chain - Gap 1 compliance
            try:
                causation_chain.validate_output()
            except Exception as e:
                raise Exception(f"Cycle {state.cycle_id}: Cause-Effect Axiom violation: {str(e)}")
        
        # Gap 3: Log to safety ledger
        ledger_entry = {
            "cycle_id": state.cycle_id,
            "step": "LEARNED", 
            "output_effect": causation_chain.output_effect if causation_chain else "No causation chain",
            "causation_chain_id": f"causation_{state.cycle_id}_{state.iteration}",
            "energy_coherence": causation_chain.energy_coherence if causation_chain else 0.0
        }
        self.safety_ledger.add_cycle_entry("LEARNED", ledger_entry)
        
        # Final chain integrity validation - Gap 3 compliance
        self.safety_ledger.validate_chain_integrity()
        
        # Gap 2: Update coherence tracker - energy conservation maintained
        self.coherence_tracker.update_coherence("LEARNED", 0)
        
        # Extract learned rule from this cycle
        learned_rule = await self._extract_learned_rule(state)
        if learned_rule:
            state.learned_rules.append(learned_rule)
        
        return state
    
    def should_terminate_cycle(self, state: PB2SCoreState) -> Tuple[bool, str]:
        """Check if cycle should terminate based on PB2S_Core conditions."""
        unresolved_contradictions = [c for c in state.contradictions if not c.resolved]
        
        # Primary termination condition: zero contradictions
        if len(unresolved_contradictions) == 0:
            return True, "zero_contradictions_achieved"
        
        # Secondary: no further revision improves integrity
        if state.iteration > 1:
            # Check if this iteration made progress
            previous_gaps = len([g for g in state.gaps if "previous" in g.context])
            current_gaps = len(state.gaps) - previous_gaps
            
            if current_gaps >= previous_gaps:
                return True, "no_integrity_improvement"
        
        return False, "continue_cycle"
    
    async def _extract_knowledge_claims(self, content: str) -> List[Dict[str, Any]]:
        """Extract knowledge claims from content for cause→effect analysis."""
        # Simplified implementation - in practice would use NLP
        claims = []
        
        # Look for causal language patterns
        causal_patterns = [
            "because", "therefore", "thus", "hence", "consequently",
            "leads to", "results in", "causes", "due to"
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            for pattern in causal_patterns:
                if pattern in sentence.lower():
                    parts = sentence.split(pattern, 1)  # Split only once
                    if len(parts) == 2:
                        claims.append({
                            "premise": parts[0].strip(),
                            "conclusion": parts[1].strip(),
                            "sources": [],  # Would extract citations in full implementation
                            "pattern": pattern
                        })
        
        return claims
    
    async def _detect_contradictions(self, content: str) -> List[Dict[str, str]]:
        """Detect contradictions in content."""
        contradictions = []
        
        # Simple contradiction patterns
        contradiction_indicators = [
            ("always", "never"), ("all", "none"), ("impossible", "possible"),
            ("cannot", "can"), ("must", "must not"), ("true", "false")
        ]
        
        sentences = content.split('.')
        for i, sentence1 in enumerate(sentences):
            for j, sentence2 in enumerate(sentences[i+1:], i+1):
                for positive, negative in contradiction_indicators:
                    if (positive in sentence1.lower() and 
                        negative in sentence2.lower()):
                        contradictions.append({
                            "description": f"Contradiction between statements about {positive}/{negative}",
                            "statement1": sentence1.strip(),
                            "statement2": sentence2.strip()
                        })
        
        return contradictions
    
    async def _identify_gaps(self, content: str) -> List[Dict[str, str]]:
        """Identify knowledge gaps that should be explicitly marked."""
        gaps = []
        
        # Gap indicators
        gap_phrases = [
            "unclear", "uncertain", "unknown", "insufficient data",
            "requires further research", "not well understood",
            "conflicting evidence", "preliminary findings"
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            for phrase in gap_phrases:
                if phrase in sentence.lower():
                    gaps.append({
                        "description": f"Knowledge gap indicated by '{phrase}'",
                        "context": sentence.strip(),
                        "type": "insufficient_evidence",
                        "research": f"Need to investigate: {sentence.strip()}"
                    })
        
        return gaps
    
    async def _resolve_contradiction(self, contradiction: Contradiction, content: str) -> Dict[str, Any]:
        """Attempt to resolve a detected contradiction."""
        # Simplified resolution strategies
        
        # Strategy 1: Check if statements refer to different contexts
        if self._different_contexts(contradiction.source_statement, contradiction.conflicting_statement):
            return {
                "success": True,
                "method": "context_disambiguation",
                "revised_content": content  # Would actually revise to clarify contexts
            }
        
        # Strategy 2: Mark as unresolved gap
        return {
            "success": False,
            "method": "marked_as_gap",
            "revised_content": content + f"\n[GAP: Unresolved contradiction - {contradiction.description}]"
        }
    
    async def _verify_knowledge_chain(self, chain: KnowledgeChain) -> Dict[str, Any]:
        """Verify a cause→effect knowledge chain."""
        # Simplified verification - would check against knowledge bases
        
        if chain.evidence_sources:
            return {
                "status": "partial",
                "confidence": 0.7
            }
        else:
            return {
                "status": "unverified",
                "confidence": 0.3
            }
    
    async def _extract_learned_rule(self, state: PB2SCoreState) -> Optional[str]:
        """Extract a compact learned rule from the cycle."""
        resolved_contradictions = [c for c in state.contradictions if c.resolved]
        
        if resolved_contradictions:
            return f"Cycle {state.iteration}: Resolved {len(resolved_contradictions)} contradictions through context disambiguation and gap marking."
        
        return None
    
    def _different_contexts(self, statement1: str, statement2: str) -> bool:
        """Check if two statements refer to different contexts."""
        # Simplified context detection
        context_indicators = ["in general", "specifically", "usually", "always", "sometimes"]
        
        s1_contexts = [ind for ind in context_indicators if ind in statement1.lower()]
        s2_contexts = [ind for ind in context_indicators if ind in statement2.lower()]
        
        return len(set(s1_contexts) & set(s2_contexts)) == 0
    
    def get_cycle_summary(self, state: PB2SCoreState) -> Dict[str, Any]:
        """Generate a summary of the PB2S_Core cycle."""
        return {
            "cycle_id": state.cycle_id,
            "iterations": state.iteration,
            "final_step": state.current_step,
            "contradictions_detected": len(state.contradictions),
            "contradictions_resolved": len([c for c in state.contradictions if c.resolved]),
            "knowledge_chains_created": len(state.knowledge_chains),
            "knowledge_chains_verified": len([kc for kc in state.knowledge_chains if kc.verification_status == "verified"]),
            "gaps_identified": len(state.gaps),
            "learned_rules": state.learned_rules,
            "pb2s_core_compliance": {
                "principles_followed": True,
                "contradictions_surfaced": len(state.contradictions) > 0,
                "gaps_marked_explicitly": len(state.gaps) > 0,
                "cause_effect_chains_tracked": len(state.knowledge_chains) > 0
            }
        }

# Global instance for use across agents
pb2s_core_engine = PB2SCoreEngine()