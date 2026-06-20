#!/usr/bin/env python
"""Check the actual uploader for known items"""

import sys
sys.path.insert(0, '/Users/samar/Projects')

import requests
from aegis_vault.utils.logger import logger

known_items = ['samar-vault', 'aegis-cloud', 'Encrypted-App-Backup-Bundle', 'angry-birds-silver-bounci-vectd', 'touhou-7-full-replays']

print("\n" + "="*60)
print("📋 Checking uploader field for your folders")
print("="*60 + "\n")

for item in known_items:
    try:
        url = f"https://archive.org/metadata/{item}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            uploader = data.get('metadata', {}).get('uploader', 'N/A')
            creator = data.get('metadata', {}).get('creator', 'N/A')
            print(f"{item}")
            print(f"  Uploader: {uploader}")
            print(f"  Creator: {creator}\n")
    except Exception as e:
        print(f"Error checking {item}: {e}\n")

print("="*60)
