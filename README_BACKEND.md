# Project Phoenix Backend

Flask REST API server for controlling QEMU virtual machines from the React Native mobile app.

## Installation

### On Termux (Android)

```bash
# Install Python and dependencies
pkg install python python-pip

# Install Flask
pip install flask flask-cors

# Install QEMU (optional, for actual VM functionality)
pkg install qemu-system-x86-64-headless qemu-utils
```

## Running the Server

```bash
# Make the script executable
chmod +x backend.py

# Run the server
python backend.py
```

The server will start on `0.0.0.0:5000` and be accessible from any device on your local network.

## Finding Your IP Address

To connect from your mobile app, you need to find your device's local IP address:

```bash
# Method 1
ip addr show wlan0 | grep inet

# Method 2
ifconfig wlan0 | grep inet
```

Look for an IP address like `192.168.x.x` or `10.0.x.x`

## API Endpoints

All endpoints required by the React Native app:

### VM Control
- `GET /vm_status` - Get current VM status
- `POST /start_vm` - Start VM with configuration
- `POST /stop_vm` - Stop running VM
- `GET /get_defaults` - Get default configuration values
- `GET /qemu_logs` - Get QEMU output logs

### Terminal
- `POST /run_terminal_command` - Execute a terminal command
- `GET /get_terminal_output` - Get terminal output

### Health Check
- `GET /health` - Server health status

## Configuration

Edit the default values at the top of `backend.py`:

```python
DEFAULT_PRIMARY_DISK_PATH = "/path/to/disk.qcow2"
DEFAULT_CDROM_PATH = "/path/to/iso.iso"
DEFAULT_RAM_MB = 8192
DEFAULT_CORES = 6
```

## Mobile App Setup

1. Open the Project Phoenix app
2. Go to Settings tab
3. Enter your server IP: `http://192.168.x.x:5000`
4. Tap "Test Connection"
5. If successful, tap "Save Settings"

## Troubleshooting

**Can't connect from mobile app:**
- Ensure both devices are on the same WiFi network
- Check firewall settings
- Verify the server is running: `curl http://localhost:5000/health`

**VM won't start:**
- Check that QEMU is installed: `which qemu-system-x86_64`
- Verify disk paths exist
- Check QEMU logs via `/qemu_logs` endpoint

**Permission errors:**
- Ensure you have read access to disk images
- Run with proper permissions for QEMU
