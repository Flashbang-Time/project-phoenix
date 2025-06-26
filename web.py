# qemu_server_unified.py - Project Phoenix Unified Server (with Setup Tools)

import os
import subprocess
from flask import Flask, render_template_string, request, jsonify, make_response
from flask_cors import CORS
import threading
import time
import queue
import re
import sys

# Get the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask app
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- QEMU CONFIGURATION DEFAULTS ---
DEFAULT_RAM_MB = 8192
DEFAULT_CORES = 6
DEFAULT_CPU_MODEL = "max"

BASE_QEMU_COMMAND = (
    "/data/data/com.termux/files/usr/bin/qemu-system-x86_64 "
    "-smp {cores} -m {ram_mb} "
    "-drive file=/data/data/com.termux/files/home/downloads/os.qcow2,if=ide,cache=writeback,aio=threads "
    "-netdev user,id=net0 -device virtio-net-pci,netdev=net0 "
    "-vga virtio -cpu {cpu_model} "
    "-vnc 0.0.0.0:0"
)
# --- END QEMU CONFIGURATION ---

# Global variables for QEMU process management
QEMU_PROCESS = None
QEMU_RUNNING_STATUS = False
QEMU_OUTPUT_QUEUE = queue.Queue()

# Global variables for setup tool feedback
SETUP_OUTPUT_QUEUE = queue.Queue() # Queue for setup command output

