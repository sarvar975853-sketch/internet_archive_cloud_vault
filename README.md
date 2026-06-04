# AegisCloudVault 🛡️

AegisCloudVault is a modern, lightweight, and secure desktop vault 
interface designed exclusively for macOS. Built with a sleek user 
interface, it provides a seamless experience for managing your secure 
files without requiring any command-line tools or technical setup.

---

## ✨ Features

* **Native macOS Styling:** Beautiful, modern GUI featuring full support 
for native macOS Light and Dark modes.
* **Zero Dependencies:** Fully self-contained application bundle. You do 
not need Python, homebrew, or any coding libraries installed on your 
system.
* **Secure Protocols:** Utilizes strong cryptographic standards and 
network wrappers to handle your cloud vault securely.
* **Optimized Performance:** Packaged natively for macOS to run smoothly 
without draining your system resources.

---

## 🚀 How to Download & Install

Since this repository contains the production-ready application, you do 
not need to clone any code or run terminal commands to install it. Follow 
these simple steps:

1. Look at the right sidebar of this page and click on the 
**[Releases](https://github.com)** section.
2. Download the latest release file: `AegisCloudVault-macOS.zip`.
3. Go to your **Downloads** folder and double-click the `.zip` file to 
extract it.
4. Drag the extracted **AegisCloudVault.app** into your **Applications** 
folder just like any standard Mac app.

**NOTE**- Windows compatibility is in progress as I don't have a windows pc.

---

🔒 Security & Privacy

AegisCloudVault is built with a Privacy-First and Local-First architecture. Because this application is designed for secure vault management, your data integrity and anonymity are the highest priorities.
1. Data Sovereignty

    Zero Telemetry: This application does not include any tracking scripts, analytics, or "phone home" telemetry. Your usage patterns, app launch frequency, and feature interactions are never recorded or transmitted.

    No Remote Logging: Error logs and crash reports are handled locally on your machine. No information about your system or your files is sent to the developer or any third party.

2. Cryptographic Integrity

    AES-256 Encryption: All secure operations utilize the industry-standard cryptography library. Data is encrypted using AES-256 bit keys, ensuring your files remain unreadable to anyone without the correct authorization.

    Local Key Processing: Your encryption keys and cloud credentials are never stored in plain text. They are processed entirely within your computer's volatile memory and are cleared the moment the application is closed.

3. Connection Transparency

    Direct-to-Cloud: AegisCloudVault establishes a direct encrypted tunnel between your macOS device and your chosen cloud provider using the requests library.

    No Middle-Man: There are no proprietary intermediate servers. Your data does not pass through any third-party infrastructure other than the official API of your cloud storage provider.

4. Privacy on macOS

    Sandbox-Friendly: The app only accesses the specific directories you interact with. It does not scan your hard drive or monitor other applications.

    No Background Processes: When you quit AegisCloudVault, every associated process is terminated. There are no hidden "helpers" or background daemons that continue to run or consume resources.

    Security Disclosure: While AegisCloudVault utilizes robust, open-source cryptographic libraries to protect your data, security is a shared responsibility. Always ensure your macOS system is up to date and that you use strong, unique passwords for your cloud accounts.
---

## 🛡️ Bypassing macOS Gatekeeper (Important!)

Because this app is independently developed and not signed with an 
expensive Apple Corporate Developer ID, macOS's security layer 
(**Gatekeeper**) will likely block it on the first launch, throwing a 
warning like *"Developer cannot be verified"* or falsely claiming the 
application is *"damaged"*.

**This is completely normal for independent software.** You can safely 
allow your Mac to run the app using either of these quick methods:

### Method 1: The Right-Click Shortcut (Easiest)
1. Open your **Applications** folder in Finder.
2. Instead of double-clicking the app normally, **Right-click** (or hold 
the `Control` key and click) on **AegisCloudVault.app**.
3. Select **Open** from the context menu.
4. A prompt will appear asking for confirmation, but this time it will 
display a working **Open** button. Click it, and macOS will permanently 
remember your preference!

### Method 2: The Terminal Permission Fix
If macOS strictly blocks the application and states it is "damaged and 
cannot be opened" (Apple's default way of quarantining downloaded internet 
files), run this quick command:

1. Open the built-in **Terminal** app on your Mac.
2. Type the following command exactly as shown, making sure to include the 
space at the end:
   ```bash
   xattr -cr
