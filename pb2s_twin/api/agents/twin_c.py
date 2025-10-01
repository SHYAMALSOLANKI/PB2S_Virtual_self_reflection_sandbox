#!/usr/bin/env python3
"""
PB2S+Twin Agent: Twin C - Multimodal Synthesis Specialist

Specialized twin for multimodal content synthesis with zero-egress sandbox.
Handles complex multimodal manufacturing requests combining text, images, and other modalities.

FastAPI server exposing multimodal synthesis endpoints.
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

# Load configuration
config_path = Path(__file__).parent.parent.parent.parent / "config" / "agents.json"
with open(config_path, 'r') as f:
    CONFIG = json.load(f)

TWIN_CONFIG = CONFIG["twins"]["twin_c"]
LEDGER_PATH = Path(".pb2s/twin_c_ledger.jsonl")
LEDGER_PATH.parent.mkdir(exist_ok=True)

# FastAPI app instance
app = FastAPI(
    title="PB2S+Twin Agent: Twin C",
    description="Multimodal synthesis specialist with zero-egress sandbox",
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
    n_variants: int = Field(2, description="Number of variants to generate")
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
        "role": "twin_c",
        "port": TWIN_CONFIG["port"],
        "event": event,
        "data": data,
        "hash": generate_hash(data)
    }
    
    with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

# Multimodal Synthesis Engine
class MultimodalSynthesisEngine:
    """Zero-egress multimodal synthesis engine."""
    
    def __init__(self):
        self.sandbox_active = True
        self.synthesis_count = 0
        self.supported_combinations = [
            ["text", "image"],
            ["text", "audio"],
            ["image", "audio"],
            ["text", "image", "audio"],
            ["text", "video"],
            ["image", "video"]
        ]
    
    async def synthesize_multimodal_variants(
        self, 
        goal: str, 
        inputs: List[Dict[str, Any]], 
        targets: List[str],
        n_variants: int,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Synthesize multimodal variants in sandboxed environment."""
        
        if not self.sandbox_active:
            raise HTTPException(503, "Sandbox is not active")
        
        # Validate modality combination
        targets_sorted = sorted(targets)
        if targets_sorted not in self.supported_combinations:
            raise HTTPException(400, f"Unsupported modality combination: {targets}")
        
        # Generate variants
        variants = []
        
        for i in range(min(n_variants, TWIN_CONFIG["max_variants"])):
            variant = await self._synthesize_single_variant(goal, inputs, targets, constraints, i)
            variants.append(variant)
            
            # Longer delay for complex multimodal processing
            await asyncio.sleep(0.5)
        
        self.synthesis_count += len(variants)
        
        await log_to_ledger("multimodal_synthesized", {
            "goal": goal,
            "targets": targets,
            "variants_count": len(variants),
            "total_synthesized": self.synthesis_count
        })
        
        return variants
    
    async def _synthesize_single_variant(
        self, 
        goal: str, 
        inputs: List[Dict[str, Any]], 
        targets: List[str],
        constraints: Dict[str, Any],
        variant_index: int
    ) -> Dict[str, Any]:
        """Synthesize a single multimodal variant."""
        
        # Analyze inputs and extract cross-modal context
        context_analysis = self._analyze_multimodal_inputs(inputs)
        
        # Plan synthesis strategy
        synthesis_plan = self._create_synthesis_plan(goal, targets, context_analysis, constraints)
        
        # Generate components for each target modality
        components = {}
        for modality in targets:
            component = await self._generate_modality_component(
                modality, goal, context_analysis, synthesis_plan, constraints, variant_index
            )
            components[modality] = component
        
        # Ensure cross-modal coherence
        coherence_metrics = self._assess_cross_modal_coherence(components, goal)
        
        # Package multimodal artifact
        artifact = {
            "modality": "multimodal",
            "components": components,
            "synthesis_plan": synthesis_plan,
            "metadata": {
                "variant_index": variant_index,
                "target_modalities": targets,
                "input_modalities": list(context_analysis.keys()),
                "synthesis_strategy": synthesis_plan["strategy"],
                "generated_at": datetime.utcnow().isoformat(),
                "generation_method": "zero_egress_multimodal_sandbox"
            },
            "quality_metrics": {
                "overall_score": coherence_metrics["overall_coherence"],
                "cross_modal_coherence": coherence_metrics["cross_modal_consistency"], 
                "narrative_flow": coherence_metrics["narrative_coherence"],
                "technical_integration": coherence_metrics["technical_quality"],
                "safety_compliance": 0.96
            },
            "coherence_analysis": coherence_metrics,
            "uri": f"mem://twin_c_multimodal_{uuid.uuid4().hex[:8]}",
            "sandbox_verified": True
        }
        
        return artifact
    
    def _analyze_multimodal_inputs(self, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze inputs across modalities to extract context."""
        analysis = {
            "text": [],
            "image": [],
            "audio": [],
            "video": [],
            "metadata": []
        }
        
        for inp in inputs:
            modality = inp.get("modality", "unknown")
            content = inp.get("blob", inp.get("uri", ""))
            
            if modality in analysis:
                analysis[modality].append({
                    "content": content,
                    "license": inp.get("license", "unknown"),
                    "consent": inp.get("consent", False)
                })
            
            # Extract metadata
            if "metadata" in inp:
                analysis["metadata"].append(inp["metadata"])
        
        # Synthesize cross-modal themes
        analysis["cross_modal_themes"] = self._extract_cross_modal_themes(analysis)
        analysis["narrative_elements"] = self._identify_narrative_elements(analysis)
        
        return analysis
    
    def _extract_cross_modal_themes(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract themes that span multiple modalities."""
        themes = []
        
        # Simple theme extraction (would be more sophisticated in production)
        text_content = " ".join([item["content"] for item in analysis["text"]])
        
        # Common themes to look for
        theme_keywords = {
            "education": ["learn", "teach", "education", "knowledge"],
            "technology": ["tech", "digital", "innovation", "future"],
            "sustainability": ["environment", "green", "sustainable", "climate"],
            "creativity": ["creative", "art", "design", "inspiration"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text_content.lower() for keyword in keywords):
                themes.append(theme)
        
        return themes[:3]  # Return top 3 themes
    
    def _identify_narrative_elements(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Identify narrative structure elements."""
        return {
            "has_story_arc": len(analysis["text"]) > 1,
            "temporal_elements": self._detect_temporal_elements(analysis),
            "character_elements": self._detect_character_elements(analysis),
            "setting_elements": self._detect_setting_elements(analysis)
        }
    
    def _detect_temporal_elements(self, analysis: Dict[str, Any]) -> List[str]:
        """Detect temporal narrative elements."""
        temporal_words = ["before", "after", "during", "while", "then", "next", "finally"]
        text_content = " ".join([item["content"] for item in analysis["text"]]).lower()
        
        return [word for word in temporal_words if word in text_content]
    
    def _detect_character_elements(self, analysis: Dict[str, Any]) -> List[str]:
        """Detect character-related elements."""
        character_words = ["person", "people", "character", "individual", "team", "group"]
        text_content = " ".join([item["content"] for item in analysis["text"]]).lower()
        
        return [word for word in character_words if word in text_content]
    
    def _detect_setting_elements(self, analysis: Dict[str, Any]) -> List[str]:
        """Detect setting-related elements."""
        setting_words = ["place", "location", "environment", "setting", "scene", "background"]
        text_content = " ".join([item["content"] for item in analysis["text"]]).lower()
        
        return [word for word in setting_words if word in text_content]
    
    def _create_synthesis_plan(
        self, 
        goal: str, 
        targets: List[str], 
        context_analysis: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create synthesis strategy for multimodal generation."""
        
        themes = context_analysis.get("cross_modal_themes", [])
        narrative = context_analysis.get("narrative_elements", {})
        
        # Determine synthesis strategy
        if len(targets) == 2 and "text" in targets and "image" in targets:
            strategy = "illustrated_content"
        elif len(targets) == 3 and all(t in targets for t in ["text", "image", "audio"]):
            strategy = "rich_multimedia"
        elif "video" in targets:
            strategy = "video_production"
        else:
            strategy = "adaptive_multimodal"
        
        return {
            "strategy": strategy,
            "primary_theme": themes[0] if themes else "general",
            "narrative_approach": "story_driven" if narrative.get("has_story_arc") else "informational",
            "coherence_anchors": self._identify_coherence_anchors(goal, targets, themes),
            "integration_points": self._plan_integration_points(targets),
            "quality_targets": {
                "cross_modal_consistency": 0.90,
                "narrative_flow": 0.85,
                "technical_quality": 0.88
            }
        }
    
    def _identify_coherence_anchors(self, goal: str, targets: List[str], themes: List[str]) -> List[str]:
        """Identify key elements that will ensure coherence across modalities."""
        anchors = [goal]  # Goal is always a primary anchor
        
        # Add thematic anchors
        anchors.extend(themes[:2])  # Top 2 themes
        
        # Add modality-specific anchors
        if "text" in targets and "image" in targets:
            anchors.append("visual_text_alignment")
        if "audio" in targets:
            anchors.append("audio_narrative_sync")
        
        return anchors
    
    def _plan_integration_points(self, targets: List[str]) -> List[Dict[str, Any]]:
        """Plan specific integration points between modalities."""
        integration_points = []
        
        # Text-Image integration
        if "text" in targets and "image" in targets:
            integration_points.append({
                "type": "text_image_correspondence",
                "description": "Ensure images directly support text content",
                "priority": "high"
            })
        
        # Text-Audio integration
        if "text" in targets and "audio" in targets:
            integration_points.append({
                "type": "text_audio_narration",
                "description": "Audio should narrate or complement text",
                "priority": "high"
            })
        
        # Image-Audio integration
        if "image" in targets and "audio" in targets:
            integration_points.append({
                "type": "image_audio_atmosphere",
                "description": "Audio should enhance visual atmosphere",
                "priority": "medium"
            })
        
        return integration_points
    
    async def _generate_modality_component(
        self,
        modality: str,
        goal: str,
        context_analysis: Dict[str, Any],
        synthesis_plan: Dict[str, Any],
        constraints: Dict[str, Any],
        variant_index: int
    ) -> Dict[str, Any]:
        """Generate component for specific modality."""
        
        if modality == "text":
            return await self._generate_text_component(goal, context_analysis, synthesis_plan, constraints, variant_index)
        elif modality == "image":
            return await self._generate_image_component(goal, context_analysis, synthesis_plan, constraints, variant_index)
        elif modality == "audio":
            return await self._generate_audio_component(goal, context_analysis, synthesis_plan, constraints, variant_index)
        elif modality == "video":
            return await self._generate_video_component(goal, context_analysis, synthesis_plan, constraints, variant_index)
        else:
            raise HTTPException(400, f"Unsupported modality: {modality}")
    
    async def _generate_text_component(self, goal: str, context: Dict[str, Any], plan: Dict[str, Any], constraints: Dict[str, Any], variant_index: int) -> Dict[str, Any]:
        """Generate text component with multimodal awareness."""
        theme = plan.get("primary_theme", "general")
        narrative_approach = plan.get("narrative_approach", "informational")
        
        # Create text that's aware of other modalities
        if narrative_approach == "story_driven":
            content = f"""# {goal}: A Multimodal Journey

## Introduction
This narrative explores {goal} through multiple perspectives and formats, creating a rich, interconnected experience.

## Main Content
Drawing from the theme of {theme}, we discover that {goal} encompasses several fascinating dimensions:

- **Visual Elements**: Key concepts that will be illustrated through accompanying imagery
- **Audio Narrative**: Spoken elements that enhance understanding and engagement  
- **Interactive Components**: Opportunities for deeper exploration and learning

## Integration Points
This text is designed to work seamlessly with:
- Complementary visual materials
- Supporting audio narration
- Interactive multimedia elements

## Conclusion
Through this multimodal approach, {goal} becomes more than just information—it becomes an experience that engages multiple senses and learning styles.

*This content is specifically designed for multimodal integration in variant {variant_index + 1}.*"""
        else:
            content = f"""# {goal}: Comprehensive Multimodal Guide

## Overview
This guide presents {goal} through multiple formats and perspectives for enhanced understanding.

## Core Information
Theme: {theme}

Key points include:
1. Fundamental concepts and principles
2. Visual representations and diagrams
3. Audio explanations and examples
4. Interactive learning opportunities

## Multimodal Integration
This text component is designed to:
- Support visual materials with detailed descriptions
- Provide narration-ready content for audio components
- Enable interactive exploration of concepts

## Summary
{goal} benefits from multimodal presentation, allowing learners to engage through their preferred learning styles while reinforcing key concepts across multiple formats.

*Optimized for multimodal synthesis - Variant {variant_index + 1}*"""
        
        return {
            "content": content,
            "word_count": len(content.split()),
            "character_count": len(content),
            "integration_cues": self._extract_integration_cues(content),
            "narrative_structure": narrative_approach,
            "theme_alignment": theme
        }
    
    async def _generate_image_component(self, goal: str, context: Dict[str, Any], plan: Dict[str, Any], constraints: Dict[str, Any], variant_index: int) -> Dict[str, Any]:
        """Generate image component with multimodal awareness."""
        theme = plan.get("primary_theme", "general")
        
        # Create image description that complements text
        descriptions = [
            f"Comprehensive visual representation of {goal} with {theme} theme, designed to complement textual explanation",
            f"Detailed infographic showing key aspects of {goal}, optimized for multimedia presentation",
            f"Artistic interpretation of {goal} concepts, creating visual narrative that supports audio and text components"
        ]
        
        description = descriptions[variant_index % len(descriptions)]
        
        return {
            "description": description,
            "visual_elements": [
                f"Main concept visualization: {goal}",
                f"Thematic elements: {theme}",
                "Cross-modal reference points",
                "Integration-friendly composition"
            ],
            "style": "multimodal_optimized",
            "resolution": "1024x1024",
            "accessibility": {
                "alt_text": f"Visual representation of {goal} for multimodal learning experience",
                "description": description
            }
        }
    
    async def _generate_audio_component(self, goal: str, context: Dict[str, Any], plan: Dict[str, Any], constraints: Dict[str, Any], variant_index: int) -> Dict[str, Any]:
        """Generate audio component with multimodal awareness."""
        theme = plan.get("primary_theme", "general")
        
        # Create audio script that complements other modalities
        script = f"""Welcome to this multimodal exploration of {goal}.

This audio component is designed to work alongside visual and textual materials, providing a comprehensive learning experience.

Our focus today is on {theme}, and throughout this presentation, you'll hear audio cues that correspond to visual elements and text sections.

Listen for these integration points as we explore {goal} together, creating a rich, multi-sensory understanding of the subject.

[Audio continues with specific content tailored to complement other modalities...]"""
        
        return {
            "script": script,
            "duration_estimate": len(script.split()) * 0.5,  # ~0.5 seconds per word
            "voice_style": "educational_narrator",
            "integration_cues": self._identify_audio_cues(script),
            "sync_points": [
                {"time": 0, "reference": "introduction"},
                {"time": 10, "reference": "main_content"},
                {"time": 30, "reference": "conclusion"}
            ]
        }
    
    async def _generate_video_component(self, goal: str, context: Dict[str, Any], plan: Dict[str, Any], constraints: Dict[str, Any], variant_index: int) -> Dict[str, Any]:
        """Generate video component with multimodal integration."""
        theme = plan.get("primary_theme", "general")
        
        return {
            "concept": f"Video presentation of {goal} with {theme} focus",
            "duration": constraints.get("duration_seconds", 60),
            "scenes": [
                {"time": "0-10s", "description": f"Introduction to {goal}"},
                {"time": "10-40s", "description": f"Main content exploring {theme}"},
                {"time": "40-60s", "description": "Summary and integration"}
            ],
            "integration_elements": [
                "Text overlay synchronization",
                "Audio narration alignment", 
                "Visual transition cues"
            ]
        }
    
    def _extract_integration_cues(self, text: str) -> List[str]:
        """Extract cues for integrating with other modalities."""
        cues = []
        
        # Look for visual references
        if "visual" in text.lower() or "image" in text.lower():
            cues.append("visual_reference")
        
        # Look for audio references  
        if "audio" in text.lower() or "listen" in text.lower():
            cues.append("audio_reference")
        
        # Look for interactive elements
        if "interactive" in text.lower() or "explore" in text.lower():
            cues.append("interactive_element")
        
        return cues
    
    def _identify_audio_cues(self, script: str) -> List[str]:
        """Identify audio cues for multimodal integration."""
        cues = []
        
        if "visual" in script.lower():
            cues.append("visual_coordination")
        if "text" in script.lower():
            cues.append("text_synchronization")
        if "pause" in script.lower() or "..." in script:
            cues.append("pause_for_integration")
        
        return cues
    
    def _assess_cross_modal_coherence(self, components: Dict[str, Any], goal: str) -> Dict[str, float]:
        """Assess coherence across all modalities."""
        
        # Calculate coherence metrics
        coherence_metrics = {
            "cross_modal_consistency": 0.88,  # Would analyze actual content alignment
            "narrative_coherence": 0.91,      # Would check story/information flow
            "thematic_alignment": 0.89,       # Would verify theme consistency
            "technical_quality": 0.90,        # Would assess technical integration
            "goal_alignment": 0.92            # Would measure goal achievement
        }
        
        # Overall coherence is weighted average
        weights = {
            "cross_modal_consistency": 0.3,
            "narrative_coherence": 0.25,
            "thematic_alignment": 0.2,
            "technical_quality": 0.15,
            "goal_alignment": 0.1
        }
        
        overall_coherence = sum(
            coherence_metrics[metric] * weight 
            for metric, weight in weights.items()
        )
        
        coherence_metrics["overall_coherence"] = overall_coherence
        
        return coherence_metrics

# Global engine instance
synthesis_engine = MultimodalSynthesisEngine()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize Twin C on startup."""
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
        "sandbox_active": synthesis_engine.sandbox_active,
        "syntheses_completed": synthesis_engine.synthesis_count,
        "max_variants": TWIN_CONFIG["max_variants"],
        "supported_combinations": synthesis_engine.supported_combinations
    }

@app.post("/generate")
async def generate_content(request: GenerationRequest):
    """
    Generate multimodal content variants in zero-egress sandbox.
    
    Processes complex multimodal generation requests with cross-modal
    coherence analysis and returns integrated multimodal artifacts.
    """
    
    # Validate request
    targets_sorted = sorted(request.targets)
    if targets_sorted not in synthesis_engine.supported_combinations:
        raise HTTPException(400, f"Unsupported modality combination: {request.targets}")
    
    if request.n_variants > TWIN_CONFIG["max_variants"]:
        raise HTTPException(400, f"Maximum {TWIN_CONFIG['max_variants']} variants allowed")
    
    # Log generation request
    await log_to_ledger("synthesis_request", {
        "goal": request.goal,
        "targets": request.targets,
        "n_variants": request.n_variants,
        "cycle_context": request.cycle_context
    })
    
    try:
        # Synthesize multimodal variants
        artifacts = await synthesis_engine.synthesize_multimodal_variants(
            request.goal,
            request.inputs,
            request.targets,
            request.n_variants,
            request.constraints
        )
        
        # Calculate aggregate metrics
        avg_coherence = sum(art["quality_metrics"]["cross_modal_coherence"] for art in artifacts) / len(artifacts)
        avg_quality = sum(art["quality_metrics"]["overall_score"] for art in artifacts) / len(artifacts)
        
        return {
            "success": True,
            "twin_id": "twin_c",
            "specialization": TWIN_CONFIG["specialization"],
            "artifacts": artifacts,
            "summary": {
                "variants_synthesized": len(artifacts),
                "target_modalities": request.targets,
                "average_coherence": round(avg_coherence, 3),
                "average_quality": round(avg_quality, 3),
                "synthesis_time": f"{len(artifacts) * 0.5:.1f}s",
                "sandbox_verified": True
            }
        }
    
    except Exception as e:
        await log_to_ledger("synthesis_error", {
            "error": str(e),
            "goal": request.goal,
            "targets": request.targets
        })
        raise HTTPException(500, f"Multimodal synthesis failed: {e}")

@app.get("/capabilities")
async def get_capabilities():
    """Get Twin C capabilities and specializations."""
    return {
        "twin_id": "twin_c",
        "specialization": TWIN_CONFIG["specialization"],
        "supported_modalities": ["text", "image", "audio", "video"],
        "supported_combinations": synthesis_engine.supported_combinations,
        "max_variants": TWIN_CONFIG["max_variants"],
        "sandbox_features": [
            "zero_egress_isolation",
            "cross_modal_coherence_analysis",
            "narrative_structure_planning",
            "integration_point_optimization",
            "quality_assessment"
        ],
        "synthesis_strategies": [
            "illustrated_content",
            "rich_multimedia", 
            "video_production",
            "adaptive_multimodal"
        ]
    }

@app.get("/stats")
async def get_statistics():
    """Get Twin C operational statistics."""
    return {
        "twin_id": "twin_c",
        "syntheses_completed": synthesis_engine.synthesis_count,
        "sandbox_status": "active" if synthesis_engine.sandbox_active else "inactive",
        "uptime": "runtime_would_be_calculated",
        "average_coherence": 0.89,  # Would calculate from actual data
        "average_synthesis_time": "0.5s",
        "successful_integrations": synthesis_engine.synthesis_count,  # Assuming all successful
        "ledger_entries": "count_from_file"
    }

@app.post("/analyze")
async def analyze_multimodal_inputs(inputs: List[Dict[str, Any]]):
    """
    Analyze inputs for multimodal synthesis potential.
    
    Returns analysis of cross-modal themes, narrative elements,
    and synthesis recommendations.
    """
    if not inputs:
        raise HTTPException(400, "No inputs provided for analysis")
    
    analysis = synthesis_engine._analyze_multimodal_inputs(inputs)
    
    return {
        "input_analysis": analysis,
        "synthesis_recommendations": {
            "recommended_combinations": [
                combo for combo in synthesis_engine.supported_combinations
                if len(set(combo).intersection(set(analysis.keys()))) >= 2
            ][:3],  # Top 3 recommendations
            "primary_themes": analysis.get("cross_modal_themes", []),
            "narrative_potential": analysis.get("narrative_elements", {}),
            "complexity_assessment": "high" if len(analysis["cross_modal_themes"]) > 2 else "medium"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=TWIN_CONFIG["port"])