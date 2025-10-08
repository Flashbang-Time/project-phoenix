#!/usr/bin/env python3
"""
Project Phoenix - QEMU VM Control Backend
Flask REST API server for controlling QEMU virtual machines from mobile app
"""

import os
import subprocess
import threading
import time
import queue
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration defaults
DEFAULT_PRIMARY_DISK_PATH = ""
DEFAULT_CDROM_PATH = ""
DEFAULT_DATA_DISK_PATH = ""
DEFAULT_RAM_MB = 8192
DEFAULT_CORES = 6
DEFAULT_CPU_MODEL = "max"
DEFAULT_BOOT_ORDER = "c"
DEFAULT_VGA_MODEL = "virtio"
DEFAULT_NET_DEVICE = "virtio-net-pci"

# Global state
QEMU_PROCESS = None
QEMU_RUNNING = False
QEMU_OUTPUT_QUEUE = queue.Queue()
TERMINAL_OUTPUT_QUEUE = queue.Queue()


def enqueue_output(pipe, output_queue):
    """Read process output line by line and put into queue"""
    try:
        for line in iter(pipe.readline, ''):
            if line:
                output_queue.put(line.strip())
    except Exception as e:
        output_queue.put(f"ERROR: {str(e)}")
    finally:
        pipe.close()


def run_qemu_thread(command):
    """Run QEMU process in background thread"""
    global QEMU_PROCESS, QEMU_RUNNING

    print(f"Starting QEMU: {command}")

    try:
        QEMU_PROCESS = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        QEMU_RUNNING = True
        print(f"QEMU started with PID: {QEMU_PROCESS.pid}")

        # Start output readers
        stdout_thread = threading.Thread(
            target=enqueue_output,
            args=(QEMU_PROCESS.stdout, QEMU_OUTPUT_QUEUE),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=enqueue_output,
            args=(QEMU_PROCESS.stderr, QEMU_OUTPUT_QUEUE),
            daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()

        # Wait for process to complete
        QEMU_PROCESS.wait()

    except FileNotFoundError:
        error_msg = "QEMU executable not found. Please install QEMU."
        print(f"ERROR: {error_msg}")
        QEMU_OUTPUT_QUEUE.put(error_msg)
    except Exception as e:
        error_msg = f"Failed to start QEMU: {str(e)}"
        print(f"ERROR: {error_msg}")
        QEMU_OUTPUT_QUEUE.put(error_msg)
    finally:
        QEMU_RUNNING = False
        QEMU_PROCESS = None
        print("QEMU process terminated")


def run_terminal_command_thread(command):
    """Execute terminal command in background thread"""
    TERMINAL_OUTPUT_QUEUE.put(f"$ {command}")

    print(f"Executing: {command}")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ''):
            if line:
                TERMINAL_OUTPUT_QUEUE.put(line.strip())

        process.wait()
        TERMINAL_OUTPUT_QUEUE.put(f"[Command finished with exit code {process.returncode}]")
        print(f"Command finished: exit code {process.returncode}")

    except Exception as e:
        error_msg = f"ERROR: Command execution failed: {str(e)}"
        TERMINAL_OUTPUT_QUEUE.put(error_msg)
        print(error_msg)


# API Routes

@app.route('/vm_status', methods=['GET'])
def vm_status():
    """Get current VM status"""
    return jsonify({
        "running": QEMU_RUNNING
    }), 200


@app.route('/start_vm', methods=['POST'])
def start_vm():
    """Start QEMU VM with provided configuration"""
    global QEMU_PROCESS, QEMU_RUNNING

    if QEMU_RUNNING:
        return jsonify({
            "status": "info",
            "message": "VM is already running"
        }), 200

    data = request.get_json()

    # Extract parameters
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
        return jsonify({
            "status": "error",
            "message": f"Invalid parameters: {str(e)}"
        }), 400

    # Validate parameters
    if not (512 <= ram_mb <= 32768):
        return jsonify({
            "status": "error",
            "message": "RAM must be between 512 MB and 32768 MB"
        }), 400

    if not (1 <= cores <= 12):
        return jsonify({
            "status": "error",
            "message": "CPU cores must be between 1 and 12"
        }), 400

    if not re.fullmatch(r'[a-zA-Z0-9_-]+', cpu_model):
        return jsonify({
            "status": "error",
            "message": "Invalid CPU model format"
        }), 400

    if boot_order not in ['c', 'd', 'n', 'cd', 'dc', 'ncd', 'dnc']:
        return jsonify({
            "status": "error",
            "message": "Invalid boot order"
        }), 400

    if vga_model not in ['std', 'qxl', 'virtio', 'vmware', 'cirrus']:
        return jsonify({
            "status": "error",
            "message": "Invalid VGA model"
        }), 400

    if net_device not in ['virtio-net-pci', 'e1000', 'rtl8139']:
        return jsonify({
            "status": "error",
            "message": "Invalid network device"
        }), 400

    if not primary_disk_path:
        return jsonify({
            "status": "error",
            "message": "Primary disk path is required"
        }), 400

    if not os.path.exists(primary_disk_path):
        return jsonify({
            "status": "error",
            "message": f"Primary disk not found: {primary_disk_path}"
        }), 400

    if cdrom_path and not os.path.exists(cdrom_path):
        return jsonify({
            "status": "error",
            "message": f"CD-ROM ISO not found: {cdrom_path}"
        }), 400

    if data_disk_path and not os.path.exists(data_disk_path):
        return jsonify({
            "status": "error",
            "message": f"Data disk not found: {data_disk_path}"
        }), 400

    # Build QEMU command
    qemu_cmd = [
        "qemu-system-x86_64",
        "-accel tcg,thread=multi",
        f"-smp {cores}",
        f"-m {ram_mb}",
        f"-cpu {cpu_model}",
        f"-boot order={boot_order}",
        f"-vga {vga_model}",
        "-netdev user,id=net0",
        f"-device {net_device},netdev=net0",
        f"-drive file={primary_disk_path},if=virtio,cache=writeback,format=qcow2",
        "-vnc :0"
    ]

    if cdrom_path:
        qemu_cmd.append(f"-cdrom {cdrom_path}")

    if data_disk_path:
        qemu_cmd.append(f"-drive file={data_disk_path},if=virtio,cache=writeback,format=qcow2")

    command = " ".join(qemu_cmd)

    # Clear previous logs
    while not QEMU_OUTPUT_QUEUE.empty():
        try:
            QEMU_OUTPUT_QUEUE.get_nowait()
        except queue.Empty:
            break

    # Start QEMU in thread
    thread = threading.Thread(target=run_qemu_thread, args=(command,), daemon=True)
    thread.start()

    # Wait a moment to check if it started
    time.sleep(2)

    if QEMU_RUNNING:
        return jsonify({
            "status": "success",
            "message": "VM started successfully"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "VM failed to start. Check logs for details."
        }), 500


