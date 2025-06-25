# qemu_server_unified.py - Project Phoenix Unified Server (No VNC Proxy)

import os
import subprocess
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import threading
import time
import queue
import re
import sys # For sys.exit for Python version check

# Get the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask app
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- QEMU CONFIGURATION DEFAULTS ---
DEFAULT_RAM_MB = 8192
DEFAULT_CORES = 6
DEFAULT_CPU_MODEL = "max"

# Base QEMU command template. Parameters will be injected.
# Ensure file paths are ABSOLUTE for your Termux environment.
# Example: /data/data/com.termux/files/home/(path_to_folder)/(os_qcow2_here.qcow2)
BASE_QEMU_COMMAND = (
    "/data/data/com.termux/files/usr/bin/qemu-system-x86_64 "
    "-smp {cores} -m {ram_mb} "
    "-drive file=/data/data/com.termux/files/home/*path-here/*path-here,if=ide,cache=writeback,aio=threads "
    "-netdev user,id=net0 -device virtio-net-pci,netdev=net0 "
    "-vga virtio -cpu {cpu_model} "
    "-vnc 0.0.0.0:0" # QEMU VNC server will listen on 0.0.0.0:5900 (display 0)
)
# --- END QEMU CONFIGURATION ---

# Global variables for QEMU process management
QEMU_PROCESS = None
QEMU_RUNNING_STATUS = False
QEMU_OUTPUT_QUEUE = queue.Queue()

# Helper function to read QEMU output in real-time
def enqueue_output(out, queue):
    """Reads lines from a stream (stdout/stderr) and puts them into a queue."""
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

# Function to run QEMU in a separate thread
def run_qemu_in_thread(command_str):
    """Executes the QEMU command in a subprocess and manages its lifecycle."""
    global QEMU_PROCESS, QEMU_RUNNING_STATUS
    print(f"DEBUG(QEMU_THREAD): Attempting to start QEMU with command: {command_str}")
    
    command_args = command_str.split()

    try:
        # Start QEMU as a subprocess, capturing its output
        QEMU_PROCESS = subprocess.Popen(
            command_args, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True # Ensure output is decoded as text
        )
        QEMU_RUNNING_STATUS = True
        print(f"DEBUG(QEMU_THREAD): QEMU process started with PID: {QEMU_PROCESS.pid}")

        # Start separate threads to read stdout and stderr asynchronously
        stdout_reader = threading.Thread(target=enqueue_output, args=(QEMU_PROCESS.stdout, QEMU_OUTPUT_QUEUE))
        stderr_reader = threading.Thread(target=enqueue_output, args=(QEMU_PROCESS.stderr, QEMU_OUTPUT_QUEUE))
        stdout_reader.daemon = True # Allows thread to exit with main program
        stderr_reader.daemon = True
        stdout_reader.start()
        stderr_reader.start()

        QEMU_PROCESS.wait() # Wait for the QEMU process to terminate

    except FileNotFoundError:
        error_msg = f"ERROR(QEMU_THREAD): QEMU executable not found at '{command_args[0]}'. Ensure QEMU is installed and path is correct."
        print(error_msg, file=sys.stderr)
        QEMU_OUTPUT_QUEUE.put(error_msg)
    except Exception as e:
        error_msg = f"ERROR(QEMU_THREAD): An unexpected error occurred while trying to run QEMU: {e}"
        print(error_msg, file=sys.stderr)
        QEMU_OUTPUT_QUEUE.put(error_msg)
    finally:
        QEMU_RUNNING_STATUS = False
        QEMU_PROCESS = None
        print("DEBUG(QEMU_THREAD): QEMU process has terminated.")

# --- Flask Routes ---

@app.route('/')
def index():
    """Serves the main HTML web interface."""
    try:
        # Load index.html relative to the script's directory
        with open(os.path.join(basedir, 'index.html'), 'r') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: index.html not found. Make sure it's in the same directory as this script.", 404

