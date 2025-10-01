#!/usr/bin/env python3
"""
Demo launcher script that sets up the Python path correctly.
"""

import sys
import os
import subprocess
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Change to project directory
os.chdir(project_root)

def run_demo(demo_name, *args):
    """Run a specific demo with arguments."""
    demo_script = project_root / "examples" / f"{demo_name}.py"
    
    if not demo_script.exists():
        print(f"❌ Demo script not found: {demo_script}")
        return
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    # Build command
    cmd = [sys.executable, str(demo_script)] + list(args)
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print(f"📁 Working directory: {project_root}")
    print("=" * 50)
    
    # Execute the demo
    try:
        result = subprocess.run(cmd, env=env, cwd=project_root, check=False)
        if result.returncode == 0:
            print("\n✅ Demo completed successfully!")
        else:
            print(f"\n❌ Demo failed with exit code: {result.returncode}")
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")

def main():
    """Main demo launcher."""
    if len(sys.argv) < 2:
        print("🎯 PB2S+Twin Demo Launcher")
        print("=" * 30)
        print("Available demos:")
        print("  demo_showcase     - Complete demo showcase")
        print("  real_world_demo   - Real-world AI content generation")
        print("  climate_education_demo - Climate education lesson generator")
        print("  interactive_demo  - Web-based interactive demo")
        print()
        print("Usage:")
        print("  python run_demo.py demo_showcase")
        print("  python run_demo.py real_world_demo --topic 'climate change'")
        print("  python run_demo.py climate_education_demo --topic 'Solar Energy'")
        print("  python run_demo.py interactive_demo")
        return
    
    demo_name = sys.argv[1]
    demo_args = sys.argv[2:]
    
    run_demo(demo_name, *demo_args)

if __name__ == "__main__":
    main()