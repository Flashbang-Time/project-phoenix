# web.py - Project Phoenix Enhanced QEMU Control Server

import os
import subprocess
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
import queue
import re
import sys

# Get the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask app, telling it where to find static files
# We're explicitly telling it the static folder is 'static' relative to this script's location
app = Flask(__name__, static_folder=os.path.join(basedir, 'static'))
CORS(app) # Enable CORS for all routes

# --- QEMU CONFIGURATION DEFAULTS ---
# NOTE: Adjust paths below to match your Termux setup if different
DEFAULT_PRIMARY_DISK_PATH = ""
DEFAULT_CDROM_PATH = "" # Leave empty if no default ISO
DEFAULT_DATA_DISK_PATH = "" # Leave empty if no default data disk

DEFAULT_RAM_MB = 8192 # 8GB
DEFAULT_CORES = 6
DEFAULT_CPU_MODEL = "max" # Use 'max' or 'host' for best performance if supported
DEFAULT_BOOT_ORDER = "c" # c=harddisk, d=cdrom, n=network
DEFAULT_VGA_MODEL = "virtio" # For better performance, often needs VirtIO drivers in guest
DEFAULT_NET_DEVICE = "virtio-net-pci" # For better performance, often needs VirtIO drivers in guest
# For USB passthrough, you usually need a specific USB bus device ID and product ID.
# Example: -device usb-host,vendorid=0xVENDORID,productid=0xPRODUCTID
# This is highly dependent on your device's kernel and permissions.
DEFAULT_USB_DEVICES = [] # List of tuples: [(vendor_id, product_id), ...]

# Base QEMU command template - will be dynamically filled
# Removed -vnc 0.0.0.0:0 as we are explicitly using an external VNC client at 5900
BASE_QEMU_COMMAND_TEMPLATE = (
    "/data/data/com.termux/files/usr/bin/qemu-system-x86_64 "
    "-smp {cores} -m {ram_mb} "
    "-cpu {cpu_model} "
    "-boot order={boot_order} "
    "-vga {vga_model} "
    "-netdev user,id=net0 "
    "-device {net_device},netdev=net0 "
    # Disk and CD-ROM drives will be appended dynamically
)
# --- END QEMU CONFIGURATION ---

# Global variables for QEMU process management
QEMU_PROCESS = None
QEMU_RUNNING_STATUS = False
QEMU_OUTPUT_QUEUE = queue.Queue() # For QEMU's stdout/stderr

# Global queue for terminal command output
TERMINAL_OUTPUT_QUEUE = queue.Queue()

# --- Helper function to read process output in real-time ---
def enqueue_output(out, output_queue):
    """Reads output from a stream line by line and puts it into a given queue."""
    for line in iter(out.readline, ''):
        output_queue.put(line)
    out.close()

# --- QEMU Process Functions ---
def run_qemu_in_thread(command_str):
    """Starts the QEMU process in a separate thread."""
    global QEMU_PROCESS, QEMU_RUNNING_STATUS
    print(f"DEBUG(QEMU_THREAD): Attempting to start QEMU with command: {command_str}")
    command_args = command_str.split() # Splits command string into a list of arguments

    try:
        QEMU_PROCESS = subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, # Decode output as text
            bufsize=1  # Line-buffered output
        )
        QEMU_RUNNING_STATUS = True
        print(f"DEBUG(QEMU_THREAD): QEMU process started with PID: {QEMU_PROCESS.pid}")

        # Start threads to read stdout and stderr from QEMU
        stdout_reader = threading.Thread(target=enqueue_output, args=(QEMU_PROCESS.stdout, QEMU_OUTPUT_QUEUE))
        stderr_reader = threading.Thread(target=enqueue_output, args=(QEMU_PROCESS.stderr, QEMU_OUTPUT_QUEUE))

        stdout_reader.daemon = True # Allow main program to exit even if these threads are running
        stderr_reader.daemon = True

        stdout_reader.start()
        stderr_reader.start()

        QEMU_PROCESS.wait() # Wait for QEMU process to terminate
    except FileNotFoundError:
        error_msg = f"ERROR(QEMU_THREAD): QEMU executable not found at '{command_args[0]}'. Ensure QEMU is installed and path is correct."
        print(error_msg, file=sys.stderr)
        QEMU_OUTPUT_QUEUE.put(error_msg) # Put error into QEMU log queue
    except Exception as e:
        error_msg = f"ERROR(QEMU_THREAD): An unexpected error occurred while trying to run QEMU: {e}"
        print(error_msg, file=sys.stderr)
        QEMU_OUTPUT_QUEUE.put(error_msg) # Put error into QEMU log queue
    finally:
        QEMU_RUNNING_STATUS = False
        QEMU_PROCESS = None
        print("DEBUG(QEMU_THREAD): QEMU process has terminated.")

