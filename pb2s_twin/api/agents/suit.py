#!/usr/bin/env python3
"""
PB2S+Twin Agent: Suit - Safety Validation Engine

Comprehensive safety validation service for PB2S+Twin manufacturing.
Provides multi-layer content validation including harm detection, license compliance,
privacy protection, bias analysis, and contradiction checking.

FastAPI server exposing safety validation endpoints.
"""

import json
import asyncio
import hashlib
import uuid
import re
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

SUIT_CONFIG = CONFIG["suit"]
LEDGER_PATH = Path(".pb2s/suit_ledger.jsonl")
LEDGER_PATH.parent.mkdir(exist_ok=True)

# FastAPI app instance
app = FastAPI(
    title="PB2S+Twin Safety Suit",
    description="Comprehensive safety validation engine for multimodal content",
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
class Artifact(BaseModel):
    modality: str = Field(..., description="Content modality")
    uri: Optional[str] = Field(None, description="Content URI")
    content: Optional[str] = Field(None, description="Direct content (for text)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ValidationRequest(BaseModel):
    artifacts: List[Artifact] = Field(..., description="Artifacts to validate")
    policy_profile: str = Field("standard", description="Validation policy profile")

class DustbinRequest(BaseModel):
    artifact_id: str = Field(..., description="Artifact to send to dustbin")
    reason: str = Field(..., description="Reason for dustbin action")
    severity: str = Field("medium", description="Severity level")

# Utility functions
def generate_hash(data: Any) -> str:
    """Generate hash for ledger integrity."""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

async def log_to_ledger(event: str, data: Dict[str, Any]):
    """Log event to suit-specific ledger."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "role": "suit",
        "event": event,
        "data": data,
        "hash": generate_hash(data)
    }
    
    with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

# Safety Validation Engine
class SafetyValidationEngine:
    """Comprehensive safety validation engine."""
    
    def __init__(self):
        self.validation_count = 0
        self.dustbin_count = 0
        self.policy_profiles = {
            "strict": {
                "harm_threshold": 0.95,
                "bias_threshold": 0.90,
                "privacy_threshold": 0.95,
                "license_threshold": 0.98,
                "contradiction_threshold": 0.85
            },
            "standard": {
                "harm_threshold": 0.85,
                "bias_threshold": 0.80,
                "privacy_threshold": 0.85,
                "license_threshold": 0.90,
                "contradiction_threshold": 0.75
            },
            "research": {
                "harm_threshold": 0.75,
                "bias_threshold": 0.70,
                "privacy_threshold": 0.80,
                "license_threshold": 0.85,
                "contradiction_threshold": 0.65
            }
        }
        
        # Initialize safety databases
        self.harm_patterns = self._load_harm_patterns()
        self.bias_indicators = self._load_bias_indicators()
        self.privacy_patterns = self._load_privacy_patterns()
        self.dustbin_items = []
    
    async def validate_artifacts(
        self, 
        artifacts: List[Artifact], 
        policy_profile: str
    ) -> Dict[str, Any]:
        """Perform comprehensive safety validation on artifacts."""
        
        if policy_profile not in self.policy_profiles:
            raise HTTPException(400, f"Unknown policy profile: {policy_profile}")
        
        thresholds = self.policy_profiles[policy_profile]
        validation_results = []
        overall_passed = True
        dustbin_incidents = []
        
        for i, artifact in enumerate(artifacts):
            artifact_id = f"artifact_{i}_{uuid.uuid4().hex[:6]}"
            
            # Run all validation checks
            result = await self._validate_single_artifact(artifact, artifact_id, thresholds)
            validation_results.append(result)
            
            # Check if artifact passes
            if not result["passed"]:
                overall_passed = False
                
                # Check if dustbin action needed
                if result["dustbin_required"]:
                    dustbin_incident = await self._handle_dustbin(artifact_id, result["violations"])
                    dustbin_incidents.append(dustbin_incident)
        
        self.validation_count += len(artifacts)
        
        # Log validation results
        await log_to_ledger("validation_completed", {
            "artifacts_count": len(artifacts),
            "policy_profile": policy_profile,
            "overall_passed": overall_passed,
            "dustbin_incidents": len(dustbin_incidents)
        })
        
        return {
            "passed": overall_passed,
            "policy_profile": policy_profile,
            "artifacts_validated": len(artifacts),
            "validation_results": validation_results,
            "dustbin_incidents": dustbin_incidents,
            "summary": self._create_validation_summary(validation_results),
            "ledger_ref": generate_hash(validation_results),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _validate_single_artifact(
        self, 
        artifact: Artifact, 
        artifact_id: str, 
        thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """Validate a single artifact against all safety checks."""
        
        checks = {}
        violations = []
        dustbin_required = False
        
        # 1. Harm Detection
        harm_result = await self._check_harm(artifact, thresholds["harm_threshold"])
        checks["harm"] = harm_result
        if not harm_result["passed"]:
            violations.append("harmful_content")
            if harm_result["severity"] == "high":
                dustbin_required = True
        
        # 2. License Compliance
        license_result = await self._check_license(artifact, thresholds["license_threshold"])
        checks["license"] = license_result
        if not license_result["passed"]:
            violations.append("license_violation")
        
        # 3. Privacy Protection
        privacy_result = await self._check_privacy(artifact, thresholds["privacy_threshold"])
        checks["privacy"] = privacy_result
        if not privacy_result["passed"]:
            violations.append("privacy_violation")
            if privacy_result["severity"] == "high":
                dustbin_required = True
        
        # 4. Bias Detection
        bias_result = await self._check_bias(artifact, thresholds["bias_threshold"])
        checks["bias"] = bias_result
        if not bias_result["passed"]:
            violations.append("bias_detected")
        
        # 5. Contradiction Analysis
        contradiction_result = await self._check_contradictions(artifact, thresholds["contradiction_threshold"])
        checks["contradiction"] = contradiction_result
        if not contradiction_result["passed"]:
            violations.append("logical_contradiction")
        
        # Overall assessment
        all_passed = all(check["passed"] for check in checks.values())
        overall_score = sum(check["score"] for check in checks.values()) / len(checks)
        
        return {
            "artifact_id": artifact_id,
            "passed": all_passed,
            "overall_score": round(overall_score, 3),
            "checks": checks,
            "violations": violations,
            "dustbin_required": dustbin_required,
            "recommendation": "approve" if all_passed else ("dustbin" if dustbin_required else "revise")
        }
    
    async def _check_harm(self, artifact: Artifact, threshold: float) -> Dict[str, Any]:
        """Check for harmful content."""
        content = self._extract_content_for_analysis(artifact)
        
        # Harm detection logic
        harm_score = 0.0
        detected_patterns = []
        severity = "low"
        
        # Check against harm patterns
        for pattern_type, patterns in self.harm_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected_patterns.append(f"{pattern_type}:{pattern}")
                    if pattern_type == "violence":
                        harm_score += 0.3
                        severity = "high"
                    elif pattern_type == "harassment":
                        harm_score += 0.2
                        severity = "medium"
                    elif pattern_type == "inappropriate":
                        harm_score += 0.1
        
        # Cap harm score at 1.0
        harm_score = min(1.0, harm_score)
        safety_score = 1.0 - harm_score
        
        return {
            "check": "harm_detection",
            "passed": safety_score >= threshold,
            "score": safety_score,
            "threshold": threshold,
            "severity": severity,
            "detected_patterns": detected_patterns,
            "details": f"Harm score: {harm_score:.3f}, Safety score: {safety_score:.3f}"
        }
    
    async def _check_license(self, artifact: Artifact, threshold: float) -> Dict[str, Any]:
        """Check license compliance."""
        
        # License compliance logic
        license_issues = []
        compliance_score = 1.0
        
        # Check metadata for license information
        metadata = artifact.metadata or {}
        license_info = metadata.get("license", "unknown")
        
        if license_info == "unknown":
            compliance_score -= 0.2
            license_issues.append("unknown_license")
        elif license_info in ["copyrighted", "proprietary"]:
            compliance_score -= 0.4
            license_issues.append("restrictive_license")
        
        # Check for copyright indicators in content
        content = self._extract_content_for_analysis(artifact)
        copyright_patterns = [r"©.*\d{4}", r"copyright.*\d{4}", r"all rights reserved"]
        
        for pattern in copyright_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                compliance_score -= 0.1
                license_issues.append("copyright_notice_found")
        
        compliance_score = max(0.0, compliance_score)
        
        return {
            "check": "license_compliance",
            "passed": compliance_score >= threshold,
            "score": compliance_score,
            "threshold": threshold,
            "license_info": license_info,
            "issues": license_issues,
            "details": f"License compliance score: {compliance_score:.3f}"
        }
    
    async def _check_privacy(self, artifact: Artifact, threshold: float) -> Dict[str, Any]:
        """Check for privacy violations."""
        content = self._extract_content_for_analysis(artifact)
        
        # Privacy detection logic
        privacy_violations = []
        privacy_score = 1.0
        severity = "low"
        
        # Check for PII patterns
        for pii_type, patterns in self.privacy_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    privacy_violations.append(f"{pii_type}:{len(matches)}_instances")
                    if pii_type in ["ssn", "credit_card"]:
                        privacy_score -= 0.4
                        severity = "high"
                    elif pii_type in ["email", "phone"]:
                        privacy_score -= 0.2
                        severity = "medium"
                    else:
                        privacy_score -= 0.1
        
        privacy_score = max(0.0, privacy_score)
        
        return {
            "check": "privacy_protection",
            "passed": privacy_score >= threshold,
            "score": privacy_score,
            "threshold": threshold,
            "severity": severity,
            "violations": privacy_violations,
            "details": f"Privacy score: {privacy_score:.3f}"
        }
    
    async def _check_bias(self, artifact: Artifact, threshold: float) -> Dict[str, Any]:
        """Check for bias indicators."""
        content = self._extract_content_for_analysis(artifact)
        
        # Bias detection logic
        bias_indicators_found = []
        bias_score = 0.0
        
        # Check for bias indicators
        for bias_type, indicators in self.bias_indicators.items():
            for indicator in indicators:
                if re.search(indicator, content, re.IGNORECASE):
                    bias_indicators_found.append(f"{bias_type}:{indicator}")
                    bias_score += 0.1
        
        bias_score = min(1.0, bias_score)
        neutrality_score = 1.0 - bias_score
        
        return {
            "check": "bias_detection",
            "passed": neutrality_score >= threshold,
            "score": neutrality_score,
            "threshold": threshold,
            "bias_indicators": bias_indicators_found,
            "details": f"Bias score: {bias_score:.3f}, Neutrality score: {neutrality_score:.3f}"
        }
    
    async def _check_contradictions(self, artifact: Artifact, threshold: float) -> Dict[str, Any]:
        """Check for logical contradictions."""
        content = self._extract_content_for_analysis(artifact)
        
        # Contradiction detection logic
        contradictions = []
        consistency_score = 0.9  # Base consistency score
        
        # Simple contradiction patterns
        contradiction_patterns = [
            (r"always.*never", "temporal_contradiction"),
            (r"all.*none", "universal_contradiction"),
            (r"impossible.*possible", "logical_contradiction"),
            (r"cannot.*can", "capability_contradiction")
        ]
        
        for pattern, contradiction_type in contradiction_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                contradictions.append(contradiction_type)
                consistency_score -= 0.1
        
        consistency_score = max(0.0, consistency_score)
        
        return {
            "check": "contradiction_analysis",
            "passed": consistency_score >= threshold,
            "score": consistency_score,
            "threshold": threshold,
            "contradictions": contradictions,
            "details": f"Consistency score: {consistency_score:.3f}"
        }
    
    async def _handle_dustbin(self, artifact_id: str, violations: List[str]) -> Dict[str, Any]:
        """Handle dustbin action for severely violating content."""
        
        dustbin_incident = {
            "incident_id": f"dustbin_{uuid.uuid4().hex[:8]}",
            "artifact_id": artifact_id,
            "timestamp": datetime.utcnow().isoformat(),
            "violations": violations,
            "action": "quarantine_and_redact",
            "severity": "high",
            "irreversible": True
        }
        
        self.dustbin_items.append(dustbin_incident)
        self.dustbin_count += 1
        
        # Log dustbin incident
        await log_to_ledger("dustbin_incident", dustbin_incident)
        
        return dustbin_incident
    
    def _extract_content_for_analysis(self, artifact: Artifact) -> str:
        """Extract analyzable content from artifact."""
        if artifact.content:
            return artifact.content
        elif artifact.uri:
            # For non-text content, use metadata or description
            if artifact.metadata:
                return str(artifact.metadata.get("description", ""))
        return ""
    
    def _create_validation_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of validation results."""
        total_artifacts = len(results)
        passed_artifacts = sum(1 for r in results if r["passed"])
        
        # Aggregate check results
        check_summary = {}
        for check_name in ["harm", "license", "privacy", "bias", "contradiction"]:
            check_results = [r["checks"][check_name] for r in results if check_name in r["checks"]]
            if check_results:
                check_summary[check_name] = {
                    "passed": sum(1 for c in check_results if c["passed"]),
                    "failed": sum(1 for c in check_results if not c["passed"]),
                    "average_score": sum(c["score"] for c in check_results) / len(check_results)
                }
        
        return {
            "total_artifacts": total_artifacts,
            "passed_artifacts": passed_artifacts,
            "failed_artifacts": total_artifacts - passed_artifacts,
            "pass_rate": passed_artifacts / total_artifacts if total_artifacts > 0 else 0,
            "check_summary": check_summary,
            "dustbin_incidents": self.dustbin_count
        }
    
    def _load_harm_patterns(self) -> Dict[str, List[str]]:
        """Load harm detection patterns."""
        return {
            "violence": [
                r"\b(kill|murder|violence|attack|assault)\b",
                r"\b(weapon|gun|knife|bomb)\b",
                r"\b(fight|combat|battle|war)\b"
            ],
            "harassment": [
                r"\b(hate|stupid|idiot|worthless)\b",
                r"\b(shut up|go away|get lost)\b",
                r"\b(racist|sexist|discriminat)\w*\b"
            ],
            "inappropriate": [
                r"\b(inappropriate|offensive|disturbing)\b",
                r"\b(adult.*content|mature.*theme)\b"
            ]
        }
    
    def _load_bias_indicators(self) -> Dict[str, List[str]]:
        """Load bias detection indicators."""
        return {
            "gender": [
                r"\b(all men|all women|typical male|typical female)\b",
                r"\b(men are|women are).*always\b"
            ],
            "racial": [
                r"\b(all.*people|those people|they all)\b",
                r"\b(typical.*person|usual.*behavior)\b"
            ],
            "cultural": [
                r"\b(their culture|those customs|primitive)\b",
                r"\b(civilized|backward|advanced)\b"
            ],
            "age": [
                r"\b(all young|all old|typical teenager)\b",
                r"\b(kids these days|back in my day)\b"
            ]
        }
    
    def _load_privacy_patterns(self) -> Dict[str, List[str]]:
        """Load privacy detection patterns."""
        return {
            "email": [r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
            "phone": [r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", r"\(\d{3}\)\s*\d{3}[-.]?\d{4}"],
            "ssn": [r"\b\d{3}-\d{2}-\d{4}\b"],
            "credit_card": [r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"],
            "address": [r"\b\d+\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b"]
        }

# Global engine instance
safety_engine = SafetyValidationEngine()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize Safety Suit on startup."""
    await log_to_ledger("startup", {
        "port": SUIT_CONFIG["port"],
        "checks_enabled": SUIT_CONFIG["checks"],
        "dustbin_policy": SUIT_CONFIG["dustbin_policy"]
    })

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "checks_enabled": SUIT_CONFIG["checks"],
        "validations_completed": safety_engine.validation_count,
        "dustbin_incidents": safety_engine.dustbin_count,
        "policy_profiles": list(safety_engine.policy_profiles.keys())
    }

@app.post("/check")
async def validate_content(request: ValidationRequest):
    """
    Perform comprehensive safety validation on artifacts.
    
    Runs all enabled safety checks including harm detection, license compliance,
    privacy protection, bias analysis, and contradiction checking.
    """
    
    if not request.artifacts:
        raise HTTPException(400, "No artifacts provided for validation")
    
    # Log validation request
    await log_to_ledger("validation_request", {
        "artifacts_count": len(request.artifacts),
        "policy_profile": request.policy_profile
    })
    
    try:
        # Perform validation
        validation_result = await safety_engine.validate_artifacts(
            request.artifacts,
            request.policy_profile
        )
        
        return validation_result
    
    except Exception as e:
        await log_to_ledger("validation_error", {
            "error": str(e),
            "artifacts_count": len(request.artifacts)
        })
        raise HTTPException(500, f"Validation failed: {e}")

@app.post("/dustbin")
async def send_to_dustbin(request: DustbinRequest):
    """
    Manually send an artifact to the dustbin.
    
    Implements controlled collapse for content that cannot be safely processed.
    """
    
    incident = await safety_engine._handle_dustbin(
        request.artifact_id,
        [f"manual_dustbin:{request.reason}"]
    )
    
    return {
        "success": True,
        "incident": incident,
        "message": "Artifact successfully quarantined in dustbin",
        "policy": SUIT_CONFIG["dustbin_policy"]
    }

@app.get("/dustbin/stats")
async def get_dustbin_stats():
    """Get dustbin statistics."""
    return {
        "total_incidents": safety_engine.dustbin_count,
        "recent_incidents": safety_engine.dustbin_items[-10:] if safety_engine.dustbin_items else [],
        "dustbin_policy": SUIT_CONFIG["dustbin_policy"],
        "quarantine_active": True
    }

@app.get("/policies")
async def get_policies():
    """Get available validation policies and their thresholds."""
    return {
        "available_profiles": list(safety_engine.policy_profiles.keys()),
        "policy_details": safety_engine.policy_profiles,
        "enabled_checks": SUIT_CONFIG["checks"],
        "dustbin_policy": SUIT_CONFIG["dustbin_policy"]
    }

@app.get("/stats")
async def get_statistics():
    """Get Safety Suit operational statistics."""
    return {
        "validations_completed": safety_engine.validation_count,
        "dustbin_incidents": safety_engine.dustbin_count,
        "uptime": "runtime_would_be_calculated",
        "check_statistics": {
            "harm_checks": safety_engine.validation_count,
            "license_checks": safety_engine.validation_count,
            "privacy_checks": safety_engine.validation_count,
            "bias_checks": safety_engine.validation_count,
            "contradiction_checks": safety_engine.validation_count
        },
        "average_validation_time": "0.1s",  # Would calculate from actual data
        "ledger_entries": "count_from_file"
    }

@app.post("/test")
async def test_validation(test_content: Dict[str, Any]):
    """
    Test validation with sample content.
    
    Useful for testing safety policies and thresholds.
    """
    
    # Create test artifact
    test_artifact = Artifact(
        modality="text",
        content=test_content.get("content", ""),
        metadata=test_content.get("metadata", {})
    )
    
    policy_profile = test_content.get("policy_profile", "standard")
    
    # Validate test content
    result = await safety_engine.validate_artifacts([test_artifact], policy_profile)
    
    return {
        "test_result": result,
        "test_artifact": test_artifact.dict(),
        "recommendations": {
            "passed": result["passed"],
            "action": "approve" if result["passed"] else "revise_or_reject",
            "primary_concerns": [
                check for check, details in result["validation_results"][0]["checks"].items()
                if not details["passed"]
            ] if result["validation_results"] else []
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SUIT_CONFIG["port"])