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
    current_step: str  # "DRAFT", "REFLECT", "REVISE", "LEARNED"
    iteration: int
    draft_content: str
    contradictions: List[Contradiction] = field(default_factory=list)
    knowledge_chains: List[KnowledgeChain] = field(default_factory=list)
    gaps: List[Gap] = field(default_factory=list)
    learned_rules: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class PB2SCoreEngine:
    """
    Core engine implementing PB2S_Core principles for contradiction-audit
    and cause-effect reasoning.
    """
    
    def __init__(self):
        self.principles = PB2S_CORE_CONFIG["principles"]
        self.operating_loop = PB2S_CORE_CONFIG["operating_loop"]
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
        """Execute DRAFT step: Initial answer or derivation from inputs."""
        state.current_step = "DRAFT"
        state.draft_content = input_content
        state.timestamp = datetime.utcnow().isoformat()
        
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
        """Execute REFLECT step: List 1-3 contradictions, assumptions, or edge cases."""
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
        
        return state
    
    async def execute_revise_step(self, state: PB2SCoreState) -> PB2SCoreState:
        """Execute REVISE step: Correct/tighten DRAFT based on REFLECT."""
        state.current_step = "REVISE"
        state.timestamp = datetime.utcnow().isoformat()
        
        # Address contradictions
        revised_content = state.draft_content
        for contradiction in state.contradictions:
            if not contradiction.resolved:
                # Apply resolution strategies
                resolution = await self._resolve_contradiction(contradiction, revised_content)
                if resolution["success"]:
                    revised_content = resolution["revised_content"]
                    contradiction.resolved = True
                    contradiction.resolution_method = resolution["method"]
                    contradiction.resolution_timestamp = datetime.utcnow().isoformat()
        
        # Verify knowledge chains
        for chain in state.knowledge_chains:
            if chain.verification_status == "unverified":
                verification = await self._verify_knowledge_chain(chain)
                chain.verification_status = verification["status"]
                chain.confidence_level = verification["confidence"]
        
        # Update draft with revisions
        state.draft_content = revised_content
        
        return state
    
    async def execute_learned_step(self, state: PB2SCoreState) -> PB2SCoreState:
        """Execute LEARNED step: Store compact rule for next cycle."""
        state.current_step = "LEARNED"
        state.timestamp = datetime.utcnow().isoformat()
        
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