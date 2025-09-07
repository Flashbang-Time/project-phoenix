# web.py - Project Phoenix Advanced QEMU Control Server

import os
import subprocess
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
import queue
import re
import sys
import psutil

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, static_folder=os.path.join(basedir, 'static'))
CORS(app)

# --- QEMU CONFIGURATION DEFAULTS ---
DEFAULT_PRIMARY_DISK_PATH = ""
DEFAULT_CDROM_PATH = ""
DEFAULT_DATA_DISK_PATH = ""
DEFAULT_RAM_MB = 8192
DEFAULT_CORES = 6
DEFAULT_CPU_MODEL = "max"
DEFAULT_BOOT_ORDER = "c"
DEFAULT_VGA_MODEL = "virtio"
DEFAULT_NET_DEVICE = "virtio-net-pci"
DEFAULT_USB_DEVICES = []
DEFAULT_WEBSOCK_IP_1 = "127.0.0.1:5901"
DEFAULT_WEBSOCK_IP_2 = "127.0.0.1:5900"


# Prints confirmation 2 times, i don't know, if someone knows
# make an issue on github

BASE_QEMU_COMMAND_TEMPLATE = (
    "qemu-system-x86_64 "
    "-accel tcg,thread=multi,tb-size=1024 "
    "-smp {cores} -m {ram_mb} "
    "-cpu {cpu_model} "
    "-boot order={boot_order} "
    "-vga {vga_model} "
    "-netdev user,id=net0 "
    "-device {net_device},netdev=net0 "
)

print("QEMU_BASE config valid!")

QEMU_DEPENDS = (
    "websockify {websock_ip_1} {websock_ip_2} "
)

print("QEMU_DEPENDS config valid!")

# Spaces for visibility

print("                     ")
#print("                     ")
#print


# --- END QEMU CONFIGURATION ---

# Global variables for QEMU process management
QEMU_PROCESS = None
QEMU_RUNNING_STATUS = False
QEMU_OUTPUT_QUEUE = queue.Queue()
TERMINAL_OUTPUT_QUEUE = queue.Queue()

# --- Helper function to read process output in real-time ---
def enqueue_output(out, output_queue):
    for line in iter(out.readline, ''):
        output_queue.put(line)
    out.close()

# --- QEMU Process Functions ---
def run_qemu_in_thread(command_str):
    global QEMU_PROCESS, QEMU_RUNNING_STATUS
    print(f"DEBUG(QEMU_THREAD): Attempting to start QEMU with command: {command_str}")
    command_args = command_str.split()

    try:
        QEMU_PROCESS = subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
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

# --- Terminal Command Execution ---
def run_terminal_command_in_thread(command_string):
    TERMINAL_OUTPUT_QUEUE.put(f"$ {command_string}\n")
    print(f"DEBUG(TERMINAL_THREAD): Executing command: {command_string}")
    try:
        process = subprocess.Popen(
            command_string,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
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
@app.route('/')
def index():
    try:
        with open(os.path.join(basedir, 'index.html'), 'r') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: index.html not found. Make sure it's in the same directory as this script.", 404

# This single route serves all files and subdirectories from the static/noVNC folder.
# This is the industry-standard way to do it.

@app.route('/noVNC/')
def novnc_index():
    try:
        with open(os.path.join(basedir, 'vnc.html'), 'r') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: vnc.html not found in directory", 404

@app.route('/noVNC/<path:filename>')
def novnc_files(filename):
    return send_from_directory(os.path.join(basedir, ''), filename)

@app.route('/vncgui')
def serve_vncgui():
    try:
        with open(os.path.join(basedir, 'vncgui.html'), 'r') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: vncgui.html not found in directory", 404

@app.route('/terminal')
def serve_terminal():
    try:
        with open(os.path.join(basedir, 'terminal.html'), 'r') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: terminal.html not found in directory"


# --- Fututi icoana si dumnezeul tau mergi fututen gura ---
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
        global QEMU_PROCESS, QEMU_RUNNING_STATUS
        if QEMU_PROCESS:
            try:
                QEMU_PROCESS.kill()
                QEMU_PROCESS = None
                QEMU_RUNNING_STATUS = False
                return jsonify({"status": "success", "message": "VM stopped successfully."}), 200
            except Exception as e:
                return jsonify({"status": "error", "message": f"Failed to stop VM: {e}"}), 500
        else:
            return jsonify({"status": "info", "message": "VM is not running."}), 200



@app.route('/vm_status', methods=['GET'])
def vm_status():
    global QEMU_RUNNING_STATUS
    status_text = "running" if QEMU_RUNNING_STATUS else "stopped"
    return jsonify({"running": QEMU_RUNNING_STATUS}), 200

 
@app.route('/qemu_logs', methods=['GET'])
def qemu_logs():
    logs = []
    while True:
        try:
            logs.append(QEMU_OUTPUT_QUEUE.get_nowait())
        except queue.Empty:
            break
    if not logs:
        logs.append("No recent QEMU logs captured here.")
    return jsonify({"logs": logs}), 200

@app.route('/get_defaults', methods=['GET'])
def get_defaults():
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
    data = request.get_json()
    command = data.get('command')
    if not command:
        return jsonify({"status": "error", "message": "No command provided."}), 400
    
    threading.Thread(target=run_terminal_command_in_thread, args=(command,)).start()
    return jsonify({"status": "processing", "message": "Command sent to terminal."}), 202

@app.route('/get_terminal_output', methods=['GET'])
def get_terminal_output():
    output_lines = []
    while True:
        try:
            line_content = TERMINAL_OUTPUT_QUEUE.get_nowait().strip()
            line_type = 'info'
            if line_content.startswith('$ '): line_type = 'command'
            elif line_content.startswith('[Command finished'): line_type = 'status'
            elif line_content.startswith('ERROR') or line_content.startswith('FATAL ERROR'): line_type = 'error'
            output_lines.append({"message": line_content, "type": line_type})
        except queue.Empty:
            break
    return jsonify({"output": output_lines}), 200



if __name__ == '__main__':
    static_folder_path = os.path.join(basedir, 'static')
    if not os.path.exists(static_folder_path):
        print(f"WARNING: 'static' folder not found at '{static_folder_path}'. Please create it.")

    print(f"DEBUG(MAIN): Flask application directory: {basedir}")
    print(f"DEBUG(MAIN): Flask static files will be served from: {static_folder_path}")
    app.run(host='0.0.0.0', port=5000, debug=True)
