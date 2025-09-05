

![alt text](https://cdn.discordapp.com/attachments/1047608068659224648/1407380771714371614/Your_paragraph_text_20250819_180544_0000.png?ex=68a5e4fb&is=68a4937b&hm=6c4e1de369943f70a156e3d27bfae412208c3f76d364a3f27b7d8c982daf540f&)



Project Phoenix – Windows VM on Android (via Termux)
===================================================

Experience full Windows on the go!
Project Phoenix transforms your Android device into a control center and QEMU VM host, complete with a web interface.
Run lightweight Windows builds, legacy apps, or just enjoy a desktop environment — all from your phone.

---------------------------------------------------
CRITICAL SECURITY NOTE
---------------------------------------------------
Do NOT expose this server to the internet.
There is no authentication. If you port-forward this, you’re basically giving strangers root access to your phone.
Keep it local only (Wi-Fi/localhost).

---------------------------------------------------
Prerequisites
---------------------------------------------------
- A brain (preferably switched on)
- An Android device
- Termux installed
- Some patience (performance depends on your phone — TCG is slow)

---------------------------------------------------
Installation
---------------------------------------------------
1. Download the latest release from GitHub (check the Releases tab).
2. Open the .sh script in Termux.
3. Run the following commands:

cd ~/downloads
chmod +x install.sh
./install.sh

---------------------------------------------------
Setup
---------------------------------------------------
1. If everything went well, access the web interface at: 127.0.0.1:5000
2. In "Primary Disk Image Path (.qcow2)" enter your image filename (example: win10.qcow2)

---------------------------------------------------
Using the VM
---------------------------------------------------
1. Use any VNC client to connect to 127.0.0.1:5900
2. Default display is always :0 (port 5900)

---------------------------------------------------
Installing Drivers
---------------------------------------------------
1. Download virtio.iso from the repo
2. Add the ISO path in the web interface
3. Boot the VM, open Device Manager in Windows, and install the drivers manually

---------------------------------------------------
Known Issues / Limitations
---------------------------------------------------
- Performance will never match native hardware (TCG is software emulation)
- Expect heating and battery drain (use while charging if possible)
- No authentication/security built in
- Sound is broken
- No snapshot support

---------------------------------------------------
Future Visions
---------------------------------------------------
- VNC password protection
- QEMU snapshot management
- Further UI optimizations
