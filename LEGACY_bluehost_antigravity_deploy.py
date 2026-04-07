"""
DEPRECATED LEGACY DEPLOY SCRIPT

Name: LEGACY_bluehost_antigravity_deploy.py
Status: DO NOT USE FOR CURRENT PRODUCTION
Reason: This script belongs to the older BlueHost / direct-SFTP deployment era.
Current production target is AWS infrastructure using EC2, S3, CloudFront, Route 53, and SES.

Notes:
- This script selectively uploads static website assets from Projects\\BlueSoap Software Website\\05-Development
- It does not deploy the FastAPI backend
- It does not use GitHub-based deployment
- It does not use the current AWS production pipeline

If deployment work is needed, prefer the current AWS-oriented tooling and documentation:
- aws_config.json
- src\\workflow\\pipeline_aws.py
- deploy\\deploy_frontend.sh
- deploy\\deploy_backend.sh
- AWS_RECOVERY_README.md
"""

import os
import json
import subprocess
import datetime

# Load Configuration
try:
    with open("deploy_config.json", "r") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("[Error] deploy_config.json not found. Run setup_ssh_deployment.py first.")
    exit(1)

SSH_KEY = CONFIG["ssh_key_path"]
USER = CONFIG["user"]
HOST = CONFIG["host"]
REMOTE_ROOT = CONFIG["remote_path"]

# Local Source (The Development Folder)
LOCAL_ROOT = os.path.join(os.getcwd(), "Projects", "BlueSoap Software Website", "05-Development")

def generate_sftp_batch(files_to_sync):
    """Generates a temporary batch script for sftp."""
    batch_path = "sftp_batch.cmd"
    
    with open(batch_path, "w") as f:
        f.write("# Automated Deployment Batch\n")
        
        created_dirs = set()
        
        for local_path in files_to_sync:
            # Convert to relative path from LOCAL_ROOT
            rel_path = os.path.relpath(local_path, LOCAL_ROOT)
            remote_path = f"{REMOTE_ROOT}/{rel_path}".replace("\\", "/")
            
            # Directory Handling
            remote_dir = os.path.dirname(remote_path)
            if remote_dir not in created_dirs:
                # Add -mkdir for the directory (recursively would be better but simple logic for now)
                # We assume top level exists. We'll try to make the specific parent.
                # Use "-" to ignore failure if it exists.
                f.write(f"-mkdir \"{remote_dir}\"\n")
                created_dirs.add(remote_dir)
            
            # Convert local path for Windows SFTP
            clean_local = local_path.replace("\\", "/")
            
            f.write(f"put \"{clean_local}\" \"{remote_path}\"\n")
            
        f.write("bye\n")
    return batch_path

def deploy_all():
    print("🚀 ANTIGRAVITY DEPLOYER: Initiating Sequence...")
    
    # 1. Identify Files (For v1, we deploy the Portal mostly)
    # In a real git-based flow, we'd check git diff. 
    # Here we scan for recent changes or specific targets.
    
    target_files = []
    # Force include Key Assets
    important_paths = [
        "images/bluesoap_cube_favicon.png",
        "offerings/agents.html",
        "offerings/web.html",
        "offerings/media.html",
        "onboarding/index.html",
        "products/audit.html",
        "products/vox.html",
        "products/grants.html",
        "products/intel.html",
        "products/brand.html",
        "portal/universal_portal.html",
        "portal/grant_seeker.html",
        "portal/intel_console.html",
        "portal/muse_labs.html",
        "portal/css/universal.css",
        "portal/dashboard.html",
        "portal/js/magnetic_buttons.js",
        "portal/js/agent_genesis.js",
        "portal/js/kingdom_map.js",
        "portal/js/kingdom_data.js",
        "portal/js/orb.js",
        "portal/agent_genesis.html",
        "portal/kingdom_map.html",
        "portal/media.html",
        "portal/muse_labs.html",
        "portal/css/style.css",
        "clients/big-love-ministries/index.html",
        "clients/big-love-ministries/agreement.html",
        "clients/big-love-ministries/js/signature_pad.js",
        "clients/big-love-ministries/ecosystem/church-suite.html",
        "clients/big-love-ministries/ecosystem/executive-suite.html",
        "clients/big-love-ministries/ecosystem/grants-suite.html",
        "clients/big-love-ministries/mailroom.html"
    ]
    
    for p in important_paths:
        full_p = os.path.join(LOCAL_ROOT, p)
        if os.path.exists(full_p):
            target_files.append(full_p)
    
    print(f"[Plan] Syncing {len(target_files)} critical assets to {HOST}...")
    
    # 2. Generate Batch
    batch_file = generate_sftp_batch(target_files)
    
    # 3. Execute SFTP
    # Command: sftp -i keyfile -b batchfile user@host
    cmd = f'sftp -i "{SSH_KEY}" -b {batch_file} -o StrictHostKeyChecking=no {USER}@{HOST}'
    
    print("[Action] Connecting to BlueHost Stargate (SFTP)...")
    try:
        # We assume OpenSSH sftp is in PATH
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ DEPLOYMENT SUCCESSFUL")
            print("The following artifacts were teleported:")
            for p in important_paths:
                print(f" - {p}")
        else:
            print("\n❌ DEPLOYMENT FAILED")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            
    except Exception as e:
        print(f"[Critical Error] {e}")
    finally:
        if os.path.exists(batch_file):
            os.remove(batch_file)

if __name__ == "__main__":
    deploy_all()
