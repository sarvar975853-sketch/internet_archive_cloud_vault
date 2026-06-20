#!/usr/bin/env python
"""
Quick test to verify folder detection is working correctly.
Run this to check if your actual folders are being found.
"""

import sys
sys.path.insert(0, '/Users/samar/Projects')

from aegis_vault.core.storage import IAStorageEngine
from aegis_vault.core.credentials import CredentialManager
from aegis_vault.utils.logger import logger

# Load credentials
cred_manager = CredentialManager()
access_key, secret_key = cred_manager.load_credentials()

if not access_key or not secret_key:
    print("❌ No credentials found. Please login first.")
    exit(1)

print("\n" + "="*60)
print("🔍 Testing Folder Detection")
print("="*60)

# Initialize storage engine
storage = IAStorageEngine(access_key, secret_key)

# Scan for folders
print("\n🔐 Scanning for your folders...")
folders = storage.scan_user_folders()

print(f"\n✅ Found {len(folders)} folders:\n")
for i, folder in enumerate(folders, 1):
    print(f"  {i}. {folder}")

print("\n" + "="*60)
if len(folders) > 0:
    print("✓ SUCCESS: Folders found!")
    print(f"✓ Your app should display these {len(folders)} folders in the sidebar")
else:
    print("❌ ERROR: No folders found")
    print("❌ Check your credentials and Internet Archive uploads")
print("="*60 + "\n")
