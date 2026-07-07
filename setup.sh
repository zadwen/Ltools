#!/bin/bash

echo "=================================================="
echo "   Ultimate Linux Gaming & Steam Tools Setup"
echo "=================================================="

# 1. Update and install core system dependencies
echo "[*] Installing required system packages..."
sudo apt update && sudo apt install -y curl jq python3-pip python3-venv git power-profiles-daemon

# 2. Run the LuaToolsLinux automated installer
echo "[*] Launching the main installer..."
echo "[*] IMPORTANT: Choose option (3) when the menu appears!"
echo "    Press Enter to start the installer..."
read -r

curl -fsSL https://raw.githubusercontent.com/Star123451/LuaToolsLinux/main/install.sh | bash

# 3. Inject optimized configuration files to prevent UI and download locks
echo "[*] Injecting ACCELA safe defaults..."
mkdir -p /home/anas/.config/SLSsteam
mkdir -p /home/anas/.local/share/ACCELA

cat << 'EOF' > /home/anas/.local/share/ACCELA/settings.json
{
    "download_settings": {
        "limit_downloads_to_steam_libraries": true,
        "skip_single_choice_selection": true,
        "maximum_concurrent_downloads": 4
    },
    "post_processing": {
        "generate_steam_achievements": false,
        "remove_steam_drm_with_steamless": true,
        "apply_goldberg_automatically": true,
        "create_application_shortcuts": false
    },
    "api_keys": {
        "hubcap_api_key": "746db49af16dcb085cac8583c072053eb6727b6363845b2cd5f36",
        "steamid64_api_key": ""
    }
}
EOF

# Fix permissions on injected files
chown -R anas:anas /home/anas/.config/SLSsteam
chown -R anas:anas /home/anas/.local/share/ACCELA

# 4. Map the layout launcher path directly to Steam
echo "[*] Mapping LuaTools layout configuration..."
mkdir -p /home/anas/.local/share/Steam/config
cat << 'EOF' > /home/anas/.local/share/Steam/config/luatools_config.json
{
    "external_launcher_path": "/home/anas/.local/share/ACCELA/ACCELA.AppImage"
}
EOF
chown -R anas:anas /home/anas/.local/share/Steam/config

# 5. Setup the automated Power Profile hardware switching (AC0 handling)
echo "[*] Deploying dynamic hardware power switcher..."
sudo mkdir -p /usr/local/bin

sudo cat << 'EOF' | sudo tee /usr/local/bin/switch_power_profile.sh > /dev/null
#!/bin/bash
sleep 0.5
AC_STATUS=$(cat /sys/class/power_supply/AC0/online 2>/dev/null)

if [ "$AC_STATUS" = "1" ]; then
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
        echo "performance" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
    fi
    for epp in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
        if [ -f "$epp" ]; then echo "performance" > "$epp"; fi
    done
    powerprofilesctl set performance 2>/dev/null
else
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
        echo "powersave" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
    fi
    for epp in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
        if [ -f "$epp" ]; then echo "balance_performance" > "$epp"; fi
    done
    powerprofilesctl set balanced 2>/dev/null
fi
EOF

sudo chmod +x /usr/local/bin/switch_power_profile.sh

# 6. Deploy the UDEV rules for the power profile
echo "[*] Creating hardware UDEV rules..."
sudo cat << 'EOF' | sudo tee /etc/udev/rules.d/99-power-profile.rules > /dev/null
SUBSYSTEM=="power_supply", ACTION=="change", RUN+="/usr/local/bin/switch_power_profile.sh"
EOF

sudo udevadm control --reload-rules && sudo udevadm trigger

echo "=================================================="
echo " Setup complete! Ready for your 4070 PC."
echo "=================================================="
