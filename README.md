# Zorin OS Ultimate Gaming & Hardware Setup Automation

This repository contains an automated setup script (`setup.sh`) designed to configure a clean installation of Zorin OS for high-performance gaming, optimized Steam utility tools, and instant hardware-level power state switching.

## What This Script Solves

When setting up custom gaming layouts, tools, and background hardware management on Linux, minor permission mismatches or manual paths can break configurations. This script completely automates the process and eliminates 5 critical friction points:

1. **Permission & UI Lock Fixes:** Automatically corrects folder permissions (`chown`) from `root` back to the standard user account (`anas`), preventing user interface freezes and "Permission Denied" errors when running tools.
2. **Optimized Network Pipelines:** Bypasses restrictive default download limits by injecting optimized network configurations, setting the system to run **4 parallel download streams** simultaneously to maximize internet bandwidth without crashing the connection.
3. **Automated API Integration:** Injects your specific Hubcap API credentials directly into the application backend configuration files, completely removing the need to manually copy or type keys during installation.
4. **Seamless Steam Launcher Mapping:** Automatically writes configuration files directly to your hidden Steam directories, perfectly linking your layout systems and external tools so everything bridges out-of-the-box.
5. **Instant Hardware-Level Power Switching:** Completely bypasses unstable desktop layer power daemons. It deploys a low-level hardware script alongside custom kernel device rules (`udev`), forcing the CPU governor to instantly snap between maximum performance (on AC power) and balanced efficiency (on battery).

---

## Architecture Breakdown

The script executes sequentially across these core areas:
* **System Packages:** Pulls down critical system binaries (`curl`, `jq`, `git`, and power management libraries) via the Advanced Package Tool (`apt`).
* **Tool Deployment:** Fetches and kicks off the interactive installer loop for the background game tools.
* **Configuration Injection:** Generates precise JSON objects inside `~/.local/share/ACCELA/` and `~/.local/share/Steam/` to seed credentials and paths natively.
* **Kernel Rule Enforcement:** Drops a custom automation binary into `/usr/local/bin/` and maps a persistent device manager profile under `/etc/udev/rules.d/` targeting the `AC0` power subsystem.

---

## How to Use It

### Step 1: Create the script locally
If you haven't done so, copy the contents of the `setup.sh` script into a file on your system:
```bash
nano setup.sh
# Paste the code, save and exit (Ctrl+O, Enter, Ctrl+X)
```
tep 2: Make it executable
Give the script permission to run as a system utility:

```
chmod +x setup.sh
```

Step 3: Execute
Run the script. Important: When the interactive installer prompt appears on your screen, manually select Option 3 to finalize the tool compilation:

Bash
```
./setup.sh
```
by zadwen
