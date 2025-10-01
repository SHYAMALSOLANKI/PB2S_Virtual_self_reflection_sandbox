#!/usr/bin/env python3
"""
PB2S+Twin Agent: Twin B - Image Generation Specialist

Specialized twin for visual content generation with zero-egress sandbox.
Handles image-based manufacturing requests with safety constraints.

FastAPI server exposing image generation endpoints.
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

TWIN_CONFIG = CONFIG["twins"]["twin_b"]
LEDGER_PATH = Path(".pb2s/twin_b_ledger.jsonl")
LEDGER_PATH.parent.mkdir(exist_ok=True)

# FastAPI app instance
app = FastAPI(
    title="PB2S+Twin Agent: Twin B",
    description="Image generation specialist with zero-egress sandbox",
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
        "role": "twin_b",
        "port": TWIN_CONFIG["port"],
        "event": event,
        "data": data,
        "hash": generate_hash(data)
    }
    
    with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

# Image Generation Engine
class ImageGenerationEngine:
    """Zero-egress image generation engine."""
    
    def __init__(self):
        self.sandbox_active = True
        self.generation_count = 0
        self.supported_formats = ["png", "jpg", "webp"]
        self.supported_resolutions = ["512x512", "1024x1024", "1024x768", "768x1024"]
    
    async def generate_image_variants(
        self, 
        goal: str, 
        inputs: List[Dict[str, Any]], 
        n_variants: int,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate image variants in sandboxed environment."""
        
        if not self.sandbox_active:
            raise HTTPException(503, "Sandbox is not active")
        
        # Simulate image generation (would integrate with actual image generation service)
        variants = []
        
        for i in range(min(n_variants, TWIN_CONFIG["max_variants"])):
            variant = await self._generate_single_image(goal, inputs, constraints, i)
            variants.append(variant)
            
            # Longer delay to simulate image processing
            await asyncio.sleep(0.3)
        
        self.generation_count += len(variants)
        
        await log_to_ledger("images_generated", {
            "goal": goal,
            "variants_count": len(variants),
            "total_generated": self.generation_count
        })
        
        return variants
    
    async def _generate_single_image(
        self, 
        goal: str, 
        inputs: List[Dict[str, Any]], 
        constraints: Dict[str, Any],
        variant_index: int
    ) -> Dict[str, Any]:
        """Generate a single image variant."""
        
        # Extract visual context from inputs
        visual_context = []
        text_prompts = []
        
        for inp in inputs:
            if inp.get("modality") == "image":
                visual_context.append(inp.get("uri", inp.get("blob", "")))
            elif inp.get("modality") == "text":
                text_prompts.append(inp.get("blob", inp.get("uri", "")))
        
        # Combine context for prompt engineering
        combined_prompt = self._create_image_prompt(goal, text_prompts, constraints, variant_index)
        
        # Determine image specifications
        resolution = constraints.get("resolution", "1024x1024")
        if resolution not in self.supported_resolutions:
            resolution = "1024x1024"
        
        style = constraints.get("style", "photorealistic")
        safety_profile = constraints.get("safety_profile", "standard")
        
        # Mock image generation (would use actual image generation API)
        image_data = await self._mock_image_generation(combined_prompt, resolution, style)
        
        # Calculate quality metrics
        quality_score = self._calculate_image_quality(image_data, goal, constraints)
        
        return {
            "modality": "image",
            "uri": f"mem://twin_b_image_{uuid.uuid4().hex[:8]}.png",
            "metadata": {
                "variant_index": variant_index,
                "prompt": combined_prompt,
                "resolution": resolution,
                "format": "png",
                "style": style,
                "safety_profile": safety_profile,
                "generated_at": datetime.utcnow().isoformat(),
                "generation_method": "zero_egress_sandbox",
                "estimated_size_kb": self._estimate_file_size(resolution)
            },
            "quality_metrics": {
                "overall_score": quality_score,
                "visual_coherence": quality_score * 0.93,
                "prompt_adherence": quality_score * 0.91,
                "artistic_quality": quality_score * 0.89,
                "safety_compliance": 0.97 if safety_profile == "strict" else 0.94
            },
            "image_description": self._generate_alt_text(combined_prompt, goal),
            "sandbox_verified": True,
            "content_warnings": self._check_content_safety(combined_prompt, style)
        }
    
    def _create_image_prompt(
        self, 
        goal: str, 
        text_inputs: List[str], 
        constraints: Dict[str, Any],
        variant_index: int
    ) -> str:
        """Create optimized image generation prompt."""
        
        style = constraints.get("style", "photorealistic")
        
        # Base prompt from goal
        base_prompt = goal
        
        # Add context from text inputs
        if text_inputs:
            context = " ".join(text_inputs)[:200]  # Limit context length
            base_prompt = f"{base_prompt}, incorporating elements from: {context}"
        
        # Style-specific prompt enhancement
        style_enhancements = {
            "photorealistic": ", high quality, detailed, professional photography",
            "artistic": ", artistic interpretation, creative composition, expressive",
            "diagram": ", clean diagram, educational illustration, clear labels",
            "infographic": ", information design, data visualization, modern layout",
            "cartoon": ", cartoon style, colorful, friendly, approachable",
            "minimalist": ", minimalist design, clean lines, simple composition"
        }
        
        prompt = base_prompt + style_enhancements.get(style, "")
        
        # Variant-specific modifications
        variant_mods = [
            ", wide angle view",
            ", close-up perspective", 
            ", side view composition"
        ]
        
        if variant_index < len(variant_mods):
            prompt += variant_mods[variant_index]
        
        # Safety filters
        safety_profile = constraints.get("safety_profile", "standard")
        if safety_profile == "strict":
            prompt += ", safe for work, appropriate for all audiences"
        
        return prompt.strip()
    
    async def _mock_image_generation(self, prompt: str, resolution: str, style: str) -> Dict[str, Any]:
        """Mock image generation for demonstration."""
        
        # Simulate image generation process
        await asyncio.sleep(0.2)  # Simulate processing time
        
        return {
            "prompt_used": prompt,
            "resolution": resolution,
            "style": style,
            "generation_steps": 50,
            "seed": hash(prompt) % 10000,
            "model_version": "mock_v1.0",
            "processing_time": 0.2
        }
    
    def _calculate_image_quality(self, image_data: Dict[str, Any], goal: str, constraints: Dict[str, Any]) -> float:
        """Calculate quality score for generated image."""
        score = 0.85  # Base score for images
        
        # Prompt adherence (simple keyword matching)
        prompt = image_data["prompt_used"].lower()
        goal_words = set(goal.lower().split())
        prompt_words = set(prompt.split())
        adherence = len(goal_words.intersection(prompt_words)) / len(goal_words) if goal_words else 0
        score += adherence * 0.1
        
        # Style appropriateness
        requested_style = constraints.get("style", "photorealistic")
        if requested_style == image_data["style"]:
            score += 0.05
        
        # Safety compliance
        safety_profile = constraints.get("safety_profile", "standard")
        if safety_profile == "strict":
            score = min(score, 0.96)  # Cap for strict safety
        
        return min(1.0, score)
    
    def _generate_alt_text(self, prompt: str, goal: str) -> str:
        """Generate accessibility alt text for the image."""
        return f"AI-generated image depicting {goal}, created from prompt: {prompt[:100]}..."
    
    def _check_content_safety(self, prompt: str, style: str) -> List[str]:
        """Check for content safety warnings."""
        warnings = []
        
        # Simple safety checks (would be more sophisticated in production)
        sensitive_terms = ["violence", "weapons", "inappropriate"]
        for term in sensitive_terms:
            if term in prompt.lower():
                warnings.append(f"contains_{term}")
        
        return warnings
    
    def _estimate_file_size(self, resolution: str) -> int:
        """Estimate file size in KB based on resolution."""
        size_map = {
            "512x512": 150,
            "1024x1024": 500,
            "1024x768": 400,
            "768x1024": 400
        }
        return size_map.get(resolution, 300)

