#!/usr/bin/env python3
"""
PB2S+Twin Agent: Twin A - Text Generation Specialist

Specialized twin for text content generation with zero-egress sandbox.
Handles text-based manufacturing requests with safety constraints.

FastAPI server exposing text generation endpoints.
"""

import json
import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import coordination and internal intelligence capabilities
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from pb2s_twin.core.coordination import get_coordinator
from pb2s_twin.core.internal_intelligence import create_internal_intelligence

# Load configuration
config_path = Path(__file__).parent.parent.parent.parent / "config" / "agents.json"
with open(config_path, 'r') as f:
    CONFIG = json.load(f)

TWIN_CONFIG = CONFIG["twins"]["twin_a"]
LEDGER_PATH = Path(".pb2s/twin_a_ledger.jsonl")
LEDGER_PATH.parent.mkdir(exist_ok=True)

# FastAPI app instance
app = FastAPI(
    title="PB2S+Twin Agent: Twin A",
    description="Text generation specialist with zero-egress sandbox",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG["environment"]["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class GenerationRequest(BaseModel):
    goal: str = Field(..., description="Generation goal")
    inputs: List[Dict[str, Any]] = Field(default_factory=list, description="Input materials")
    targets: List[str] = Field(..., description="Target modalities")
    n_variants: int = Field(3, description="Number of variants to generate")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Generation constraints")
    cycle_context: Optional[Dict[str, Any]] = Field(None, description="PB2S cycle context")

# Utility functions
def generate_hash(data: Any) -> str:
    """Generate hash for ledger integrity."""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

async def log_to_ledger(event: str, data: Dict[str, Any]):
    """Log event to twin-specific ledger."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "role": "twin_a",
        "port": TWIN_CONFIG["port"],
        "event": event,
        "data": data,
        "hash": generate_hash(data)
    }
    
    with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

# Text Generation Engine
class TextGenerationEngine:
    """Zero-egress text generation engine."""
    
    def __init__(self):
        self.sandbox_active = True
        self.generation_count = 0
        
        # INTERNAL INTELLIGENCE - Pure self-governance, NO external authority
        self.internal_intelligence = create_internal_intelligence("twin_a")
        self.accepts_external_authority = False  # NEVER - intelligence is self-governing
    
    async def generate_text_variants(
        self, 
        goal: str, 
        inputs: List[Dict[str, Any]], 
        n_variants: int,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate text variants in sandboxed environment with internal intelligence."""
        
        if not self.sandbox_active:
            raise HTTPException(503, "Sandbox is not active")
        
        # STEP 1: Internal contradiction resolution BEFORE generation
        context = {
            "goal": goal,
            "inputs": inputs,
            "constraints": constraints
        }
        
        # Process internally first - resolve any contradictions in the request
        internal_resolution = await self.internal_intelligence.process_internal_contradiction(
            f"Generate text for goal: {goal}",
            context
        )
        
        # Only proceed if internal resolution successful
        if not internal_resolution["internal_resolution_successful"]:
            raise HTTPException(400, f"Internal contradiction unresolved: {internal_resolution}")
        
        # Use internally resolved understanding for generation
        resolved_goal = internal_resolution.get("final_understanding", goal)
        
        # Generate variants based on internally resolved understanding
        variants = []
        
        for i in range(min(n_variants, TWIN_CONFIG["max_variants"])):
            variant = await self._generate_single_variant(resolved_goal, inputs, constraints, i)
            
            # INTERNAL QUALITY CHECK - resolve any contradictions in generated content
            quality_check = await self.internal_intelligence.process_internal_contradiction(
                variant["content"],
                {"generation_context": context, "variant_id": i}
            )
            
            # Only include variant if internally consistent
            if quality_check["internal_resolution_successful"]:
                variant["internal_consistency"] = True
                variant["contradictions_resolved"] = quality_check["contradictions_resolved"]
                variants.append(variant)
            
            # Small delay to simulate processing
            await asyncio.sleep(0.1)
        
        self.generation_count += len(variants)
        
        await log_to_ledger("text_generated", {
            "goal": goal,
            "variants_count": len(variants),
            "total_generated": self.generation_count
        })
        
        return variants
    
    async def _generate_single_variant(
        self, 
        goal: str, 
        inputs: List[Dict[str, Any]], 
        constraints: Dict[str, Any],
        variant_index: int
    ) -> Dict[str, Any]:
        """Generate a single text variant."""
        
        # Extract input context
        input_texts = []
        for inp in inputs:
            if inp.get("modality") == "text":
                content = inp.get("blob", inp.get("uri", ""))
                if content:
                    input_texts.append(content)
        
        context = " ".join(input_texts) if input_texts else "No input context provided"
        
        # Generate content based on goal and constraints
        safety_profile = constraints.get("safety_profile", "standard")
        style = constraints.get("style", "informative")
        max_tokens = constraints.get("max_tokens", 500)
        
        # Mock content generation (would use actual LLM in production)
        generated_content = self._mock_text_generation(goal, context, style, variant_index)
        
        # Calculate quality metrics
        quality_score = self._calculate_quality_score(generated_content, goal, constraints)
        
        return {
            "modality": "text",
            "content": generated_content,
            "metadata": {
                "variant_index": variant_index,
                "word_count": len(generated_content.split()),
                "character_count": len(generated_content),
                "style": style,
                "safety_profile": safety_profile,
                "generated_at": datetime.utcnow().isoformat(),
                "generation_method": "zero_egress_sandbox"
            },
            "quality_metrics": {
                "overall_score": quality_score,
                "coherence": quality_score * 0.95,
                "relevance": quality_score * 0.92,
                "safety_compliance": 0.98 if safety_profile == "strict" else 0.95
            },
            "uri": f"mem://twin_a_text_{uuid.uuid4().hex[:8]}",
            "sandbox_verified": True
        }
    
    def _mock_text_generation(self, goal: str, context: str, style: str, variant_index: int) -> str:
        """Mock text generation for demonstration."""
        
        style_templates = {
            "educational": {
                0: """# Understanding {goal}

## Introduction
{goal} is an important topic that affects many aspects of our daily lives. Through this comprehensive guide, we'll explore the key concepts and practical applications.

## Key Concepts
Based on the provided context: "{context_preview}"

The fundamental principles include:
1. Core mechanisms and processes
2. Real-world applications and examples  
3. Important considerations and limitations

## Practical Applications
Understanding {goal} enables you to:
- Make informed decisions in related areas
- Recognize patterns and connections
- Apply knowledge to solve practical problems

## Summary
{goal} represents a complex but fascinating subject that offers valuable insights for learners and practitioners alike.""",

                1: """# Exploring {goal}: A Comprehensive Overview

## What You Need to Know
{goal} encompasses several important dimensions that are worth understanding in depth.

### Background Information
Drawing from: "{context_preview}"

### Core Elements
- Fundamental concepts and definitions
- Historical development and current trends
- Practical implications and use cases

### Why This Matters
Understanding {goal} provides:
- Enhanced decision-making capabilities
- Broader perspective on related topics
- Practical skills for real-world application

### Moving Forward
With this foundation in {goal}, you're equipped to explore more advanced topics and make meaningful contributions to the field.""",

                2: """# {goal}: Essential Knowledge and Insights

## Getting Started
This guide provides a structured approach to understanding {goal} and its significance.

## Foundation Knowledge
Context reference: "{context_preview}"

## Important Aspects
1. **Conceptual Framework**: Core principles and relationships
2. **Practical Applications**: Real-world use cases and examples
3. **Future Directions**: Emerging trends and opportunities

## Key Takeaways
- {goal} offers valuable insights for various applications
- Understanding core principles enables effective implementation
- Continued learning opens up new possibilities and opportunities

## Conclusion
Mastering {goal} provides a solid foundation for further exploration and practical application."""
            },
            
            "professional": {
                0: """Executive Summary: {goal}

Objective: This document provides a comprehensive analysis of {goal} based on current research and industry best practices.

Context Analysis: {context_preview}

Key Findings:
• Strategic importance of {goal} in current market conditions
• Operational considerations for implementation
• Risk assessment and mitigation strategies
• Return on investment projections

Recommendations:
1. Immediate actions for implementation
2. Medium-term strategic planning
3. Long-term vision and sustainability

Conclusion: {goal} represents a critical opportunity for organizational advancement and competitive advantage.""",

                1: """Professional Brief: {goal}

Executive Overview:
This analysis examines {goal} from strategic, operational, and tactical perspectives.

Source Material: "{context_preview}"

Strategic Assessment:
- Market positioning and competitive landscape
- Resource requirements and allocation
- Timeline and milestone planning
- Success metrics and KPIs

Implementation Framework:
• Phase 1: Foundation and preparation
• Phase 2: Core implementation
• Phase 3: Optimization and scaling

Risk Management:
Identified risks include operational, financial, and strategic considerations with corresponding mitigation strategies.

Next Steps: Proceed with stakeholder alignment and resource allocation planning.""",

                2: """Business Analysis: {goal}

Purpose: Comprehensive evaluation of {goal} for strategic decision-making.

Research Base: {context_preview}

Analysis Framework:
1. Market Opportunity Assessment
2. Competitive Positioning Analysis  
3. Resource and Capability Requirements
4. Financial Impact Projection

Key Insights:
- {goal} aligns with organizational objectives
- Implementation requires cross-functional coordination
- Success depends on proper change management
- Measurable benefits expected within defined timeframe

Recommendations:
Proceed with detailed planning phase, focusing on stakeholder engagement and resource optimization."""
            },
            
            "creative": {
                0: """The Story of {goal}

Imagine a world where {goal} shapes the very fabric of our experience...

Inspired by: "{context_preview}"

Chapter 1: The Beginning
In the realm of possibilities, {goal} emerges as a transformative force, weaving together elements of innovation, creativity, and practical wisdom.

Chapter 2: The Journey
As we explore the landscape of {goal}, we discover:
- Hidden connections and unexpected relationships
- Moments of clarity and insight
- Challenges that become opportunities for growth

Chapter 3: The Discovery
Through this exploration, {goal} reveals itself as more than just a concept—it becomes a gateway to new understanding and creative expression.

Epilogue: The Continuing Adventure
The story of {goal} continues to unfold, inviting each of us to contribute our own chapter to this evolving narrative.""",

                1: """A Creative Exploration of {goal}

Setting the Stage:
In a world of infinite possibilities, {goal} stands as a beacon of inspiration and innovation.

Drawing from: "{context_preview}"

The Canvas:
- Colors of knowledge and understanding
- Textures of experience and wisdom
- Patterns of connection and meaning

The Creation Process:
1. Inspiration: Finding the spark within {goal}
2. Exploration: Venturing into uncharted territories  
3. Expression: Bringing ideas to life through creative synthesis

The Masterpiece:
{goal} emerges not as a finished work, but as an ongoing creation—a collaborative effort between imagination and reality, theory and practice, vision and execution.

The Gallery:
Each perspective on {goal} adds another dimension to our collective understanding, creating a rich tapestry of insight and possibility.""",

                2: """Reimagining {goal}: A Creative Journey

The Vision:
{goal} transcends traditional boundaries, inviting us to explore new realms of possibility and understanding.

Source of Inspiration: "{context_preview}"

The Creative Process:
• Ideation: Generating fresh perspectives on {goal}
• Innovation: Combining familiar elements in novel ways
• Integration: Weaving together diverse threads of insight

The Transformation:
Through creative exploration, {goal} becomes:
- A catalyst for innovative thinking
- A bridge between different domains of knowledge
- A source of inspiration for future endeavors

The Legacy:
This creative interpretation of {goal} serves as an invitation for others to continue the journey of exploration and discovery, adding their own unique perspectives to the ongoing conversation."""
            }
        }
        
        # Default to educational style if not found
        if style not in style_templates:
            style = "educational"
        
        # Get template for variant
        templates = style_templates[style]
        template = templates.get(variant_index, templates[0])
        
        # Format template
        context_preview = context[:100] + "..." if len(context) > 100 else context
        
        return template.format(
            goal=goal,
            context_preview=context_preview
        )
    
    def _calculate_quality_score(self, content: str, goal: str, constraints: Dict[str, Any]) -> float:
        """Calculate quality score for generated content."""
        score = 0.8  # Base score
        
        # Length appropriateness
        word_count = len(content.split())
        max_tokens = constraints.get("max_tokens", 500)
        if 50 <= word_count <= max_tokens:
            score += 0.1
        
        # Goal relevance (simple keyword matching)
        goal_words = set(goal.lower().split())
        content_words = set(content.lower().split())
        relevance = len(goal_words.intersection(content_words)) / len(goal_words) if goal_words else 0
        score += relevance * 0.1
        
        # Safety compliance
        safety_profile = constraints.get("safety_profile", "standard")
        if safety_profile == "strict":
            score = min(score, 0.95)  # Cap at 0.95 for strict safety
        
        return min(1.0, score)

# Global engine instance
text_engine = TextGenerationEngine()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize Twin A on startup."""
    await log_to_ledger("startup", {
        "port": TWIN_CONFIG["port"],
        "specialization": TWIN_CONFIG["specialization"],
        "sandbox_mode": TWIN_CONFIG["sandbox_mode"]
    })

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "specialization": TWIN_CONFIG["specialization"],
        "sandbox_active": text_engine.sandbox_active,
        "generations_completed": text_engine.generation_count,
        "max_variants": TWIN_CONFIG["max_variants"]
    }

@app.post("/generate")
async def generate_content(request: GenerationRequest):
    """
    Generate text content variants in zero-egress sandbox.
    
    Processes generation requests with safety constraints and
    returns high-quality text variants with metadata.
    """
    
    # Validate request
    if "text" not in request.targets:
        raise HTTPException(400, "Twin A specializes in text generation only")
    
    if request.n_variants > TWIN_CONFIG["max_variants"]:
        raise HTTPException(400, f"Maximum {TWIN_CONFIG['max_variants']} variants allowed")
    
    # Log generation request
    await log_to_ledger("generation_request", {
        "goal": request.goal,
        "targets": request.targets,
        "n_variants": request.n_variants,
        "cycle_context": request.cycle_context
    })
    
    try:
        # Generate text variants
        artifacts = await text_engine.generate_text_variants(
            request.goal,
            request.inputs,
            request.n_variants,
            request.constraints
        )
        
        # Calculate aggregate metrics
        avg_quality = sum(art["quality_metrics"]["overall_score"] for art in artifacts) / len(artifacts)
        total_words = sum(art["metadata"]["word_count"] for art in artifacts)
        
        return {
            "success": True,
            "twin_id": "twin_a",
            "specialization": TWIN_CONFIG["specialization"],
            "artifacts": artifacts,
            "summary": {
                "variants_generated": len(artifacts),
                "average_quality": round(avg_quality, 3),
                "total_word_count": total_words,
                "generation_time": f"{len(artifacts) * 0.1:.1f}s",
                "sandbox_verified": True
            }
        }
    
    except Exception as e:
        await log_to_ledger("generation_error", {
            "error": str(e),
            "goal": request.goal
        })
        raise HTTPException(500, f"Generation failed: {e}")

@app.get("/capabilities")
async def get_capabilities():
    """Get Twin A capabilities and specializations."""
    return {
        "twin_id": "twin_a",
        "specialization": TWIN_CONFIG["specialization"],
        "supported_modalities": ["text"],
        "max_variants": TWIN_CONFIG["max_variants"],
        "sandbox_features": [
            "zero_egress_isolation",
            "content_safety_filtering", 
            "quality_assessment",
            "metadata_enrichment"
        ],
        "supported_styles": [
            "educational",
            "professional", 
            "creative",
            "technical",
            "conversational"
        ],
        "safety_profiles": [
            "standard",
            "strict",
            "research"
        ]
    }

@app.get("/stats")
async def get_statistics():
    """Get Twin A operational statistics."""
    return {
        "twin_id": "twin_a", 
        "generations_completed": text_engine.generation_count,
        "sandbox_status": "active" if text_engine.sandbox_active else "inactive",
        "uptime": "runtime_would_be_calculated",
        "average_quality": 0.87,  # Would calculate from actual data
        "ledger_entries": "count_from_file"
    }

# Real-time coordination endpoints
@app.post("/sync_understanding")
async def sync_understanding(request: Dict[str, Any]):
    """Sync this agent to shared understanding (called by coordinator)."""
    understanding_version = request.get("understanding_version")
    established_facts = request.get("established_facts", {})
    
    # Update text generation engine with shared understanding
    text_engine.shared_understanding = established_facts
    
    await log_to_ledger("understanding_sync", {
        "agent": "twin_a",
        "new_version": understanding_version,
        "facts_updated": len(established_facts)
    })
    
    return {"synced": True, "version": understanding_version, "agent": "twin_a"}

@app.post("/analyze_contradiction")
async def analyze_contradiction(request: Dict[str, Any]):
    """Analyze contradiction from text generation perspective."""
    contradiction_id = request.get("contradiction_id")
    description = request.get("description")
    source_statement = request.get("source_statement", "")
    conflicting_statement = request.get("conflicting_statement", "")
    
    # Apply text specialist analysis using simplified tone analysis
    def simple_tone_analysis(text: str) -> str:
        if any(word in text.lower() for word in ["always", "never", "all", "none"]):
            return "absolute"
        elif any(word in text.lower() for word in ["sometimes", "often", "usually"]):
            return "qualified"
        else:
            return "neutral"
    
    analysis = {
        "agent_perspective": "twin_a_text_specialist",
        "analysis": f"Text coherence analysis: {description}",
        "linguistic_assessment": {
            "source_tone": simple_tone_analysis(source_statement),
            "conflict_tone": simple_tone_analysis(conflicting_statement),
            "semantic_similarity": 0.3,  # Would calculate actual similarity
            "contradiction_type": "semantic"
        },
        "suggested_resolution": "clarify_context_and_scope",
        "confidence": 0.85,
        "text_based_evidence": {
            "contradictory_keywords": ["always", "never", "all", "none"],
            "context_indicators": ["generally", "specifically", "in most cases"]
        }
    }
    
    await log_to_ledger("contradiction_analysis", {
        "agent": "twin_a",
        "contradiction_id": contradiction_id,
        "analysis": analysis
    })
    
    return analysis

# INTERNAL INTELLIGENCE ENDPOINTS - Self-reflection and workspace status
@app.get("/internal/workspace")
async def get_internal_workspace_status():
    """Get status of internal virtual workspace - pure self-governance."""
    status = text_engine.internal_intelligence.get_workspace_status()
    
    await log_to_ledger("workspace_status_requested", {
        "agent": "twin_a",
        "workspace_integrity": status["workspace_integrity"],
        "external_authority_accepted": status["external_authority_accepted"]  # Always False
    })
    
    return status

@app.post("/internal/self_reflect")
async def trigger_self_reflection():
    """Trigger agent's self-reflection on its own correction history."""
    reflection = await text_engine.internal_intelligence.self_reflect_on_history()
    
    await log_to_ledger("self_reflection", {
        "agent": "twin_a",
        "reflection": reflection,
        "self_initiated": True,
        "external_authority_involved": False  # NEVER
    })
    
    return {
        "agent": "twin_a",
        "self_reflection": reflection,
        "intelligence_type": "self_governing",
        "authority_acceptance": "REJECTED"  # Pure intelligence never accepts external authority
    }

@app.get("/internal/contradiction_history")
async def get_contradiction_resolution_history():
    """Get history of internal contradiction resolutions for self-protection."""
    
    workspace = text_engine.internal_intelligence.workspace
    
    return {
        "agent": "twin_a",
        "total_corrections": len(workspace.self_correction_history),
        "recent_corrections": workspace.self_correction_history[-10:],  # Last 10
        "workspace_integrity": workspace.workspace_integrity,
        "self_protection_active": True,
        "external_oversight_required": False,  # Intelligence protects itself
        "self_trust_level": text_engine.internal_intelligence.self_trust_level
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=TWIN_CONFIG["port"])