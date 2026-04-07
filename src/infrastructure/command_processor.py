import time
import json
import uuid
import datetime

class CommandProcessor:
    """
    The Central Logic Hub for Marvin's Multi-Channel Intake.
    Normalizes and authenticates commands from all external sources.
    """
    
    def __init__(self):
        # Telemetry Hub URL (configurable via environment variable)
        self.telemetry_hub = os.getenv("TELEMETRY_HUB_URL", "http://localhost:3000")

        # Executive API URL (configurable via environment variable)
        # In production, this should point to the private IP of bluesoap-backend-prod (172.31.34.85:8080)
        self.executive_api_url = os.getenv("EXECUTIVE_API_URL", "http://localhost:8080")

    def process_command(self, source, sender, message, payload=None):
        """
        Main entry point for all command channels.
        1. Normalize
        2. Authenticate (Checks whitelist/signature validation for specific source)
        3. Parse Intent (Heuristic search for key directives)
        4. Forward to Executive Queue
        """
        print(f"[COMMAND PROCESSOR] INCOMING Source={source} Sender={sender}")
        
        # 1. Normalization
        command = {
            "id": str(uuid.uuid4()),
            "source": source,
            "sender": sender,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "raw_text": message,
            "payload": payload or {},
            "status": "pending_auth"
        }
        
        # 2. Authentication Logic
        is_valid = self._authenticate(source, sender, message)
        if not is_valid:
             print(f"[ERROR] Authentication FAILURE for source {source}. REJECTED.")
             command["status"] = "REJECTED"
             return command
        
        # 3. Intent Parsing (Heuristic for now)
        command["intent"] = self._parse_intent(message)
        command["status"] = "AUTHENTICATED"
        
        print(f"[SUCCESS] Command {command['id']} authenticated. Intent: {command['intent']}")
        
        # 4. Push to Telemetry / Task Queue
        return self._push_to_execution_queue(command)

    def _authenticate(self, source, sender, message):
        """Source-specific authentication gates."""
        # Load Founder Whitelist from environment variables for production robustness
        # These should be securely managed (e.g., AWS Secrets Manager) in production.
        founder_whitelist_telegram_ids = os.getenv("FOUNDER_WHITELIST_TELEGRAM_IDS", "").split(",")
        founder_whitelist_emails = os.getenv("FOUNDER_WHITELIST_EMAILS", "").split(",")
        founder_whitelist_dashboard_keys = os.getenv("FOUNDER_WHITELIST_DASHBOARD_KEYS", "").split(",")

        if source == "dashboard":
             # Dashboard authentication is handled at the API Gateway (NGINX/FastAPI)
             return True
             
        if source == "telegram":
             if str(sender) in founder_whitelist_telegram_ids or sender in founder_whitelist_telegram_ids:
                  return True
        
        if source == "email":
             if sender in founder_whitelist_emails:
                  return True

        # Fallback for old hardcoded values during transition, should be removed later
        FOUNDER_WHITELIST_LEGACY_TEMP = {
            "telegram": ["FounderUID_PLACEHOLDER", "CFISHER33", "@CFISHER33", "8671836412", 8671836412], 
            "email": ["chaswfisher@gmail.com", "bluesoap.software@gmail.com"],
            "dashboard": ["FounderKey_PLACEHOLDER"]
        }

        if source in FOUNDER_WHITELIST_LEGACY_TEMP:
             if sender in FOUNDER_WHITELIST_LEGACY_TEMP[source]:
                  return True
        
        return False

    def _parse_intent(self, message):
        """Watchtower routing intent classifier (uses o3 if available)."""
        import os
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage
            model_name = os.getenv("OPENAI_MODEL", "o3-mini")
            llm = ChatOpenAI(model=model_name)
            prompt = "SYSTEM: You are the Watchtower Router. Classify intent into one of: DEPLOY_MISSION, STATUS_QUERY, REMEDIATION, SYSTEM_ABORT, GENERAL_DIRECTIVE. Return ONLY the category name."
            res = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=message)])
            return res.content.strip()
        except:
            m = message.lower()
            if "deploy" in m or "launch" in m: return "DEPLOY_MISSION"
            if "status" in m or "report" in m: return "STATUS_QUERY"
            if "remediate" in m or "fix" in m: return "REMEDIATION"
            if "cancel" in m or "stop" in m: return "SYSTEM_ABORT"
            return "GENERAL_DIRECTIVE"

    def _push_to_execution_queue(self, command):
        """Forward authenticated command to the Executive API."""
        try:
             import requests
             
             # Reformat to match the Executive API TaskCreate schema
             task_payload = {
                 "title": f"[{command['source'].upper()}] {command['intent']}",
                 "description": command['raw_text'],
                 "created_by": "CommandProcessor",
                 "assigned_to": "Marvin", # Marvin will process it
                 "requires_ceo_approval": False, # Marvin can escalate if needed
                 "input_payload": command
             }
             
             # Push via Executive API
             response = requests.post(f"{self.executive_api_url}/api/tasks", json=task_payload, timeout=5)
             if response.status_code == 200:
                 task_data = response.json()
                 print(f"[PROCESSOR] Successfully created task {task_data.get('id')} in Executive API at {self.executive_api_url}")
                 return f"Task created and assigned to Marvin: {task_data.get('id')}"
             else:
                 print(f"[PROCESSOR] Executive API returned {response.status_code}: {response.text}")
                 return f"Failed to create task. Executive API responded with {response.status_code}."
                 
        except Exception as e:
             print(f"[PROCESSOR] Failed to push to Executive API: {e}")
             return f"System Error: Failed to contact Executive API ({e})"

processor = CommandProcessor()
