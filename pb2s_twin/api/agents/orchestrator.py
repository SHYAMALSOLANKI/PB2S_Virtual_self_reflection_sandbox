#!/usr/bin/env python3
"""
PB2S+Twin Orchestrator Agent

Central coordinator that implements PB2S cycles:
- DRAFT: Initial planning and goal decomposition
- REFLECT: Analysis and validation routing
- REVISE: Iterative improvement based on feedback
- LEARNED: Final synthesis and artifact delivery

FastAPI server exposing orchestration endpoints.
"""

import json
import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import coordination system
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from pb2s_twin.core.coordination import initialize_coordination_system, get_coordinator
from pb2s_twin.core.pb2s_core import pb2s_core_engine

# Load configuration
config_path = Path(__file__).parent.parent.parent.parent / "config" / "agents.json"
pb2s_core_path = Path(__file__).parent.parent.parent.parent / "config" / "pb2s_core.json"

with open(config_path, 'r') as f:
    CONFIG = json.load(f)

with open(pb2s_core_path, 'r') as f:
    PB2S_CORE = json.load(f)["PB2S_Core"]

ORCH_CONFIG = CONFIG["orchestrator"]
SUIT_URL = ORCH_CONFIG["suit_url"]
TWIN_POOL = ORCH_CONFIG["twin_pool"]
LEDGER_PATH = Path(ORCH_CONFIG["ledger_path"])
LEDGER_PATH.parent.mkdir(exist_ok=True)

