#!/usr/bin/env python3
"""Select supported daemon profiles without writing CPU sysfs controls."""
from pathlib import Path
import subprocess


def desired_profile(root):
    online = []
    battery = False
    for supply in root.iterdir():
        try:
            kind = (supply / 'type').read_text().strip()
            battery |= kind == 'Battery'
            if kind in {'Mains', 'USB', 'USB_C', 'USB_PD', 'USB_PD_DRP', 'Wireless'}:
                online.append((supply / 'online').read_text().strip() == '1')
        except OSError:
            continue
    if any(online):
        return 'performance'
    if online and battery:
        return 'power-saver'
    # Desktops and unknown adapters should not be classified as battery-powered.
    return 'balanced'


def apply(root=Path('/sys/class/power_supply'), runner=subprocess.run):
    listing = runner(['powerprofilesctl', 'list'], check=True, capture_output=True, text=True)
    available = {line.strip().lstrip('*').strip().removesuffix(':')
                 for line in listing.stdout.splitlines() if line.rstrip().endswith(':')}
    desired = desired_profile(root)
    if desired not in available:
        desired = 'balanced'
    if desired not in available:
        raise RuntimeError('No supported balanced profile was reported by powerprofilesctl.')
    current = runner(['powerprofilesctl', 'get'], check=True, capture_output=True, text=True).stdout.strip()
    if current != desired:
        runner(['powerprofilesctl', 'set', desired], check=True)


if __name__ == '__main__':
    apply()
