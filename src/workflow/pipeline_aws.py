import os
import json
import zipfile
import subprocess
import time
import sys
# Conditional imports to avoid crashing if deps not installed yet
try:
    import boto3
    import paramiko
    from scp import SCPClient
except ImportError:
    print("[WARNING] AWS dependencies not found. Please run: pip install -r requirements_aws.txt")

class BlueSoapPipeline:
    def __init__(self, config_path="aws_config.json"):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config = self._load_config(config_path)
        
        # Initialize AWS Clients (Lazy Load)
        self.s3_client = None
        self.cf_client = None

    def _load_config(self, path):
        if not os.path.exists(path):
            print(f"[ERROR] Config file not found: {path}")
            print("Please copy 'aws_config_template.json' to 'aws_config.json' and fill in your details.")
            sys.exit(1)
        with open(path, "r") as f:
            return json.load(f)

    def _get_s3(self):
        if not self.s3_client:
            self.s3_client = boto3.client('s3', region_name=self.config.get("aws_region", "us-east-2"))
        return self.s3_client

    def _get_cf(self):
        if not self.cf_client:
            self.cf_client = boto3.client('cloudfront', region_name=self.config.get("aws_region", "us-east-2"))
        return self.cf_client

    def deploy_frontend(self, target="production"):
        """
        Syncs frontend assets to S3.
        target: 'production' (bluesoapsoftware.com) or 'watchtower' (bluesoap-frontend)
        """
        if target not in self.config["frontend"]:
            print(f"[ERROR] Target '{target}' not defined in config.")
            return

        conf = self.config["frontend"][target]
        bucket_name = conf["s3_bucket"]
        local_path = os.path.join(self.root_dir, conf["local_path"])
        dist_id = conf["cloudfront_distribution_id"]
        
        print(f"\n🌐 [{target.upper()}] Starting Deployment...")
        print(f"   -> Local Source: {local_path}")
        print(f"   -> Target Bucket: s3://{bucket_name}")

        if not os.path.exists(local_path):
            print(f"[ERROR] Local path not found: {local_path}")
            return

        s3 = self._get_s3()
        
        # 0. Ensure Website Hosting is Enabled (Fix for NoSuchWebsiteConfiguration)
        try:
            print(f"   -> Verifying Website Configuration for {bucket_name}...")
            s3.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration={
                    'ErrorDocument': {'Key': 'index.html'},
                    'IndexDocument': {'Suffix': 'index.html'},
                }
            )
            # Also ensure public access logic (omitted for brevity, assuming bucket policy is set or will be manual)
            print("   -> Website Configuration Enabled.")
        except Exception as e:
            print(f"      [!] Failed to set website config: {e}")

        # 1. Sync Files
        print(f"   -> Syncing files...")
        upload_count = 0
        for root, dirs, files in os.walk(local_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, local_path)
                s3_key = rel_path.replace("\\", "/") 
                
                # Watchtower Prefix logic: If watchtower, clients are usually in root of local_path? 
                # Yes: src/static/clients -> /clients/{id}/... 
                # Actually, local_path is src/static for prod, src/static/clients for watchtower.
                # If src/static/clients contains folder "tlr", rel_path is "tlr/index.html".
                # We want /clients/tlr/index.html in the bucket? Or just /tlr/?
                # User said: /clients/{client_id}/prototype/.
                # If local is src/static/clients/tlr/index.html -> rel is tlr/index.html.
                # If target is watchtower, should we prepend 'clients/'?
                # The bucket is "bluesoap-frontend". 
                # Requirement: /clients/{client_id}/prototype/
                # Let's assume for now we mirror the folder structure. 
                # If local_path = src/static/clients, and file is tlr/index.html, s3_key is tlr/index.html.
                # We should probably prepend "clients/" to match the request or assume the bucket root IS clients?
                # "Each client will receive their own directory... /clients/{client_id}/"
                # If I sync "src/static/clients" to bucket root, I get "tlr/index.html". 
                # I should probably map src/static/clients -> s3://bucket/clients/
                
                final_key = s3_key
                if target == "watchtower":
                     final_key = f"clients/{s3_key}"

                # Content Type Guessing
                content_type = "application/octet-stream"
                if file.endswith(".html"): content_type = "text/html"
                elif file.endswith(".css"): content_type = "text/css"
                elif file.endswith(".js"): content_type = "application/javascript"
                elif file.endswith(".png"): content_type = "image/png"
                elif file.endswith(".jpg"): content_type = "image/jpeg"
                elif file.endswith(".json"): content_type = "application/json"
                elif file.endswith(".md"): content_type = "text/markdown"

                try:
                    s3.upload_file(
                        full_path, 
                        bucket_name, 
                        final_key, 
                        ExtraArgs={'ContentType': content_type}
                    )
                    upload_count += 1
                except Exception as e:
                    print(f"      [!] Failed to upload {final_key}: {e}")

        print(f"   -> Uploaded {upload_count} files.")

        # 2. Invalidate CloudFront
        if dist_id:
            print(f"   -> Invalidating CloudFront ({dist_id})...")
            cf = self._get_cf()
            try:
                batch = {
                    'Paths': {
                        'Quantity': 1,
                        'Items': ['/*']
                    },
                    'CallerReference': str(time.time())
                }
                cf.create_invalidation(DistributionId=dist_id, InvalidationBatch=batch)
                print("   -> Invalidation Request Sent.")
            except Exception as e:
                print(f"      [!] Invalidation Failed: {e}")
        else:
            print("   -> Skipped Invalidation (ID missing).")
    def _create_backend_zip(self):
        print("   -> Creating deployment package...")
        zip_path = os.path.join(self.root_dir, "backend_deploy.zip")
        src_dir = os.path.join(self.root_dir, "src")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.root_dir):
                # Exclude .git, __pycache__, vmv, etc.
                if ".git" in root or "__pycache__" in root or "venv" in root:
                    continue
                
                # Only include src/, requirements.txt, .env
                rel_root = os.path.relpath(root, self.root_dir)
                
                # Filtering logic
                if not (rel_root == "." or rel_root.startswith("src") or rel_root.startswith("research_reports")):
                    continue

                for file in files:
                    if file.endswith(".pyc"): continue
                    # Explicit inclusions
                    if rel_root == "." and file not in ["requirements.txt", "requirements_aws.txt", ".env", "aws_config.json"]:
                        continue
                        
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, self.root_dir)
                    zipf.write(full_path, arcname)
                    
        print(f"   -> Package Ready: {zip_path}")
        return zip_path

    def deploy_backend(self):
        """Deploys code to EC2 instances."""
        print("\n⚙️ [BACKEND] Starting Deployment...")
        instances = self.config["backend"]["ec2_instances"]
        remote_dir = self.config["backend"]["remote_path"]
        service = self.config["backend"]["service_name"]
        
        # 1. Create Zip
        zip_path = self._create_backend_zip()
        
        # 2. Deploy to each instance
        for inst in instances:
            ip = inst["ip"]
            user = inst["user"]
            key = inst["key_path"] # Check if relative or absolute
            if not os.path.isabs(key):
                key = os.path.join(self.root_dir, key)

            print(f"   -> Connecting to {ip}...")
            
            try:
                # SSH Connection
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=user, key_filename=key)
                
                # SCP Upload
                print(f"      + Uploading package...")
                with SCPClient(ssh.get_transport()) as scp:
                    scp.put(zip_path, f"/tmp/backend_deploy.zip")
                    
                # Remote Commands
                print(f"      + Installing & Restarting...")
                host_service = inst.get("service_name", service)
                commands = [
                    f"mkdir -p {remote_dir}",
                    f"unzip -o /tmp/backend_deploy.zip -d {remote_dir}",
                    f"/opt/bluesoap/venv/bin/pip install -r {remote_dir}/requirements.txt",
                    f"sudo systemctl restart {host_service}",
                    f"sudo systemctl status {host_service} --no-pager"
                ]
                
                for cmd in commands:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    exit_status = stdout.channel.recv_exit_status()
                    output = stdout.read().decode()
                    if exit_status != 0 and "status" not in cmd:
                        print(f"      [!] Command Failed: {cmd}")
                        print(f"          {stderr.read().decode()}")
                    elif "status" in cmd:
                         print(f"      [INFO] Service Status:\n{output}")
                    
                print(f"      + {ip}: Deployment Successful.")
                if inst.get("role") == "fastapi":
                    print("      + Verified target role: fastapi (canonical service expected: executive-api).")
                    validate_cmds = [
                        "curl -o /dev/null -s -w '%{http_code}' http://127.0.0.1:8080/docs",
                        "curl -o /dev/null -s -w '%{http_code}' http://127.0.0.1:8080/openapi.json"
                    ]
                    for vcmd in validate_cmds:
                        stdin, stdout, stderr = ssh.exec_command(vcmd)
                        code = stdout.read().decode().strip()
                        print(f"      + Validation {vcmd.split('/')[-1]} => {code}")
                ssh.close()
                
            except Exception as e:
                print(f"      [!] Failed to deploy to {ip}: {e}")
                
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        print("   -> Backend Deployment Complete.")

if __name__ == "__main__":
    pipeline = BlueSoapPipeline()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        print("Usage: python pipeline_aws.py [production|watchtower|backend|all]")
        sys.exit(1)
        
    if mode in ["production", "all"]:
        pipeline.deploy_frontend(target="production")
        
    if mode in ["watchtower", "all"]:
        pipeline.deploy_frontend(target="watchtower")
    
    if mode in ["backend", "all"]:
        pipeline.deploy_backend()
