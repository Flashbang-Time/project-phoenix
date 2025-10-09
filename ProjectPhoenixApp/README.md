# Project Phoenix Mobile (less broken*)

A React Native mobile application for controlling Project Phoenix QEMU VMs running on Android via Termux.

## Features

- **VM Control**: Start, stop, and configure QEMU virtual machines
- **VNC Access**: Remote desktop connection to your VMs
- **Terminal**: Execute commands on the host system
- **Settings**: Configure server connection and app behavior
- **Real-time Monitoring**: Live VM status updates

## Prerequisites

1. **Termux** installed on your Android device
2. **Project Phoenix server** running in Termux
3. **Node.js and Expo CLI** for development

## Installation

### For Development

1. Clone this repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npx expo start
   ```
4. Use Expo Go app to scan the QR code and run on your device

### For Production

1. Build the APK:
   ```bash
   npx expo build:android
   ```
2. Install the generated APK on your Android device

## Configuration

### First-time Setup

1. **On Termux device**: Run the HTTPS setup script
   ```bash
   cd /path/to/project
   ./setup_https.sh
   ```

2. **Start the backend server**:
   ```bash
   python backend.py
   ```

3. **In the mobile app**:
   - Open the app and go to the **Settings** tab
   - Set **Server URL** to: `https://localhost:5000` or `https://YOUR-IP:5000`
   - Tap **Test Connection**
   - If successful, tap **Save Settings**

### Important Notes

- The app **requires HTTPS** (not HTTP)
- Self-signed certificates are supported but may show warnings
- Use hostname (localhost) or IP address with HTTPS
- Both HTTP and HTTPS work, but HTTPS is strongly recommended

## Usage

### VM Control
- Configure VM settings (RAM, CPU, disk images, etc.)
- Start and stop virtual machines
- Monitor VM status in real-time

### VNC Connection
- Connect to your VM's desktop remotely
- Use touch gestures to interact with the VM
- Full-screen VNC viewer with disconnect option

### Terminal Access
- Execute commands on the host system
- View command output in real-time
- Quick command shortcuts for common operations

## Server Requirements

This app requires the Project Phoenix Flask server to be running. Make sure:

1. The server is accessible on your network
2. CORS is properly configured
3. All API endpoints are functional

## Troubleshooting

### Connection Issues

**"Network request failed" errors:**
- Make sure server URL uses `https://` (not `http://`)
- Verify server is running: `curl -k https://localhost:5000/health`
- Check both devices are on same WiFi network
- Try using IP address instead of hostname if resolution fails

**Certificate errors with HTTPS:**
- This is normal with self-signed certificates
- The app is configured to accept them
- Rebuild the app after configuration changes

**Can't connect with hostname:**
- Use IP address instead: `https://192.168.x.x:5000`
- Find your IP: `ip addr show wlan0 | grep inet`

### VNC Problems
- Make sure the VM is running before connecting
- Check that VNC is properly configured in QEMU
- Try refreshing the VNC connection

### Performance
- Close other apps to free up memory
- Use a device with sufficient RAM for smooth operation
- Consider reducing VM resource allocation if needed

## Development

### Project Structure
```
src/
├── screens/          # Main app screens
├── services/         # API service layer
└── components/       # Reusable components (future)
```

### Adding Features
1. Create new screens in `src/screens/`
2. Add navigation routes in `App.js`
3. Extend `ApiService.js` for new API endpoints
4. Update the UI with appropriate styling

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the Project Phoenix documentation
3. Open an issue on GitHub
