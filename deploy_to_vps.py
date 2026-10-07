# -*- coding: utf-8 -*-
"""
Deploy Global Cloud Directory & Telemetry to Remote VPS
Uploads HTML catalogs and database files directly to Nginx web root.
"""

import paramiko
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VPS_HOST = "109.248.43.154"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "hwDrIMD3PUeCqYhP"
REMOTE_DIR = "/var/www/html"

print("=" * 70)
print(f"🚀 DEPLOYING HTML CATALOGS TO REMOTE VPS: {VPS_HOST}")
print("=" * 70)

# Connect SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()

files_to_upload = [
    ("global_cloud_catalog.html", "index.html"),
    ("global_cloud_catalog.html", "global_cloud_catalog.html"),
    ("master_hourly_directory.html", "master_hourly_directory.html"),
    ("master_cloud_directory.json", "master_cloud_directory.json"),
    ("master_hourly_directory.json", "master_hourly_directory.json"),
]

for local_name, remote_name in files_to_upload:
    if os.path.exists(local_name):
        local_path = os.path.abspath(local_name)
        remote_path = f"{REMOTE_DIR}/{remote_name}"
        size = os.path.getsize(local_path)
        print(f"  📤 Uploading {local_name} ({size:,} bytes) → {remote_path}...")
        sftp.put(local_path, remote_path)
        print(f"  ✅ Uploaded {remote_name}")
    else:
        print(f"  ⚠️ File not found locally: {local_name}")

sftp.close()

# Verify file permissions and Nginx configuration
stdin, stdout, stderr = ssh.exec_command(f"chmod -R 755 {REMOTE_DIR}; ls -lh {REMOTE_DIR}")
output = stdout.read().decode('utf-8')
print("\n📋 Remote /var/www/html Contents:")
print(output)

ssh.close()

print("=" * 70)
print(f"🎉 DEPLOYMENT COMPLETE! LIVE URLS:")
print(f"  🌐 Master Directory (All 609 Providers): http://{VPS_HOST}/")
print(f"  🌐 Full Catalog URL:                    http://{VPS_HOST}/global_cloud_catalog.html")
print(f"  ⏱️ Hourly Directory (62 Providers):    http://{VPS_HOST}/master_hourly_directory.html")
print(f"  📊 Raw Cloud JSON:                      http://{VPS_HOST}/master_cloud_directory.json")
print(f"  📊 Raw Hourly JSON:                     http://{VPS_HOST}/master_hourly_directory.json")
print("=" * 70)