@app.route('/stop_vm', methods=['POST'])
def stop_vm():
    """Stop running QEMU VM"""
    global QEMU_PROCESS, QEMU_RUNNING

    if not QEMU_RUNNING or QEMU_PROCESS is None:
        return jsonify({
            "status": "info",
            "message": "VM is not running"
        }), 200

    try:
        print("Stopping QEMU process...")
        QEMU_PROCESS.terminate()

        try:
            QEMU_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("QEMU didn't stop gracefully, killing...")
            QEMU_PROCESS.kill()
            QEMU_PROCESS.wait()

        QEMU_RUNNING = False
        QEMU_PROCESS = None

        return jsonify({
            "status": "success",
            "message": "VM stopped successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to stop VM: {str(e)}"
        }), 500


@app.route('/get_defaults', methods=['GET'])
def get_defaults():
    """Get default configuration values"""
    return jsonify({
        "default_primary_disk_path": DEFAULT_PRIMARY_DISK_PATH,
        "default_cdrom_path": DEFAULT_CDROM_PATH,
        "default_data_disk_path": DEFAULT_DATA_DISK_PATH,
        "default_ram_mb": DEFAULT_RAM_MB,
        "default_cores": DEFAULT_CORES,
        "default_cpu_model": DEFAULT_CPU_MODEL,
        "default_boot_order": DEFAULT_BOOT_ORDER,
        "default_vga_model": DEFAULT_VGA_MODEL,
        "default_net_device": DEFAULT_NET_DEVICE
    }), 200


@app.route('/qemu_logs', methods=['GET'])
def qemu_logs():
    """Get recent QEMU output logs"""
    logs = []

    while not QEMU_OUTPUT_QUEUE.empty():
        try:
            logs.append(QEMU_OUTPUT_QUEUE.get_nowait())
        except queue.Empty:
            break

    if not logs:
        logs = ["No recent logs available"]

    return jsonify({
        "logs": logs
    }), 200


@app.route('/run_terminal_command', methods=['POST'])
def run_terminal_command():
    """Execute a terminal command"""
    data = request.get_json()
    command = data.get('command', '').strip()

    if not command:
        return jsonify({
            "status": "error",
            "message": "No command provided"
        }), 400

    # Start command execution in thread
    thread = threading.Thread(target=run_terminal_command_thread, args=(command,), daemon=True)
    thread.start()

    return jsonify({
        "status": "processing",
        "message": "Command sent to terminal"
    }), 202


@app.route('/get_terminal_output', methods=['GET'])
def get_terminal_output():
    """Get terminal command output"""
    output_lines = []

    while not TERMINAL_OUTPUT_QUEUE.empty():
        try:
            line = TERMINAL_OUTPUT_QUEUE.get_nowait()

            # Determine line type
            line_type = 'info'
            if line.startswith('$ '):
                line_type = 'command'
            elif line.startswith('[Command finished'):
                line_type = 'status'
            elif line.startswith('ERROR'):
                line_type = 'error'

            output_lines.append({
                "message": line,
                "type": line_type
            })
        except queue.Empty:
            break

    return jsonify({
        "output": output_lines
    }), 200


@app.route('/noVNC/')
def novnc_index():
    """Serve noVNC viewer page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Phoenix VNC</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <h1>VNC Viewer</h1>
        <p>Configure your VNC client to connect to this server on port 5900</p>
    </body>
    </html>
    """, 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "vm_running": QEMU_RUNNING
    }), 200


if __name__ == '__main__':
    print("=" * 60)
    print("Project Phoenix Backend Server")
    print("=" * 60)
    print(f"Starting server on 0.0.0.0:5000")
    print(f"VM Running: {QEMU_RUNNING}")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