# --- Helper functions for QEMU process ---
def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def run_qemu_in_thread(command_str):
    global QEMU_PROCESS, QEMU_RUNNING_STATUS
    print(f"DEBUG(QEMU_THREAD): Attempting to start QEMU with command: {command_str}")
    command_args = command_str.split()
    try:
        QEMU_PROCESS = subprocess.Popen(
            command_args, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        QEMU_RUNNING_STATUS = True
        print(f"DEBUG(QEMU_THREAD): QEMU process started with PID: {QEMU_PROCESS.pid}")
        stdout_reader = threading.Thread(target=enqueue_output, args=(QEMU_PROCESS.stdout, QEMU_OUTPUT_QUEUE))
        stderr_reader = threading.Thread(target=enqueue_output, args=(QEMU_PROCESS.stderr, QEMU_OUTPUT_QUEUE))
        stdout_reader.daemon = True
        stderr_reader.daemon = True
        stdout_reader.start()
        stderr_reader.start()
        QEMU_PROCESS.wait()
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

# --- Setup Tool Functions ---
def run_setup_command_in_thread(command, success_message, error_message):
    """Executes a setup command in a subprocess and sends output to SETUP_OUTPUT_QUEUE."""
    print(f"DEBUG(SETUP_THREAD): Running command: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stdout and stderr
            text=True,
            bufsize=1 # Line-buffered output
        )
        # Enqueue output line by line
        for line in iter(process.stdout.readline, ''):
            SETUP_OUTPUT_QUEUE.put(line.strip())
            print(f"SETUP_OUTPUT: {line.strip()}") # Also print to server console
        process.wait()
        if process.returncode == 0:
            SETUP_OUTPUT_QUEUE.put(f"SUCCESS: {success_message}")
            print(f"DEBUG(SETUP_THREAD): {success_message}")
        else:
            SETUP_OUTPUT_QUEUE.put(f"ERROR: {error_message} (Exit Code: {process.returncode})")
            print(f"ERROR(SETUP_THREAD): {error_message} (Exit Code: {process.returncode})", file=sys.stderr)
    except Exception as e:
        SETUP_OUTPUT_QUEUE.put(f"FATAL ERROR: Failed to execute command '{command[0]}': {e}")
        print(f"FATAL ERROR(SETUP_THREAD): Failed to execute command '{command[0]}': {e}", file=sys.stderr)

# --- Flask Routes ---

@app.route('/')
def index():
    try:
        with open(os.path.join(basedir, 'index.html'), 'r') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: index.html not found. Make sure it's in the same directory as this script.", 404

@app.route('/create_downloads_dir', methods=['POST'])
def create_downloads_dir():
    """Flask route to create the /downloads/ directory."""
    downloads_path = os.path.join(os.path.expanduser("~"), "downloads")
    
    if os.path.exists(downloads_path):
        return jsonify({"status": "info", "message": f"Directory '{downloads_path}' already exists."}), 200

    threading.Thread(
        target=run_setup_command_in_thread,
        args=(
            ["mkdir", "-p", downloads_path],
            f"Directory '{downloads_path}' created successfully.",
            f"Failed to create directory '{downloads_path}'."
        )
    ).start()
    return jsonify({"status": "processing", "message": f"Attempting to create directory '{downloads_path}'. Check setup logs."}), 202

@app.route('/install_qemu_headless', methods=['POST'])
def install_qemu_headless():
    """Flask route to install qemu-system-x86-64-headless."""
    # Check if QEMU executable exists as a simple proxy for already installed
    qemu_executable_path = "/data/data/com.termux/files/usr/bin/qemu-system-x86_64"
    if os.path.exists(qemu_executable_path) and os.path.islink(qemu_executable_path): # Check if it's a symlink typical of pkg install
         return jsonify({"status": "info", "message": "QEMU headless appears to be already installed."}), 200
    if os.path.exists(qqemu_executable_path) and os.path.isfile(qemu_executable_path) and os.access(qemu_executable_path, os.X_OK):
        return jsonify({"status": "info", "message": "QEMU headless (executable) appears to be already installed."}), 200


    threading.Thread(
        target=run_setup_command_in_thread,
        args=(
            ["pkg", "install", "-y", "qemu-system-x86-64-headless"],
            "QEMU headless package installed successfully.",
            "Failed to install QEMU headless package."
        )
    ).start()
    return jsonify({"status": "processing", "message": "Attempting to install QEMU headless package. Check setup logs."}), 202

@app.route('/get_setup_logs', methods=['GET'])
def get_setup_logs():
    """Retrieves recent output from setup commands."""
    logs = []
    while True:
        try:
            logs.append(SETUP_OUTPUT_QUEUE.get_nowait())
        except queue.Empty:
            break
    return jsonify({"logs": logs}), 200

@app.route('/start_vm', methods=['POST'])
def start_vm():
    global QEMU_PROCESS, QEMU_RUNNING_STATUS

    if QEMU_PROCESS is not None:
        print("DEBUG(API): VM is already running, ignoring start request.")
        return jsonify({"status": "info", "message": "VM is already running."}), 200

    data = request.get_json()
    
    try:
        ram_mb = int(data.get('ram_mb', DEFAULT_RAM_MB))
        cores = int(data.get('cores', DEFAULT_CORES))
        cpu_model = str(data.get('cpu_model', DEFAULT_CPU_MODEL))
    except (ValueError, TypeError):
        error_msg = "Invalid input for RAM or Cores. Please provide valid numbers."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400

    if not (512 <= ram_mb <= 32768):
        error_msg = "RAM must be between 512 MB and 32768 MB."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if not (1 <= cores <= 12):
        error_msg = "Cores must be between 1 and 12."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": "Cores must be between 1 and 12."}), 400
    
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', cpu_model):
        error_msg = "Invalid CPU model. Only alphanumeric, hyphens, and underscores allowed."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400

    dynamic_qemu_command = BASE_QEMU_COMMAND.format(ram_mb=ram_mb, cores=cores, cpu_model=cpu_model)

    print(f"DEBUG(API): Received request to START VM with RAM={ram_mb}MB, Cores={cores}, CPU={cpu_model}")
    while not QEMU_OUTPUT_QUEUE.empty():
        QEMU_OUTPUT_QUEUE.get_nowait()

    threading.Thread(target=run_qemu_in_thread, args=(dynamic_qemu_command,)).start()
    
    time.sleep(3)

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
    global QEMU_PROCESS, QEMU_RUNNING_STATUS
    if QEMU_PROCESS:
        print("DEBUG(API): Received request to STOP VM.")
        try:
            QEMU_PROCESS.kill()
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
    global QEMU_RUNNING_STATUS
    status_text = "running" if QEMU_RUNNING_STATUS else "stopped"
    print(f"DEBUG(API): VM Status Requested - Current Status: {status_text}")
    return jsonify({"running": QEMU_RUNNING_STATUS}), 200

@app.route('/qemu_logs', methods=['GET'])
def qemu_logs():
    logs = []
    while True:
        try:
            logs.append(QEMU_OUTPUT_QUEUE.get_nowait())
        except queue.Empty:
            break
    return jsonify({"logs": logs}), 200

@app.route('/get_defaults', methods=['GET'])
def get_defaults():
    return jsonify({
        "default_ram_mb": DEFAULT_RAM_MB,
        "default_cores": DEFAULT_CORES,
        "default_cpu_model": DEFAULT_CPU_MODEL
    })

if __name__ == '__main__':
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required for this script.", file=sys.stderr)
        sys.exit(1)
    
    print(f"DEBUG(MAIN): Flask application directory: {basedir}")
    app.run(host='0.0.0.0', port=5000, debug=True)
