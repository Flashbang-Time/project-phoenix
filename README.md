

![alt text](https://cdn.discordapp.com/attachments/1047608068659224648/1407380771714371614/Your_paragraph_text_20250819_180544_0000.png?ex=68a5e4fb&is=68a4937b&hm=6c4e1de369943f70a156e3d27bfae412208c3f76d364a3f27b7d8c982daf540f&)



# 🚀 Project Phoenix – Windows VM on Android (via Termux)

**Experience full Windows on the go!**  
Project Phoenix transforms your Android device into a control center + QEMU VM host, complete with a touch-friendly web interface.

⚡ Run lightweight Windows builds, legacy apps, or just enjoy a desktop environment — all from your phone.

---

## ⚠️ Critical Security Note

👉 **Do NOT expose this server to the internet.**  
There is no authentication. If you port-forward this, you’re basically giving strangers root access to your phone.  
**Keep it local only (Wi-Fi/localhost).**

---

## 🛠️ Prerequisites

- 🧠 A brain (preferably switched on)  
- 📱 An Android device  
- 📦 Termux installed  
- ⚡ Some patience (performance depends on your phone — TCG is slooow)  

---

## 📥 Installation

Download the latest release from GitHub (look in the **Releases** tab).  

Open the `.sh` script in Termux.  

Run the following commands:

```bash
cd ~/downloads
chmod +x install.sh
./install.sh
```

---

## ⚙️ Setup

Once installed, open your browser and go to:  
**http://127.0.0.1:5000**

In the web interface, enter your primary disk image filename, e.g.:  

```
win10.qcow2
```

(Place this file inside the Project Phoenix directory so QEMU can find it.)

---

## 🖥️ Using the VM

You’ve got two options:

1. **Built-in browser VNC viewer** (runs inside the web UI)  
2. **External VNC client** → connect to `127.0.0.1:5900`

---

## 📀 Installing Drivers (Windows Guests)

1. Add the **virtio.iso** driver image through the web interface.  
2. Boot Windows, open **Device Manager**, and manually install drivers for each unknown device:
   - Storage  
   - Network  
   - Display (basic virtio GPU)  

👉 Don’t panic if Windows complains. Just keep clicking **Next** like a “human being.”

---

## ⚠️ Known Issues / Limitations

- 🔇 **Sound is broken** (might be unfixable, TCG doesn’t like us)  
- 🔑 **No VNC password** yet (planned, maybe)  
- 💤 **No snapshot support** (not my problem)  
- 🔥 **Performance + heat:** x86 on ARM = TCG hell. Expect lag + hot phone. (so don't expect miracles)

---

## 🔮 Future Visions

- VNC authentication  
- Snapshot management  
- Better networking options  
- Maybe fixing audio (**pls help**)  
