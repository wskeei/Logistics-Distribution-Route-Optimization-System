import subprocess
import sys
import os
import signal

import time

def kill_port(port):
    """Find and kill process on a specific port."""
    try:
        # Find PID using lsof
        output = subprocess.check_output(["lsof", "-t", "-i", f":{port}"]).strip().decode()
        if output:
            pids = output.split()
            print(f"⚠️  Port {port} is in use by PIDs {', '.join(pids)}. Killing them...")
            for pid in pids:
                 subprocess.run(["kill", "-9", pid])
            print(f"✅ PIDs {', '.join(pids)} killed.")
            time.sleep(1) # Wait for port to retain
    except subprocess.CalledProcessError:
        pass # Port not in use

def kill_celery():
    """Kill running celery workers."""
    try:
        subprocess.run(["pkill", "-f", "celery"], check=False)
        # print("🧹 Cleaned up old Celery processes.")
    except Exception:
        pass

def handle_sigterm(*args):
    """Handle SIGTERM signal to trigger cleanup."""
    raise KeyboardInterrupt()

def run_services():
    # Register signal handler for proper shutdown on docker/IDE stop
    signal.signal(signal.SIGTERM, handle_sigterm)

    # Cleanup before starting
    print("🧹 Cleaning up existing processes...")
    kill_port(8000)
    kill_celery()

    # Determine the directory where this script is located
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure the parent directory is in PYTHONPATH so 'backend' module can be found
    env = os.environ.copy()
    parent_dir = os.path.dirname(backend_dir)
    env["PYTHONPATH"] = parent_dir + os.pathsep + env.get("PYTHONPATH", "")

    # Define commands
    uvicorn_cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--app-dir", "..", "--reload"]
    celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.app.worker", "worker", "--loglevel=info"]
    
    print(f"🚀 Starting Backend Services...")
    print(f"📂 Working Directory: {backend_dir}")
    
    # Check if we are potentially running in the wrong environment
    if "backend" not in os.path.abspath(sys.prefix).lower() and "uv" not in os.path.abspath(sys.prefix).lower():
         print("⚠️  WARNING: It looks like you might not be running in the project's uv environment.")
         print("    Please ensure you ran 'uv sync' and are using 'uv run python run_dev.py'.")

    processes = []
    try:
        # Start Uvicorn
        print("Starting FastAPI (Uvicorn)...")
        uvicorn_process = subprocess.Popen(uvicorn_cmd, cwd=backend_dir, env=env)
        processes.append(uvicorn_process)
        
        # Start Celery
        print("Starting Celery Worker...")
        celery_process = subprocess.Popen(celery_cmd, cwd=backend_dir, env=env)
        processes.append(celery_process)
        
        print("\n✅ Services started! Press Ctrl+C to stop both.\n")
        
        # Wait for processes
        for p in processes:
            p.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    except Exception as e:
        print(f"❌ Error occurred: {e}")
    finally:
        # Terminate processes on exit
        print("🧹 Cleaning up...")
        for p in processes:
            if p.poll() is None: # If still running
                p.terminate()
                try:
                    p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    p.kill()
        
        # Force cleanup ports and celery again to be sure
        kill_port(8000)
        kill_celery()
        print("✅ Services stopped cleanly.")
        sys.exit(0)

if __name__ == "__main__":
    run_services()
