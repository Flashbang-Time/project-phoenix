# Project Phoenix

Experience Full Windows on the Go!
Project Phoenix is an innovative and highly optimized web-based control panel designed to bring the power of a Windows Virtual Machine directly to your Android phone, leveraging the robust capabilities of Termux. Forget bulky laptops or complex command-line interfaces; Project Phoenix streamlines VM management into an intuitive, touch-friendly web interface, making high-performance mobile virtualization a reality.

This project empowers you to boot, manage, and interact with a lightweight Windows operating system, perfect for specialized software, legacy applications, or simply enjoying a desktop environment on your mobile device. With built-in audio support and essential setup tools, Project Phoenix offers a comprehensive solution for mobile computing enthusiasts and power users.

✨ Unleash Your Phone's Potential: Key Features
Effortless VM Management: Start and stop your Windows VM with single-click simplicity directly from your web browser.

Dynamic Configuration: Tailor your VM's performance by adjusting RAM (MB), CPU cores, and even selecting specific CPU models (like GraniteRapids-v1 for optimized performance on ARM processors) before each launch.

Integrated Visuals & Audio: Experience your Windows desktop in real-time through an embedded VNC viewer (powered by noVNC) and enjoy clear audio output thanks to seamless PulseAudio integration.

Live Status & Diagnostics: Keep an eye on your VM's operational status and review real-time QEMU logs and setup command outputs for straightforward troubleshooting.

One-Click Setup Tools: Conveniently prepare your Termux environment with integrated buttons to:

Create a dedicated ~/downloads/ directory for your VM files.

Install the qemu-system-x86-64-headless package, automating complex Termux commands.

Portable & Accessible: Control your VM from your phone's browser, or any device on your local network, transforming your Android device into a true mobile workstation.

🛠️ Requirements & Setup: What You'll Need
To get Project Phoenix soaring, ensure your Android device (or Termux environment within an emulator like Bluestacks) is ready:

Termux App: Your indispensable Linux environment on Android. Download from F-Droid for stability.

Ample Storage: A full Windows VM image requires substantial free space (100GB+).

Sufficient RAM: For a usable Windows experience, your phone should ideally have 8GB or more of RAM.

Windows VM Disk Image (.qcow2): A pre-installed, optimized Windows OS image in QEMU's .qcow2 format (lightweight/Lite builds recommended).

QEMU for Termux: Specifically the qemu-system-x86-64-headless package (installable via the UI's setup tools).

Python 3 & Dependencies: Handled automatically during setup.

Good Cooling: Running a VM is CPU intensive and will generate significant heat.

🚀 Quick Start (Detailed steps in README.md):
Install Termux & Essentials: pkg update && pkg upgrade -y, termux-setup-storage, pkg install python git dbus build-essential -y.

Prepare VM Image: Create ~/windows_vm and copy your YourWindowsVM.qcow2 there.

Clone Project Phoenix: git clone [YOUR_REPO_URL] && cd Project-Phoenix-QEMU-Control.

Install Python Libs: pip install Flask Flask-Cors websockets.

Configure QEMU Command: Edit qemu_server_unified.py to set your VM image path and preferred CPU model (e.g., -cpu GraniteRapids-v1).

Download noVNC Local Files: curl novnc.js and util.js into a static folder within your project.

Start PulseAudio: In a new Termux session: export XDG_RUNTIME_DIR=$(mktemp -d); pulseaudio --start.

Run Server: In your main Termux session: python qemu_server_unified.py.

Access UI: Open http://127.0.0.1:5000 in your phone's browser.

⚠️ Important Disclaimers & Security Information
Performance: Expect performance limitations. QEMU on ARM uses software emulation (TCG) for x86 instructions, which is inherently slower than native hardware virtualization. While optimized, it won't match a dedicated PC.

Heat & Battery: High CPU load will cause significant device heating and rapid battery drain. Use in a well-ventilated area or while charging.

VM Optimization is KEY: The responsiveness of your VM is highly dependent on the Windows image itself. Use "Lite" versions, disable unnecessary services, and optimize settings within Windows.

Security (CRITICAL!):

This server lacks authentication and robust security measures.

NEVER expose this server to the public internet via port forwarding or similar methods.

Doing so would allow unauthorized users to potentially execute arbitrary commands on your phone, install malicious software, or perform denial-of-service attacks.

Keep Project Phoenix strictly confined to your local network (e.g., Wi-Fi).

💡 Future Visions
Project Phoenix is continuously evolving! Ideas for future enhancements include: VNC password protection, QEMU snapshot management, advanced networking configurations, and improved UI/UX for a seamless experience.