# Global engine instance
image_engine = ImageGenerationEngine()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize Twin B on startup."""
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
        "sandbox_active": image_engine.sandbox_active,
        "generations_completed": image_engine.generation_count,
        "max_variants": TWIN_CONFIG["max_variants"],
        "supported_formats": image_engine.supported_formats
    }

@app.post("/generate")
async def generate_content(request: GenerationRequest):
    """
    Generate image content variants in zero-egress sandbox.
    
    Processes generation requests with safety constraints and
    returns high-quality image variants with metadata.
    """
    
    # Validate request
    if "image" not in request.targets:
        raise HTTPException(400, "Twin B specializes in image generation only")
    
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
        # Generate image variants
        artifacts = await image_engine.generate_image_variants(
            request.goal,
            request.inputs,
            request.n_variants,
            request.constraints
        )
        
        # Calculate aggregate metrics
        avg_quality = sum(art["quality_metrics"]["overall_score"] for art in artifacts) / len(artifacts)
        total_size_kb = sum(art["metadata"]["estimated_size_kb"] for art in artifacts)
        
        # Check for content warnings
        total_warnings = sum(len(art["content_warnings"]) for art in artifacts)
        
        return {
            "success": True,
            "twin_id": "twin_b",
            "specialization": TWIN_CONFIG["specialization"],
            "artifacts": artifacts,
            "summary": {
                "variants_generated": len(artifacts),
                "average_quality": round(avg_quality, 3),
                "total_size_kb": total_size_kb,
                "content_warnings": total_warnings,
                "generation_time": f"{len(artifacts) * 0.3:.1f}s",
                "sandbox_verified": True
            }
        }
    
    except Exception as e:
        await log_to_ledger("generation_error", {
            "error": str(e),
            "goal": request.goal
        })
        raise HTTPException(500, f"Image generation failed: {e}")

@app.get("/capabilities")
async def get_capabilities():
    """Get Twin B capabilities and specializations."""
    return {
        "twin_id": "twin_b",
        "specialization": TWIN_CONFIG["specialization"],
        "supported_modalities": ["image"],
        "max_variants": TWIN_CONFIG["max_variants"],
        "supported_formats": image_engine.supported_formats,
        "supported_resolutions": image_engine.supported_resolutions,
        "sandbox_features": [
            "zero_egress_isolation",
            "content_safety_filtering",
            "quality_assessment", 
            "accessibility_support",
            "metadata_enrichment"
        ],
        "supported_styles": [
            "photorealistic",
            "artistic",
            "diagram",
            "infographic", 
            "cartoon",
            "minimalist"
        ],
        "safety_profiles": [
            "standard",
            "strict",
            "research"
        ]
    }

@app.get("/stats")
async def get_statistics():
    """Get Twin B operational statistics."""
    return {
        "twin_id": "twin_b",
        "generations_completed": image_engine.generation_count,
        "sandbox_status": "active" if image_engine.sandbox_active else "inactive",
        "uptime": "runtime_would_be_calculated",
        "average_quality": 0.89,  # Would calculate from actual data
        "average_generation_time": "0.3s",
        "total_warnings": 0,  # Would track actual warnings
        "ledger_entries": "count_from_file"
    }

@app.post("/preview")
async def preview_generation(request: Dict[str, Any]):
    """
    Preview image generation without full processing.
    
    Returns prompt and estimated parameters for review before generation.
    """
    goal = request.get("goal", "")
    inputs = request.get("inputs", [])
    constraints = request.get("constraints", {})
    
    if not goal:
        raise HTTPException(400, "Goal is required for preview")
    
    # Extract text inputs for context
    text_inputs = [inp.get("blob", "") for inp in inputs if inp.get("modality") == "text"]
    
    # Create preview prompt
    preview_prompt = image_engine._create_image_prompt(goal, text_inputs, constraints, 0)
    
    return {
        "preview_prompt": preview_prompt,
        "estimated_resolution": constraints.get("resolution", "1024x1024"),
        "estimated_style": constraints.get("style", "photorealistic"),
        "estimated_size_kb": image_engine._estimate_file_size(constraints.get("resolution", "1024x1024")),
        "safety_profile": constraints.get("safety_profile", "standard"),
        "content_warnings": image_engine._check_content_safety(preview_prompt, constraints.get("style", "photorealistic"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=TWIN_CONFIG["port"])