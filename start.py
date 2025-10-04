#!/usr/bin/env python3
"""
AI Companion Video Call - Startup Script
Starts both backend and frontend services
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command and return the process"""
    print(f"Running: {command}")
    return subprocess.Popen(command, cwd=cwd, shell=shell)

def check_port(port):
    """Check if a port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def main():
    print("🚀 Starting AI Companion Video Call Platform")
    print("=" * 50)
    
    # Get project root directory
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    
    # Check if directories exist
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return 1
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return 1
    
    processes = []
    
    try:
        # Start Redis (if not running)
        print("\n📦 Checking Redis...")
        if not check_port(6379):
            print("⚠️  Redis not running. Please start Redis manually:")
            print("   brew services start redis  # macOS")
            print("   sudo systemctl start redis  # Linux")
            print("   redis-server               # Direct start")
        else:
            print("✅ Redis is running")
        
        # Start Backend
        print("\n🔧 Starting Backend (FastAPI)...")
        backend_cmd = "python main.py"
        backend_process = run_command(backend_cmd, cwd=backend_dir)
        processes.append(("Backend", backend_process))
        
        # Wait a bit for backend to start
        time.sleep(3)
        
        # Start Frontend
        print("\n🎨 Starting Frontend (Next.js)...")
        frontend_cmd = "npm run dev"
        frontend_process = run_command(frontend_cmd, cwd=frontend_dir)
        processes.append(("Frontend", frontend_process))
        
        print("\n✅ Services started successfully!")
        print("\n📱 Access the application:")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("\n🛑 Press Ctrl+C to stop all services")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if any process died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n❌ {name} process died unexpectedly!")
                    return 1
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Terminate all processes
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
        
        print("✅ All services stopped")
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Cleanup on error
        for name, process in processes:
            process.terminate()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