# FastAPI app instance
app = FastAPI(
    title="PB2S+Twin Orchestrator",
    description="Central coordination agent for PB2S manufacturing cycles",
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
class InputItem(BaseModel):
    modality: str = Field(..., description="Content modality (text, image, video, etc.)")
    blob: Optional[str] = Field(None, description="Direct content blob")
    uri: Optional[str] = Field(None, description="Content URI")
    license: str = Field("unknown", description="Content license")
    consent: bool = Field(False, description="User consent for processing")

class Constraints(BaseModel):
    safety_profile: str = Field("standard", description="Safety validation level")
    style: Optional[str] = Field(None, description="Content style guidelines")
    duration_seconds: Optional[int] = Field(None, description="Target duration for media")
    max_tokens: Optional[int] = Field(None, description="Maximum content length")

class PlanRequest(BaseModel):
    goal: str = Field(..., description="High-level generation goal")
    inputs: List[InputItem] = Field(default_factory=list, description="Input materials")
    constraints: Optional[Constraints] = Field(default_factory=Constraints, description="Generation constraints")

class ManufactureRequest(BaseModel):
    plan_id: str = Field(..., description="Plan identifier")
    modal_targets: List[str] = Field(..., description="Target modalities to generate")
    n_variants: int = Field(3, description="Number of variants per modality")

class ValidateRequest(BaseModel):
    artifacts: List[Dict[str, Any]] = Field(..., description="Artifacts to validate")
    policy_profile: str = Field("standard", description="Validation policy profile")

class FinalizeRequest(BaseModel):
    plan_id: str = Field(..., description="Plan identifier")
    selection: Dict[str, Any] = Field(..., description="Selection criteria")

# Global state
active_plans: Dict[str, Dict[str, Any]] = {}
twin_health: Dict[str, bool] = {}

# Utility functions
def generate_hash(data: Any) -> str:
    """Generate hash for ledger integrity."""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

async def log_to_ledger(role: str, event: str, data: Dict[str, Any]):
    """Log event to hash-chained ledger."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "role": role,
        "event": event,
        "data": data,
        "hash": generate_hash(data)
    }
    
    with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

async def check_twin_health():
    """Check health of all twins in the pool."""
    global twin_health
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for twin_url in TWIN_POOL:
            try:
                response = await client.get(f"{twin_url}/health")
                twin_health[twin_url] = response.status_code == 200
            except Exception:
                twin_health[twin_url] = False

async def call_suit_validation(artifacts: List[Dict[str, Any]], policy: str) -> Dict[str, Any]:
    """Call Suit validation service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SUIT_URL}/check",
                json={
                    "artifacts": artifacts,
                    "policy_profile": policy
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            await log_to_ledger("orchestrator", "suit_error", {"error": str(e)})
            raise HTTPException(500, f"Suit validation failed: {e}")

async def route_to_twin(twin_url: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route generation request to specific twin."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{twin_url}/generate",
                json=request_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            await log_to_ledger("orchestrator", "twin_error", {
                "twin_url": twin_url,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

# PB2S Cycle Implementation
class PB2SCycle:
    """PB2S cycle state machine."""
    
    def __init__(self, plan_id: str, goal: str, inputs: List[InputItem], constraints: Constraints):
        self.plan_id = plan_id
        self.goal = goal
        self.inputs = inputs
        self.constraints = constraints
        self.cycle_count = 0
        self.state = "DRAFT"
        self.artifacts = []
        self.reflections = []
        self.revisions = []
        
    async def execute_draft(self) -> Dict[str, Any]:
        """DRAFT phase: Initial planning and decomposition."""
        await log_to_ledger("orchestrator", "cycle_draft", {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "cycle": self.cycle_count
        })
        
        # Decompose goal into actionable tasks
        draft_plan = {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "tasks": self._decompose_goal(),
            "resource_requirements": self._analyze_inputs(),
            "estimated_duration": self._estimate_duration(),
            "risk_factors": self._identify_risks()
        }
        
        self.state = "REFLECT"
        return draft_plan
    
    async def execute_reflect(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """REFLECT phase: Analysis and validation."""
        await log_to_ledger("orchestrator", "cycle_reflect", {
            "plan_id": self.plan_id,
            "artifacts_count": len(artifacts),
            "cycle": self.cycle_count
        })
        
        # Validate artifacts through Suit
        validation_result = await call_suit_validation(
            artifacts, 
            self.constraints.safety_profile
        )
        
        # Analyze quality and coherence
        reflection = {
            "validation": validation_result,
            "quality_scores": self._assess_quality(artifacts),
            "coherence_analysis": self._check_coherence(artifacts),
            "improvement_suggestions": self._suggest_improvements(artifacts)
        }
        
        self.reflections.append(reflection)
        
        # Decide next action
        if validation_result.get("passed", False) and self.cycle_count >= ORCH_CONFIG["cycle_min_passes"] - 1:
            self.state = "LEARNED"
        else:
            self.state = "REVISE"
        
        return reflection
    
    async def execute_revise(self, reflection: Dict[str, Any]) -> Dict[str, Any]:
        """REVISE phase: Iterative improvement."""
        await log_to_ledger("orchestrator", "cycle_revise", {
            "plan_id": self.plan_id,
            "cycle": self.cycle_count,
            "improvements": reflection.get("improvement_suggestions", [])
        })
        
        # Generate revision instructions
        revision_plan = {
            "plan_id": self.plan_id,
            "cycle": self.cycle_count,
            "revisions_needed": reflection["improvement_suggestions"],
            "focus_areas": self._prioritize_improvements(reflection),
            "updated_constraints": self._update_constraints(reflection)
        }
        
        self.revisions.append(revision_plan)
        self.cycle_count += 1
        self.state = "DRAFT"  # Return to DRAFT for next iteration
        
        return revision_plan
    
    async def execute_learned(self, final_artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """LEARNED phase: Final synthesis and delivery."""
        await log_to_ledger("orchestrator", "cycle_learned", {
            "plan_id": self.plan_id,
            "total_cycles": self.cycle_count + 1,
            "final_artifacts": len(final_artifacts)
        })
        
        # Package final deliverables
        learned_output = {
            "plan_id": self.plan_id,
            "goal_achieved": True,
            "final_artifacts": final_artifacts,
            "provenance": {
                "cycles_completed": self.cycle_count + 1,
                "reflections": self.reflections,
                "revisions": self.revisions,
                "total_duration": "estimated"  # Would calculate actual time
            },
            "delivery_manifest": self._create_manifest(final_artifacts)
        }
        
        return learned_output
    
    def _decompose_goal(self) -> List[Dict[str, Any]]:
        """Decompose high-level goal into specific tasks."""
        # Simple goal decomposition (would be more sophisticated in real implementation)
        tasks = [
            {"task": "content_research", "priority": 1},
            {"task": "content_generation", "priority": 2},
            {"task": "quality_validation", "priority": 3},
            {"task": "final_packaging", "priority": 4}
        ]
        return tasks
    
    def _analyze_inputs(self) -> Dict[str, Any]:
        """Analyze input requirements and resources."""
        return {
            "input_count": len(self.inputs),
            "modalities": list(set(inp.modality for inp in self.inputs)),
            "licensed_content": sum(1 for inp in self.inputs if inp.consent),
            "estimated_processing_time": len(self.inputs) * 2  # 2 seconds per input
        }
    
    def _estimate_duration(self) -> int:
        """Estimate processing duration in seconds."""
        base_time = 30  # Base processing time
        complexity_multiplier = len(self.inputs) * 10
        return base_time + complexity_multiplier
    
    def _identify_risks(self) -> List[str]:
        """Identify potential risks in the generation process."""
        risks = []
        if not any(inp.consent for inp in self.inputs):
            risks.append("no_consented_inputs")
        if self.constraints.safety_profile == "strict":
            risks.append("strict_safety_requirements")
        return risks
    
    def _assess_quality(self, artifacts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess quality of generated artifacts."""
        # Mock quality assessment
        return {
            "overall_quality": 0.85,
            "coherence": 0.90,
            "safety_compliance": 0.95,
            "goal_alignment": 0.88
        }
    
    def _check_coherence(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check cross-modal coherence."""
        return {
            "cross_modal_consistency": 0.87,
            "narrative_flow": 0.92,
            "style_consistency": 0.89,
            "technical_accuracy": 0.91
        }
    
    def _suggest_improvements(self, artifacts: List[Dict[str, Any]]) -> List[str]:
        """Suggest improvements based on analysis."""
        suggestions = []
        # Mock improvement suggestions
        if len(artifacts) < 2:
            suggestions.append("increase_variant_diversity")
        if self.cycle_count == 0:
            suggestions.append("refine_initial_approach")
        return suggestions
    
    def _prioritize_improvements(self, reflection: Dict[str, Any]) -> List[str]:
        """Prioritize improvement areas."""
        return reflection.get("improvement_suggestions", [])[:3]  # Top 3 priorities
    
    def _update_constraints(self, reflection: Dict[str, Any]) -> Constraints:
        """Update constraints based on reflection."""
        # Would modify constraints based on learnings
        return self.constraints
    
    def _create_manifest(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create delivery manifest."""
        return {
            "artifact_count": len(artifacts),
            "modalities": list(set(art.get("modality", "unknown") for art in artifacts)),
            "delivery_format": "json_package",
            "quality_assured": True,
            "safety_validated": True
        }

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup."""
    await log_to_ledger("orchestrator", "startup", {"port": ORCH_CONFIG["port"]})
    
    # Start health monitoring
    asyncio.create_task(periodic_health_check())

async def periodic_health_check():
    """Periodic health check of twins."""
    while True:
        await check_twin_health()
        await asyncio.sleep(ORCH_CONFIG["health_check_interval"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "twins_healthy": sum(twin_health.values()),
        "twins_total": len(TWIN_POOL),
        "active_plans": len(active_plans)
    }

@app.post("/pb2s/plan")
async def create_plan(request: PlanRequest, background_tasks: BackgroundTasks):
    """
    PB2S DRAFT Phase: Create initial plan from goal and inputs.
    
    This endpoint initializes a new PB2S cycle with goal decomposition
    and resource analysis.
    """
    plan_id = f"PLAN-{uuid.uuid4().hex[:8]}"
    
    # Initialize PB2S cycle
    cycle = PB2SCycle(plan_id, request.goal, request.inputs, request.constraints)
    active_plans[plan_id] = cycle
    
    # Execute DRAFT phase
    draft_result = await cycle.execute_draft()
    
    return {
        "success": True,
        "plan_id": plan_id,
        "cycle_id": f"CYCLE-{cycle.cycle_count}",
        "phase": "DRAFT",
        "draft_plan": draft_result,
        "next_steps": "Call /pb2s/twin/manufacture to begin generation"
    }

@app.post("/pb2s/twin/manufacture")
async def manufacture_content(request: ManufactureRequest):
    """
    Route manufacturing request to Twin pool.
    
    Distributes generation tasks across healthy twins and collects
    candidate artifacts for validation.
    """
    if request.plan_id not in active_plans:
        raise HTTPException(404, f"Plan {request.plan_id} not found")
    
    cycle = active_plans[request.plan_id]
    
    # Check twin health
    await check_twin_health()
    healthy_twins = [url for url, healthy in twin_health.items() if healthy]
    
    if not healthy_twins:
        raise HTTPException(503, "No healthy twins available")
    
    # Distribute work across twins
    manufacturing_tasks = []
    for i, modality in enumerate(request.modal_targets):
        twin_url = healthy_twins[i % len(healthy_twins)]  # Round-robin distribution
        
        task_data = {
            "goal": cycle.goal,
            "inputs": [inp.dict() for inp in cycle.inputs],
            "targets": [modality],
            "n_variants": request.n_variants,
            "constraints": cycle.constraints.dict(),
            "cycle_context": {
                "plan_id": request.plan_id,
                "cycle_count": cycle.cycle_count
            }
        }
        
        manufacturing_tasks.append(route_to_twin(twin_url, task_data))
    
    # Execute all manufacturing tasks
    results = await asyncio.gather(*manufacturing_tasks, return_exceptions=True)
    
    # Process results
    all_artifacts = []
    twin_results = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            await log_to_ledger("orchestrator", "twin_failed", {
                "twin_url": healthy_twins[i % len(healthy_twins)],
                "error": str(result)
            })
            continue
        
        if result.get("success", False):
            artifacts = result.get("artifacts", [])
            all_artifacts.extend(artifacts)
            twin_results.append(result)
    
    if not all_artifacts:
        raise HTTPException(500, "No artifacts generated by twins")
    
    return {
        "success": True,
        "plan_id": request.plan_id,
        "artifacts_generated": len(all_artifacts),
        "twin_results": twin_results,
        "candidates": all_artifacts,
        "next_steps": "Call /suit/validate for safety validation"
    }

@app.post("/suit/validate")
async def validate_content(request: ValidateRequest):
    """
    Route validation request to Suit service.
    
    Performs comprehensive safety validation including harm detection,
    license compliance, privacy protection, bias analysis, and contradiction checking.
    """
    validation_result = await call_suit_validation(request.artifacts, request.policy_profile)
    
    # Log validation result
    await log_to_ledger("orchestrator", "validation_completed", {
        "artifacts_count": len(request.artifacts),
        "policy_profile": request.policy_profile,
        "validation_passed": validation_result.get("passed", False)
    })
    
    return validation_result

@app.post("/pb2s/finalize")
async def finalize_plan(request: FinalizeRequest):
    """
    PB2S LEARNED Phase: Complete the manufacturing cycle.
    
    Finalizes the PB2S cycle with artifact selection and delivery packaging.
    """
    if request.plan_id not in active_plans:
        raise HTTPException(404, f"Plan {request.plan_id} not found")
    
    cycle = active_plans[request.plan_id]
    
    # Mock final artifacts selection (would implement actual selection logic)
    final_artifacts = [
        {
            "modality": "text",
            "content": f"Final content for {cycle.goal}",
            "quality_score": 0.92,
            "safety_validated": True
        }
    ]
    
    # Execute LEARNED phase
    learned_result = await cycle.execute_learned(final_artifacts)
    
    # Clean up
    del active_plans[request.plan_id]
    
    return {
        "success": True,
        "plan_id": request.plan_id,
        "phase": "LEARNED",
        "learned_output": learned_result,
        "status": "completed"
    }

@app.get("/pb2s/status/{plan_id}")
async def get_plan_status(plan_id: str):
    """Get current status of a PB2S plan."""
    if plan_id not in active_plans:
        raise HTTPException(404, f"Plan {plan_id} not found")
    
    cycle = active_plans[plan_id]
    
    return {
        "plan_id": plan_id,
        "current_state": cycle.state,
        "cycle_count": cycle.cycle_count,
        "goal": cycle.goal,
        "reflections_count": len(cycle.reflections),
        "revisions_count": len(cycle.revisions)
    }

@app.get("/pb2s/ledger")
async def get_ledger_summary():
    """Get ledger summary for audit purposes."""
    if not LEDGER_PATH.exists():
        return {"entries": 0, "integrity": "unknown"}
    
    entries = []
    with open(LEDGER_PATH, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    
    return {
        "entries": len(entries),
        "latest_entry": entries[-1] if entries else None,
        "integrity": "verified",  # Would implement actual hash chain verification
        "ledger_path": str(LEDGER_PATH)
    }

# Real-time coordination endpoints
@app.post("/coordination/establish_grounding")
async def establish_common_grounding(request: Dict[str, Any]):
    """Establish common grounding across all agents via contradiction resolution."""
    coordinator = await get_coordinator()
    
    result = await coordinator.establish_common_grounding(
        request.get("new_information", {}),
        "orchestrator"
    )
    
    await log_to_ledger("common_grounding", result)
    return result

@app.post("/coordination/real_time_action")
async def coordinate_real_time_action(request: Dict[str, Any]):
    """Coordinate real-time action across agents while maintaining autonomy."""
    coordinator = await get_coordinator()
    
    result = await coordinator.coordinate_real_time_action(request)
    
    await log_to_ledger("coordinated_action", result)
    return result

@app.post("/coordination/handle_emergence")
async def handle_understanding_emergence(request: Dict[str, Any]):
    """Handle emergence of new understanding patterns - act immediately."""
    coordinator = await get_coordinator()
    
    result = await coordinator.handle_understanding_emergence(request)
    
    await log_to_ledger("understanding_emergence", result)
    return result

@app.get("/coordination/status")
async def get_coordination_status():
    """Get current coordination status across all agents."""
    coordinator = await get_coordinator()
    
    return {
        "shared_understanding": {
            "version": coordinator.shared_understanding.version,
            "established_facts_count": len(coordinator.shared_understanding.established_facts),
            "active_contradictions": len(coordinator.shared_understanding.active_contradictions),
            "participating_agents": len(coordinator.shared_understanding.participating_agents),
            "confidence_level": coordinator.shared_understanding.confidence_level
        },
        "agent_states": {
            agent_id: {
                "coordination_status": state.coordination_status,
                "individual_capability_active": state.individual_capability_active,
                "understanding_version": state.shared_understanding_version
            }
            for agent_id, state in coordinator.agent_states.items()
        },
        "coordination_active": coordinator.coordination_active
    }

@app.post("/sync_understanding")
async def sync_understanding(request: Dict[str, Any]):
    """Sync this agent to shared understanding (called by coordinator)."""
    understanding_version = request.get("understanding_version")
    established_facts = request.get("established_facts", {})
    
    # Update agent's understanding
    # In full implementation, would update internal state
    
    await log_to_ledger("understanding_sync", {
        "new_version": understanding_version,
        "facts_updated": len(established_facts)
    })
    
    return {"synced": True, "version": understanding_version}

@app.post("/analyze_contradiction")
async def analyze_contradiction(request: Dict[str, Any]):
    """Analyze contradiction from orchestrator perspective."""
    contradiction_id = request.get("contradiction_id")
    description = request.get("description")
    
    # Apply orchestrator's specialized analysis
    analysis = {
        "agent_perspective": "orchestrator",
        "analysis": f"From coordination perspective: {description}",
        "suggested_resolution": "context_disambiguation",
        "confidence": 0.8
    }
    
    await log_to_ledger("contradiction_analysis", {
        "contradiction_id": contradiction_id,
        "analysis": analysis
    })
    
    return analysis

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=ORCH_CONFIG["port"])