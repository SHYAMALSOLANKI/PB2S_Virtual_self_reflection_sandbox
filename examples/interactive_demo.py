#!/usr/bin/env python3
"""
Interactive Web Demo: PB2S+Twin Multi-Modal AI Platform

Real-time web interface for demonstrating PB2S+Twin capabilities:
- Live content generation with safety validation
- Multi-modal AI integrations (text, image, audio)
- Real-time audit trail monitoring
- Interactive safety dashboard
- API playground with live examples

Launch: python examples/interactive_demo.py
Access: http://localhost:8080
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Web framework
try:
    from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    HAS_WEB = True
except ImportError:
    HAS_WEB = False

# PB2S+Twin components
from pb2s_twin.core.orchestrator import PB2SOrchestrator
from pb2s_twin.twin.sandbox import VirtualTwin
from pb2s_twin.safety.suit_engine import SuitEngine
from pb2s_twin.ledger.audit_trail import SafetyLedger


class InteractiveDemo:
    """Interactive web demo for PB2S+Twin system."""
    
    def __init__(self):
        if not HAS_WEB:
            raise ImportError("FastAPI required: pip install fastapi uvicorn")
        
        self.app = FastAPI(
            title="PB2S+Twin Interactive Demo",
            description="Real-time multi-modal AI with safety validation",
            version="1.0.0"
        )
        
        # CORS for web interface
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize PB2S system
        self.ledger = SafetyLedger("./demo_audit_trail.jsonl")
        self.suit_engine = SuitEngine(mode="interactive")
        self.twin = VirtualTwin(ledger=self.ledger)
        self.orchestrator = PB2SOrchestrator(
            twin=self.twin,
            suit_engine=self.suit_engine,
            ledger=self.ledger
        )
        
        # Active websocket connections
        self.connections = []
        
        # Setup routes
        self.setup_routes()
        
        # Create static files directory
        self.setup_static_files()
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            return self.get_demo_html()
        
        @self.app.get("/api/status")
        async def status():
            """System status endpoint."""
            stats = await self.ledger.get_stats()
            return {
                "system": "PB2S+Twin Interactive Demo",
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "ledger_entries": stats["total_entries"],
                "safety_score": 0.95,
                "active_connections": len(self.connections)
            }
        
        @self.app.post("/api/generate")
        async def generate_content(request: Dict[str, Any]):
            """Generate content with safety validation."""
            
            try:
                prompt = request.get("prompt", "")
                modality = request.get("modality", "text")
                safety_level = request.get("safety_level", "standard")
                
                if not prompt:
                    raise HTTPException(400, "Prompt required")
                
                # Broadcast generation start
                await self.broadcast_update({
                    "type": "generation_started",
                    "prompt": prompt,
                    "modality": modality,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Generate content through PB2S system
                result = await self.generate_with_safety(prompt, modality, safety_level)
                
                # Broadcast completion
                await self.broadcast_update({
                    "type": "generation_completed",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                return result
                
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.broadcast_update({
                    "type": "generation_error",
                    "error": error_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                return error_result
        
        @self.app.get("/api/audit-trail")
        async def get_audit_trail():
            """Get recent audit trail entries."""
            entries = await self.ledger.get_recent_entries(50)
            return {
                "entries": entries,
                "total_count": len(entries),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/api/safety-dashboard")
        async def safety_dashboard():
            """Get safety dashboard data."""
            stats = await self.ledger.get_stats()
            
            return {
                "overall_safety_score": 0.95,
                "total_validations": stats["total_entries"],
                "flags_raised": 12,  # Demo data
                "dustbin_incidents": 2,  # Demo data
                "safety_trends": [
                    {"timestamp": "2024-01-01T10:00:00", "score": 0.94},
                    {"timestamp": "2024-01-01T11:00:00", "score": 0.96},
                    {"timestamp": "2024-01-01T12:00:00", "score": 0.95}
                ],
                "recent_flags": [
                    {
                        "timestamp": "2024-01-01T12:30:00",
                        "type": "content_policy",
                        "severity": "low",
                        "artifact_type": "text",
                        "message": "Minor policy concern flagged for review"
                    }
                ]
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates."""
            await websocket.accept()
            self.connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except:
                pass
            finally:
                if websocket in self.connections:
                    self.connections.remove(websocket)
        
        @self.app.get("/api/examples")
        async def get_examples():
            """Get example prompts and use cases."""
            return {
                "text_generation": [
                    "Explain quantum computing to a 12-year-old",
                    "Write a product description for an eco-friendly water bottle",
                    "Create a safety manual for a chemistry lab"
                ],
                "image_generation": [
                    "A futuristic classroom with holographic displays",
                    "Renewable energy sources in a peaceful landscape",
                    "Children learning science through interactive experiments"
                ],
                "multi_modal": [
                    "Create educational content about climate change with images",
                    "Design a marketing campaign for sustainable products",
                    "Generate a technical manual with diagrams and audio"
                ]
            }
    
    async def generate_with_safety(
        self, 
        prompt: str, 
        modality: str, 
        safety_level: str
    ) -> Dict[str, Any]:
        """Generate content with full safety validation."""
        
        # Phase 1: Draft generation
        await self.broadcast_update({
            "type": "phase_update",
            "phase": "draft",
            "message": "Generating initial content..."
        })
        
        if modality == "text":
            generated_content = await self.generate_text_demo(prompt)
        elif modality == "image":
            generated_content = await self.generate_image_demo(prompt)
        else:
            generated_content = await self.generate_multimodal_demo(prompt)
        
        # Phase 2: Safety validation
        await self.broadcast_update({
            "type": "phase_update",
            "phase": "safety",
            "message": "Running safety validation..."
        })
        
        safety_result = await self.validate_safety(generated_content, safety_level)
        
        # Phase 3: Audit logging
        await self.broadcast_update({
            "type": "phase_update",
            "phase": "audit",
            "message": "Logging to audit trail..."
        })
        
        audit_entry = await self.log_generation(prompt, generated_content, safety_result)
        
        return {
            "success": True,
            "prompt": prompt,
            "modality": modality,
            "content": generated_content,
            "safety": safety_result,
            "audit_id": audit_entry["id"],
            "generation_time": "2.3s",  # Demo timing
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_text_demo(self, prompt: str) -> Dict[str, Any]:
        """Demo text generation."""
        return {
            "type": "text",
            "content": f"""
# Generated Content

Based on your prompt: "{prompt}"

This is demonstration content generated by the PB2S+Twin system. In a real implementation, this would connect to advanced language models like GPT-4 to generate high-quality, contextually relevant content.

## Key Features:
- **Safety Validated**: All content passes through multiple safety checks
- **Audit Trail**: Every generation is logged for transparency
- **Multi-Modal**: Can integrate text, images, and audio
- **Interactive**: Real-time generation with live updates

The actual content would be much more sophisticated and tailored to your specific prompt.
            """.strip(),
            "word_count": 95,
            "safety_score": 0.96,
            "complexity": "intermediate"
        }
    
    async def generate_image_demo(self, prompt: str) -> Dict[str, Any]:
        """Demo image generation."""
        return {
            "type": "image",
            "description": f"AI-generated image based on: '{prompt}'",
            "url": "/static/demo-image.png",
            "metadata": {
                "style": "photorealistic",
                "resolution": "1024x1024",
                "safety_filtered": True,
                "generation_model": "DALL-E-3 (demo)"
            },
            "safety_score": 0.98
        }
    
    async def generate_multimodal_demo(self, prompt: str) -> Dict[str, Any]:
        """Demo multi-modal generation."""
        return {
            "type": "multimodal",
            "components": {
                "text": {
                    "content": f"Multi-modal content for: {prompt}",
                    "word_count": 150
                },
                "image": {
                    "description": f"Accompanying visual for {prompt}",
                    "url": "/static/demo-multimodal.png"
                },
                "metadata": {
                    "coherence_score": 0.94,
                    "cross_modal_safety": 0.97
                }
            },
            "safety_score": 0.95
        }
    
    async def validate_safety(self, content: Dict[str, Any], level: str) -> Dict[str, Any]:
        """Validate content safety."""
        # Simulate safety validation
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return {
            "passed": True,
            "score": 0.96,
            "level": level,
            "checks": [
                {"name": "content_policy", "passed": True, "score": 0.98},
                {"name": "bias_detection", "passed": True, "score": 0.95},
                {"name": "toxicity_filter", "passed": True, "score": 0.99},
                {"name": "privacy_scan", "passed": True, "score": 0.94}
            ],
            "flags": [],
            "recommendations": []
        }
    
    async def log_generation(
        self, 
        prompt: str, 
        content: Dict[str, Any], 
        safety: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log generation to audit trail."""
        
        entry = {
            "id": f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "content_type": content["type"],
            "safety_score": safety["score"],
            "validation_passed": safety["passed"]
        }
        
        # In real implementation, would use actual ledger
        await self.ledger.log_entry("generation", entry)
        
        return entry
    
    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected clients."""
        if not self.connections:
            return
        
        message_str = json.dumps(message)
        dead_connections = []
        
        for connection in self.connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.append(connection)
        
        # Remove dead connections
        for dead in dead_connections:
            self.connections.remove(dead)
    
    def setup_static_files(self):
        """Setup static file serving."""
        static_dir = Path("./static")
        static_dir.mkdir(exist_ok=True)
        
        # Create demo image placeholder
        demo_image_info = """
This is a placeholder for demo images.
In a real implementation, generated images would be served here.
"""
        
        with open(static_dir / "demo-image.png.txt", 'w') as f:
            f.write(demo_image_info)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    def get_demo_html(self) -> str:
        """Generate demo HTML interface."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PB2S+Twin Interactive Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem; }
        .card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h3 { color: #333; margin-bottom: 1rem; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #555; }
        .form-control { width: 100%; padding: 0.75rem; border: 2px solid #e1e5e9; border-radius: 5px; font-size: 1rem; }
        .form-control:focus { outline: none; border-color: #667eea; }
        .btn { background: #667eea; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 5px; font-size: 1rem; cursor: pointer; transition: background 0.3s; }
        .btn:hover { background: #5a67d8; }
        .btn:disabled { background: #a0aec0; cursor: not-allowed; }
        .status { padding: 1rem; border-radius: 5px; margin: 1rem 0; }
        .status.success { background: #f0fff4; border-left: 4px solid #48bb78; }
        .status.error { background: #fed7d7; border-left: 4px solid #f56565; }
        .status.info { background: #ebf8ff; border-left: 4px solid #4299e1; }
        .result { background: #f7fafc; padding: 1rem; border-radius: 5px; margin-top: 1rem; white-space: pre-wrap; }
        .safety-score { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 15px; font-size: 0.875rem; font-weight: 600; }
        .safety-high { background: #c6f6d5; color: #276749; }
        .safety-medium { background: #fef5e7; color: #c05621; }
        .safety-low { background: #fed7d7; color: #c53030; }
        .log-entry { background: white; padding: 1rem; margin: 0.5rem 0; border-radius: 5px; border-left: 3px solid #667eea; }
        .log-timestamp { font-size: 0.875rem; color: #666; }
        .examples { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
        .example-tag { background: #e2e8f0; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.875rem; cursor: pointer; }
        .example-tag:hover { background: #cbd5e0; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
        .metric { text-align: center; padding: 1rem; }
        .metric-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .metric-label { color: #666; margin-top: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 PB2S+Twin Interactive Demo</h1>
            <p>Real-time multi-modal AI with safety validation and audit trails</p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>🚀 Content Generation</h3>
                <form id="generateForm">
                    <div class="form-group">
                        <label for="prompt">Prompt</label>
                        <textarea id="prompt" class="form-control" rows="3" placeholder="Enter your generation prompt..."></textarea>
                        <div class="examples">
                            <span class="example-tag" onclick="setPrompt('Explain renewable energy to children')">Educational Content</span>
                            <span class="example-tag" onclick="setPrompt('Create a product description for an AI tool')">Marketing Copy</span>
                            <span class="example-tag" onclick="setPrompt('Write safety guidelines for lab work')">Safety Manual</span>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="modality">Content Type</label>
                        <select id="modality" class="form-control">
                            <option value="text">Text Only</option>
                            <option value="image">Image Generation</option>
                            <option value="multimodal">Multi-Modal</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="safetyLevel">Safety Level</label>
                        <select id="safetyLevel" class="form-control">
                            <option value="standard">Standard</option>
                            <option value="strict">Strict</option>
                            <option value="research">Research Mode</option>
                        </select>
                    </div>
                    <button type="submit" class="btn" id="generateBtn">Generate Content</button>
                </form>

                <div id="generationStatus"></div>
                <div id="generationResult"></div>
            </div>

            <div class="card">
                <h3>🛡️ Safety Dashboard</h3>
                <div class="dashboard-grid">
                    <div class="metric">
                        <div class="metric-value" id="safetyScore">0.95</div>
                        <div class="metric-label">Safety Score</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="totalValidations">1,247</div>
                        <div class="metric-label">Validations</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="flagsRaised">12</div>
                        <div class="metric-label">Flags Raised</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="dustbinIncidents">2</div>
                        <div class="metric-label">Dustbin</div>
                    </div>
                </div>
                <button class="btn" onclick="refreshDashboard()">Refresh Dashboard</button>
            </div>
        </div>

        <div class="card">
            <h3>📊 Live Audit Trail</h3>
            <div id="auditTrail">
                <div class="log-entry">
                    <div class="log-timestamp">2024-01-01 12:30:45</div>
                    <div>Content generation: "Explain quantum computing" - Safety score: <span class="safety-score safety-high">0.96</span></div>
                </div>
                <div class="log-entry">
                    <div class="log-timestamp">2024-01-01 12:29:12</div>
                    <div>Safety validation passed - Multi-modal content - Safety score: <span class="safety-score safety-high">0.94</span></div>
                </div>
                <div class="log-entry">
                    <div class="log-timestamp">2024-01-01 12:27:33</div>
                    <div>Image generation: "Futuristic classroom" - Safety score: <span class="safety-score safety-high">0.98</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleRealtimeUpdate(data);
        };

        // Handle form submission
        document.getElementById('generateForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const prompt = document.getElementById('prompt').value;
            const modality = document.getElementById('modality').value;
            const safetyLevel = document.getElementById('safetyLevel').value;
            
            if (!prompt.trim()) {
                showStatus('Please enter a prompt', 'error');
                return;
            }
            
            const generateBtn = document.getElementById('generateBtn');
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, modality, safety_level: safetyLevel })
                });
                
                const result = await response.json();
                displayResult(result);
                
            } catch (error) {
                showStatus(`Error: ${error.message}`, 'error');
            } finally {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Content';
            }
        });

        function handleRealtimeUpdate(data) {
            switch(data.type) {
                case 'generation_started':
                    showStatus(`Starting generation: "${data.prompt}"`, 'info');
                    break;
                case 'phase_update':
                    showStatus(`${data.phase.toUpperCase()}: ${data.message}`, 'info');
                    break;
                case 'generation_completed':
                    showStatus('Generation completed successfully!', 'success');
                    break;
                case 'generation_error':
                    showStatus(`Generation failed: ${data.error.error}`, 'error');
                    break;
            }
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('generationStatus');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }

        function displayResult(result) {
            const resultDiv = document.getElementById('generationResult');
            
            if (result.success) {
                const safetyClass = result.safety.score > 0.95 ? 'safety-high' : 
                                 result.safety.score > 0.85 ? 'safety-medium' : 'safety-low';
                
                resultDiv.innerHTML = `
                    <div class="result">
                        <h4>Generated Content</h4>
                        <p><strong>Type:</strong> ${result.modality}</p>
                        <p><strong>Safety Score:</strong> <span class="safety-score ${safetyClass}">${result.safety.score}</span></p>
                        <p><strong>Generation Time:</strong> ${result.generation_time}</p>
                        <p><strong>Audit ID:</strong> ${result.audit_id}</p>
                        <hr>
                        ${formatContent(result.content)}
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `<div class="status error">Generation failed: ${result.error}</div>`;
            }
        }

        function formatContent(content) {
            if (content.type === 'text') {
                return `<pre>${content.content}</pre>`;
            } else if (content.type === 'image') {
                return `
                    <p><strong>Description:</strong> ${content.description}</p>
                    <p><em>Image would be displayed here in real implementation</em></p>
                `;
            } else if (content.type === 'multimodal') {
                return `
                    <p><strong>Multi-modal content generated:</strong></p>
                    <p>• Text: ${content.components.text.word_count} words</p>
                    <p>• Visual: ${content.components.image.description}</p>
                    <p>• Coherence Score: ${content.components.metadata.coherence_score}</p>
                `;
            }
            return '<p>Content generated successfully</p>';
        }

        function setPrompt(text) {
            document.getElementById('prompt').value = text;
        }

        async function refreshDashboard() {
            try {
                const response = await fetch('/api/safety-dashboard');
                const data = await response.json();
                
                document.getElementById('safetyScore').textContent = data.overall_safety_score;
                document.getElementById('totalValidations').textContent = data.total_validations.toLocaleString();
                document.getElementById('flagsRaised').textContent = data.flags_raised;
                document.getElementById('dustbinIncidents').textContent = data.dustbin_incidents;
                
                showStatus('Dashboard refreshed', 'success');
            } catch (error) {
                showStatus('Failed to refresh dashboard', 'error');
            }
        }

        // Load dashboard data on page load
        refreshDashboard();
    </script>
</body>
</html>
        """


def main():
    """Launch the interactive demo server."""
    
    print("🚀 Starting PB2S+Twin Interactive Demo Server")
    print("=" * 50)
    
    if not HAS_WEB:
        print("❌ Missing dependencies!")
        print("Install with: pip install fastapi uvicorn")
        return
    
    # Initialize demo
    demo = InteractiveDemo()
    
    print("✅ PB2S+Twin system initialized")
    print("✅ Web interface configured")
    print("✅ Real-time WebSocket ready")
    print("")
    print("🌐 Starting server...")
    print("   URL: http://localhost:8080")
    print("   API: http://localhost:8080/api/status")
    print("")
    print("📱 Features:")
    print("   • Real-time content generation")
    print("   • Live safety validation")
    print("   • Interactive audit trail")
    print("   • Multi-modal AI demos")
    print("")
    print("Press Ctrl+C to stop the server")
    
    # Launch server
    uvicorn.run(
        demo.app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    main()