@app.route('/start_vm', methods=['POST'])
def start_vm():
    """Handles requests to start the QEMU VM with dynamic parameters."""
    global QEMU_PROCESS, QEMU_RUNNING_STATUS

    if QEMU_PROCESS is not None:
        print("DEBUG(API): VM is already running, ignoring start request.")
        return jsonify({"status": "info", "message": "VM is already running."}), 200

    data = request.get_json() # Get JSON data from the frontend
    
    # Extract and validate parameters, using defaults if not provided
    try:
        ram_mb = int(data.get('ram_mb', DEFAULT_RAM_MB))
        cores = int(data.get('cores', DEFAULT_CORES))
        cpu_model = str(data.get('cpu_model', DEFAULT_CPU_MODEL))
    except (ValueError, TypeError):
        error_msg = "Invalid input for RAM or Cores. Please provide valid numbers."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400

    # Sanity checks for input values
    if not (512 <= ram_mb <= 32768): # Sensible RAM limits (512MB to 32GB)
        error_msg = "RAM must be between 512 MB and 32768 MB."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if not (1 <= cores <= 12): # Sensible core limits (1 to 12 cores)
        error_msg = "Cores must be between 1 and 12."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": "Cores must be between 1 and 12."}), 400
    
    # Basic sanitization for CPU model to prevent command injection
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', cpu_model):
        error_msg = "Invalid CPU model. Only alphanumeric, hyphens, and underscores allowed."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400

    # Construct the dynamic QEMU command string
    dynamic_qemu_command = BASE_QEMU_COMMAND.format(ram_mb=ram_mb, cores=cores, cpu_model=cpu_model)

    print(f"DEBUG(API): Received request to START VM with RAM={ram_mb}MB, Cores={cores}, CPU={cpu_model}")
    while not QEMU_OUTPUT_QUEUE.empty(): # Clear any previous QEMU logs
        QEMU_OUTPUT_QUEUE.get_nowait()

    # Start QEMU in a new thread so the Flask server remains responsive
    threading.Thread(target=run_qemu_in_thread, args=(dynamic_qemu_command,)).start()
    
    time.sleep(3) # Give QEMU a moment to attempt starting

    # Check status and return appropriate response to the UI
    if QEMU_RUNNING_STATUS:
        message = "VM started successfully. Connect your VNC client to 127.0.0.1:5900 (display 0)."
        status = "success"
        print(f"DEBUG(API): {message}")
    else:
        message = "VM failed to start or encountered an error. Check Termux console or /qemu_logs for details."
        status = "error"
        print(f"DEBUG(API): {message}")
        
    return jsonify({"status": status, "message": message}), 200

@app.route('/stop_vm', methods=['POST'])
def stop_vm():
    """Handles requests to stop the running QEMU VM."""
    global QEMU_PROCESS, QEMU_RUNNING_STATUS
    if QEMU_PROCESS:
        print("DEBUG(API): Received request to STOP VM.")
        try:
            QEMU_PROCESS.kill() # Forcefully terminate the QEMU process
            QEMU_PROCESS = None
            QEMU_RUNNING_STATUS = False
            print("DEBUG(API): VM stopped successfully.")
            return jsonify({"status": "success", "message": "VM stopped successfully."}), 200
        except Exception as e:
            error_msg = f"ERROR(API): Failed to stop VM: {e}"
            print(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
    else:
        print("DEBUG(API): VM is not running, ignoring stop request.")
        return jsonify({"status": "info", "message": "VM is not running."}), 200

@app.route('/vm_status', methods=['GET'])
def vm_status():
    """Provides the current running status of the VM."""
    global QEMU_RUNNING_STATUS
    status_text = "running" if QEMU_RUNNING_STATUS else "stopped"
    print(f"DEBUG(API): VM Status Requested - Current Status: {status_text}")
    return jsonify({"running": QEMU_RUNNING_STATUS}), 200

@app.route('/qemu_logs', methods=['GET'])
def qemu_logs():
    """Retrieves recent QEMU stdout/stderr output for debugging."""
    logs = []
    # Get all items currently in the queue without blocking
    while True:
        try:
            logs.append(QEMU_OUTPUT_QUEUE.get_nowait())
        except queue.Empty:
            break
    return jsonify({"logs": logs}), 200

@app.route('/get_defaults', methods=['GET'])
def get_defaults():
    """Provides the default VM configuration parameters to the frontend."""
    return jsonify({
        "default_ram_mb": DEFAULT_RAM_MB,
        "default_cores": DEFAULT_CORES,
        "default_cpu_model": DEFAULT_CPU_MODEL
    })

if __name__ == '__main__':
    # Initial check for Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required for this script.", file=sys.stderr)
        sys.exit(1)
    
    print(f"DEBUG(MAIN): Flask application directory: {basedir}")
    app.run(host='0.0.0.0', port=5000, debug=True) # Run Flask app