# --- Terminal Command Execution ---
def run_terminal_command_in_thread(command_string):
    """Executes a given shell command and puts its output into the terminal output queue."""
    TERMINAL_OUTPUT_QUEUE.put(f"$ {command_string}\n") # Echo command to terminal
    print(f"DEBUG(TERMINAL_THREAD): Executing command: {command_string}")
    try:
        process = subprocess.Popen(
            command_string,
            shell=True, # Use shell=True to allow piping, redirection, etc.
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stdout and stderr
            text=True,
            bufsize=1 # Line-buffered output
        )
        for line in iter(process.stdout.readline, ''):
            TERMINAL_OUTPUT_QUEUE.put(line)
        process.wait()
        TERMINAL_OUTPUT_QUEUE.put(f"[Command finished with exit code {process.returncode}]\n")
        print(f"DEBUG(TERMINAL_THREAD): Command finished with exit code {process.returncode}")
    except Exception as e:
        error_msg = f"ERROR(TERMINAL_THREAD): Failed to execute command: {e}\n"
        TERMINAL_OUTPUT_QUEUE.put(error_msg)
        print(f"ERROR(TERMINAL_THREAD): {error_msg}", file=sys.stderr)

# --- Flask Routes ---

# Route to serve static files (like CSS, JS if needed)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def index():
    """Serves the main HTML page for the control panel."""
    try:
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

    data = request.get_json()

    # --- Extract and Validate Parameters ---
    try:
        ram_mb = int(data.get('ram_mb', DEFAULT_RAM_MB))
        cores = int(data.get('cores', DEFAULT_CORES))
        cpu_model = str(data.get('cpu_model', DEFAULT_CPU_MODEL))
        boot_order = str(data.get('boot_order', DEFAULT_BOOT_ORDER))
        vga_model = str(data.get('vga_model', DEFAULT_VGA_MODEL))
        net_device = str(data.get('net_device', DEFAULT_NET_DEVICE))
        
        primary_disk_path = str(data.get('primary_disk_path', DEFAULT_PRIMARY_DISK_PATH)).strip()
        cdrom_path = str(data.get('cdrom_path', DEFAULT_CDROM_PATH)).strip()
        data_disk_path = str(data.get('data_disk_path', DEFAULT_DATA_DISK_PATH)).strip()

    except (ValueError, TypeError) as e:
        error_msg = f"Invalid input for VM parameters: {e}. Please provide valid values."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400

    # Basic input validation
    if not (512 <= ram_mb <= 32768):
        error_msg = "RAM must be between 512 MB and 32768 MB."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if not (1 <= cores <= 12):
        error_msg = "Cores must be between 1 and 12."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', cpu_model):
        error_msg = "Invalid CPU model. Only alphanumeric, hyphens, and underscores allowed."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if boot_order not in ['c', 'd', 'n', 'cd', 'dc', 'ncd', 'dnc']: # Expand as needed
        error_msg = "Invalid boot order. Use 'c' for disk, 'd' for CD-ROM, 'n' for network."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if vga_model not in ['std', 'qxl', 'virtio', 'vmware', 'cirrus']:
        error_msg = "Invalid VGA model."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if net_device not in ['virtio-net-pci', 'e1000', 'rtl8139']:
        error_msg = "Invalid Network device model."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400

    if not primary_disk_path:
        error_msg = "Primary Disk Path cannot be empty."
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if not os.path.exists(primary_disk_path):
        error_msg = f"Primary Disk image not found at: {primary_disk_path}"
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if cdrom_path and not os.path.exists(cdrom_path):
        error_msg = f"CD-ROM ISO image not found at: {cdrom_path}"
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400
    if data_disk_path and not os.path.exists(data_disk_path):
        error_msg = f"Data Disk image not found at: {data_disk_path}"
        print(f"ERROR(API): {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 400

    # --- Construct the QEMU Command ---
    qemu_command_parts = [
        BASE_QEMU_COMMAND_TEMPLATE.format(
            ram_mb=ram_mb,
            cores=cores,
            cpu_model=cpu_model,
            boot_order=boot_order,
            vga_model=vga_model,
            net_device=net_device
        )
    ]

    # Add primary disk
    qemu_command_parts.append(
        f"-drive file={primary_disk_path},if=virtio,cache=writeback,aio=threads,format=qcow2"
    )
    # Add CD-ROM if specified
    if cdrom_path:
        qemu_command_parts.append(
            f"-cdrom={cdrom_path}" # Use ide for CD-ROM usually
        )
    # Add secondary data disk if specified
    if data_disk_path:
        qemu_command_parts.append(
            f"-drive media={data_disk_path},if=virtio,cache=writeback,aio=threads,format=qcow2"
        )
    # Add USB passthrough devices (if configured)
    # This assumes DEFAULT_USB_DEVICES is a list of (vendor_id, product_id)
    # Example: DEFAULT_USB_DEVICES = [("0x1234", "0xABCD")]
    for vendor_id, product_id in DEFAULT_USB_DEVICES:
        qemu_command_parts.append(f"-device usb-host,vendorid={vendor_id},productid={product_id}")


    dynamic_qemu_command = " ".join(qemu_command_parts)

    print(f"DEBUG(API): Received request to START VM with config: RAM={ram_mb}MB, Cores={cores}, CPU={cpu_model}, Primary Disk={primary_disk_path}, CD-ROM={cdrom_path}, Data Disk={data_disk_path}, Boot Order={boot_order}, VGA={vga_model}, Net={net_device}")
    print(f"DEBUG(API): Full QEMU command: {dynamic_qemu_command}")

    # Clear any previous QEMU logs before starting a new session
    while not QEMU_OUTPUT_QUEUE.empty(): QEMU_OUTPUT_QUEUE.get_nowait()

    # Start QEMU in a separate thread to keep the Flask app responsive
    threading.Thread(target=run_qemu_in_thread, args=(dynamic_qemu_command,)).start()

    time.sleep(3) # Give QEMU a moment to attempt starting

    # Check QEMU_RUNNING_STATUS to see if it successfully started
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
    # Add a note about the Termux console if no logs are captured here
    if not logs:
        logs.append("No recent QEMU logs captured here. Check Termux console where 'web.py' is running for direct QEMU output.")
    return jsonify({"logs": logs}), 200

@app.route('/get_defaults', methods=['GET'])
def get_defaults():
    """Provides the default VM configuration parameters to the frontend."""
    return jsonify({
        "default_primary_disk_path": DEFAULT_PRIMARY_DISK_PATH,
        "default_cdrom_path": DEFAULT_CDROM_PATH,
        "default_data_disk_path": DEFAULT_DATA_DISK_PATH,
        "default_ram_mb": DEFAULT_RAM_MB,
        "default_cores": DEFAULT_CORES,
        "default_cpu_model": DEFAULT_CPU_MODEL,
        "default_boot_order": DEFAULT_BOOT_ORDER,
        "default_vga_model": DEFAULT_VGA_MODEL,
        "default_net_device": DEFAULT_NET_DEVICE,
    })

@app.route('/run_terminal_command', methods=['POST'])
def run_terminal_command():
    """Executes a shell command received from the frontend terminal."""
    data = request.get_json()
    command = data.get('command')
    if not command:
        return jsonify({"status": "error", "message": "No command provided."}), 400

    # !!! SECURITY WARNING !!!
    # Running shell=True with user-provided input is extremely dangerous.
    # For a real-world application, you MUST sanitize input string extremely
    # carefully or use a whitelist of allowed commands.
    # This implementation is for demonstration purposes in a controlled environment.
    print(f"DEBUG(API): Received terminal command: {command}")
    threading.Thread(target=run_terminal_command_in_thread, args=(command,)).start()
    return jsonify({"status": "processing", "message": "Command sent to terminal."}), 202

@app.route('/get_terminal_output', methods=['GET'])
def get_terminal_output():
    """Retrieves recent output from the terminal command execution."""
    output_lines = []
    while True:
        try:
            output_lines.append(QEMU_OUTPUT_QUEUE.get_nowait()) # Re-using QEMU queue for simplicity
            # No, actually, use the correct queue for terminal output
            # If terminal output is not distinct from QEMU output, we need a separate queue.
            # Let's ensure TERMINAL_OUTPUT_QUEUE is used here.
            # FIX: Changed this to TERMINAL_OUTPUT_QUEUE
            # Also, send objects with type for proper logging in frontend
            line_content = TERMINAL_OUTPUT_QUEUE.get_nowait().strip()
            line_type = 'info'
            if line_content.startswith('$ '): line_type = 'command'
            elif line_content.startswith('[Command finished'): line_type = 'status'
            elif line_content.startswith('ERROR') or line_content.startswith('FATAL ERROR'): line_type = 'error'
            output_lines.append({"message": line_content, "type": line_type})
        except queue.Empty:
            break
    return jsonify({"output": output_lines}), 200

# Entry point for the Flask application
if __name__ == '__main__':
    # Initial check for Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required for this script.", file=sys.stderr)
        sys.exit(1)

    print(f"DEBUG(MAIN): Flask application directory: {basedir}")
    print(f"DEBUG(MAIN): Flask static files will be served from: {os.path.join(basedir, 'static')}")
    app.run(host='0.0.0.0', port=5000, debug=True) # Run Flask app
