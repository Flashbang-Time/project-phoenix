

![alt text](https://cdn.discordapp.com/attachments/1047608068659224648/1388179605604663468/Your_paragraph_text.png?ex=68600a81&is=685eb901&hm=8877f93ee180aacabfd9064409ff7c596f79fc05e92cba72b0b6fac0e5cf09b3&)



Experience Full Windows on the Go!
Project Phoenix is an innovative and highly optimized web-based control panel designed to bring the power of a Windows Virtual Machine directly to your Android phone, leveraging the robust capabilities of Termux. Forget bulky laptops or complex command-line interfaces; Project Phoenix streamlines VM management into an intuitive, touch-friendly web interface, making high-performance mobile virtualization a reality.

This project empowers you to boot, manage, and interact with a lightweight Windows operating system, perfect for specialized software, legacy applications, or simply enjoying a desktop environment on your mobile device. With built-in audio support and essential setup tools, Project Phoenix offers a comprehensive solution for mobile computing enthusiasts and power users.

⚠️ PREREQUISITES

1A. some mental capacity

2A. a brain

3A. an android phone

4A. termux


💡 INSTALLING

Download the script from the release and import the script into termux (open the file with termux), and run these commands

cd downloads

chmod +x install.sh

./install.sh


💡 SETUP

1B. If everything went well, you should be able to access the web interface using 127.0.0.1:5000 on any browser

2B. In the Primary Disk Image Path (.qcow2) put in the image file name eg. win10.qcow2

💡 USING THE VM

1C. Using any VNC app, connect to 127.0.0.1:5900

💡 INSTALLING DRIVERS

If you are on Windows, make sure to install the Drivers provided in the repo, here's how to:

Go into the web interface, and put in the filename eg. virtio.iso

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
Project Phoenix is continuously evolving! Ideas for future enhancements include: VNC password protectionand QEMU snapshot management.
