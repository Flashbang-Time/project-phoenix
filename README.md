# Project Phoenix 🪖

Experience Full Windows on the Go!
Project Phoenix is an innovative and highly optimized web-based control panel designed to bring the power of a Windows Virtual Machine directly to your Android phone, leveraging the robust capabilities of Termux. Forget bulky laptops or complex command-line interfaces; Project Phoenix streamlines VM management into an intuitive, touch-friendly web interface, making high-performance mobile virtualization a reality.

This project empowers you to boot, manage, and interact with a lightweight Windows operating system, perfect for specialized software, legacy applications, or simply enjoying a desktop environment on your mobile device. With built-in audio support and essential setup tools, Project Phoenix offers a comprehensive solution for mobile computing enthusiasts and power users.

⚠️ PREREQUISITES

1A. some mental capacity

2A. a brain

3A. an android phone

4A. termux

5A. INPORTANT check step 2C

💡 HOW TO INSTALL

1B. Open Termux (downloaded from FDroid) 

2B. Now execute the following commands

3B. apt update, apt upgrade

4B. apt install qemu-common

5B. apt install qemu-system-x86-64-headless

6B. apt install python (if not installed already)

7B. pip install flask

8B. pip install flask_cors


💡 FIRST SETUP

1C. Import the web.py, index.html and os image using your file manager (just open the files with termux and import them into the default [downloads] folder)

2C. MAKE SURE YOUR OS IMAGE IS CALLED os.qcow2 OTHERWISE THE VM WON'T BOOT

3C. Execute these commands:
   cd downloads
   pyhton web.py

4C. If everything went well, you should be able to access the web interface using 127.0.0.1:5000 on any browser

💡 USING THE VM

1D. Using any VNC app, connect to 127.0.0.1:5900

💡 INSTALLING DRIVERS

If you are on Windows, make sure to install the Drivers provided in the repo, here's how to:

cd downloads (if not already in the downloads directory)

rm web.py

using any text editor of your choice open web.py from your file explorer and in the

BASE_QEMU_COMMAND = (

    "/data/data/com.termux/files/usr/bin/qemu-system-x86_64 "
    
    "-smp {cores} -m {ram_mb} "
    
    "-drive file=/data/data/com.termux/files/home/downloads/os.qcow2,if=ide,cache=writeback,aio=threads "
    
    "-netdev user,id=net0 -device virtio-net-pci,netdev=net0 "
    
    "-vga virtio -cpu {cpu_model} "
    
    "-vnc 0.0.0.0:0"
)

Add a line called "-cdrom virtio-win-0.1.271.iso"

So it'll be like this

BASE_QEMU_COMMAND = (

    "/data/data/com.termux/files/usr/bin/qemu-system-x86_64 "
    
    "-smp {cores} -m {ram_mb} "
    
    "-drive file=/data/data/com.termux/files/home/downloads/os.qcow2,if=ide,cache=writeback,aio=threads "
    
    "-netdev user,id=net0 -device virtio-net-pci,netdev=net0 "
    
    "-vga virtio -cpu {cpu_model} "
    
    "-vnc 0.0.0.0:0"
    
    "-cdrom virtio-win-0.1.271.iso"    
)

After editing it reimport the file into termux using step 1C.

Again, execute:

cd downloads

python web.py

After boot, go into device manager and install the drivers like any human being.


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
