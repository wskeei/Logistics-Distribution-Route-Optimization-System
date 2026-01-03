import subprocess
import sys
import os
import signal

def run_services():
    # Determine the directory where this script is located
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure the parent directory is in PYTHONPATH so 'backend' module can be found
    env = os.environ.copy()
    parent_dir = os.path.dirname(backend_dir)
    env["PYTHONPATH"] = parent_dir + os.pathsep + env.get("PYTHONPATH", "")

    # Define commands
    # We are in 'backend/' directory.
    # PYTHONPATH includes '.../Logistics Distribution Route Optimization System' (parent of backend)
    # So we can import 'backend.app.main'.
    uvicorn_cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--app-dir", "..", "--reload"]
    celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.app.worker", "worker", "--loglevel=info"]
    
    print(f"🚀 Starting Backend Services...")
    print(f"📂 Working Directory: {backend_dir}")
    print(f"🐍 Python Executable: {sys.executable}")
    print(f"🔧 Python Prefix: {sys.prefix}")
    
    # Check if we are potentially running in the wrong environment
    if "backend" not in os.path.abspath(sys.prefix).lower() and "uv" not in os.path.abspath(sys.prefix).lower():
         print("⚠️  WARNING: It looks like you might not be running in the project's uv environment.")
         print("    Please ensure you ran 'uv sync' and are using 'uv run python run_dev.py'.")

    # Define commands
    try:
        # Start Uvicorn
        print("Starting FastAPI (Uvicorn)...")
        uvicorn_process = subprocess.Popen(uvicorn_cmd, cwd=backend_dir, env=env)
        
        # Start Celery
        print("Starting Celery Worker...")
        celery_process = subprocess.Popen(celery_cmd, cwd=backend_dir, env=env)
        
        print("\n✅ Services started! Press Ctrl+C to stop both.\n")
        
        # Wait for both processes
        uvicorn_process.wait()
        celery_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        # Terminate processes on Ctrl+C
        if 'uvicorn_process' in locals():
            uvicorn_process.terminate()
        if 'celery_process' in locals():
            celery_process.terminate()
        print("✅ Services stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        if 'uvicorn_process' in locals():
            uvicorn_process.kill()
        if 'celery_process' in locals():
            celery_process.kill()
        sys.exit(1)

if __name__ == "__main__":
    run_services()
