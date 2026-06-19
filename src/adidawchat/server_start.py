import subprocess
import os
import sys

def launch_background(port="8000"):
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", port]
    
    # Open a file to write logs to
    log_file = open("uvicorn.log", "w")

    if os.name == "nt":  # Windows execution
        # DETACHED_PROCESS flag prevents a command prompt window from popping up
        subprocess.Popen(cmd, stdout=log_file, stderr=log_file, creationflags=subprocess.DETACHED_PROCESS)
    else:  # Linux / macOS execution
        subprocess.Popen(cmd, stdout=log_file, stderr=log_file, start_new_session=True)
        
    print("FastAPI app is now running in the background. Logs are being written to uvicorn.log")

if __name__ == "__main__":
    launch_background()