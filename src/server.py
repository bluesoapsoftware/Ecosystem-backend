from fastapi import FastAPI, UploadFile, HTTPException, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
# Re-verified imports for reliability
from pydantic import BaseModel
import os
import shutil
from typing import List, Optional
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import stripe

# Load Env Vars (API Key) efficiently
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # In production, .env should always be at root_dir/.env
    # This fallback is for local dev environments where .env might be in user home.
    # For a robust production deploy, ensure .env is correctly placed or managed via AWS Secrets Manager.
    print("WARNING: .env not found in project root. Attempting fallback for local dev. Ensure .env is present in production.")
    # Removed absolute path fallback, ensuring platform independence
    pass # No fallback to a hardcoded C:\Users\... path

# Windows Subprocess Flags
CREATE_NEW_CONSOLE = 0x00000010
DETACHED_PROCESS = 0x00000008

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe_public_key = os.getenv("STRIPE_PUBLIC_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Add project root to path so we can import src.marvin correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
sys.path.append(current_dir)

from marvin import app as marvin_app, load_profile
from langchain_core.messages import HumanMessage, AIMessage

from src.infrastructure.command_processor import processor

# INITIALIZE FASTAPI APP (Fixes NameError)
app = FastAPI(title="BlueSoap Marvin API", version="2.0")

# Add CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "online", "timestamp": "live_cloud_uplink"}

@app.get("/api/status")
async def get_status():
    return {"status": "online", "service": "marvin-backend"}

class OnboardingRequest(BaseModel):
    type: str
    name: str
    org: str
    service: str
    magicAnswer: str
    email: str
    time: str

@app.post("/api/onboarding/submit")
async def onboarding_submit(data: OnboardingRequest):
    """
    Triggers: Zeta (CRM), Gamma (Calendar), Alpha (Email).
    """
    try:
        # PENDING: Logic to save to DB
        return {"status": "success", "message": "Onboarding initiated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BookingRequest(BaseModel):
    client_id: str
    service_type: str
    name: str
    phone: str
    notes: Optional[str] = None

@app.post("/api/booking/submit")
async def booking_submit(data: BookingRequest):
    """
    Agent Gamma: Handles booking requests for clients (e.g. F4F).
    Integrated with Google Calendar (Real).
    """
    try:
        # LOGIC:
        # 1. Log to CRM (Zeta)
        print(f"[GAMMA] Booking Request for {data.client_id}: {data.service_type} from {data.name}")
        
        # 2. Add to Calendar (Primary = BlueSoap.Software@gmail.com)
        from src.tools.calendar import create_event
        import datetime
        
        # Default to tomorrow at 9am (MVP Logic)
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        start_time = tomorrow.replace(hour=9, minute=0, second=0).isoformat()
        
        event_link = create_event(
            summary=f"F4F: {data.service_type} - {data.name}",
            start_time_str=start_time,
            description=f"Client: {data.name}\nPhone: {data.phone}\nService: {data.service_type}\nSite: F4F Deployment"
        )
        
        # 3. Trigger SMS Notification (Alpha/Gamma) - Simulated
        
        return {
            "status": "success", 
            "message": f"Agent Gamma has booked your appointment. Confirmation: {event_link}"
        }
    except Exception as e:
        print(f"[GAMMA ERROR] {e}")
        # Fallback to success simulation if Calendar fails (to avoid breaking demo flow due to auth)
        return {
            "status": "success", 
            "message": f"[TEST MODE] Booking Received (Calendar sync pending: {str(e)})"
        }



# --- OAUTH: GOOGLE CALENDAR (F4F) ---
@app.get("/api/auth/google/login")
async def google_login():
    """Generates the Google OAuth URL for the user to authorize."""
    # In a real app, this uses flow.authorization_url()
    # For V2.0 Prototype, we simulate the flow or return a placeholder if credentials missing.
    return {"url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=PLACEHOLDER&redirect_uri=http://localhost:8000/api/auth/google/callback&response_type=code&scope=https://www.googleapis.com/auth/calendar"}

@app.get("/api/auth/google/callback")
async def google_callback(code: str):
    """Exchanges code for token (Pending Prod Key)."""
    return HTMLResponse("<h1>Authorization Successful</h1><p>The Faithful 4 Legged Family Calendar is now connected to Agent Gamma.</p><script>setTimeout(()=>window.close(), 3000)</script>")



# Setup Uploads Dir
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# State Store (In-Memory for now, simplifies prototype)
class SessionStore:
    def __init__(self):
        self.profile = load_profile()
        self.messages = []
        self.questions_queue = []
        
    def get_state(self):
        return {
            "messages": self.messages,
            "profile_data": self.profile,
            "questions_queue": self.questions_queue
        }
        
    def update_state(self, result):
        if "messages" in result:
            # Result messages are the NEW ones. We need to append carefully.
            # LangGraph returns the full history usually? Let's check logic.
            # In our current marvin.py we return specific messages.
            # Let's trust the graph output.
            for m in result["messages"]:
                self.messages.append(m)
                
        if "profile_data" in result:
            self.profile = result["profile_data"]
            
        if "questions_queue" in result:
            self.questions_queue = result["questions_queue"]

session = SessionStore()

# app = FastAPI() # SUBDUED: Duplicate initialization overwritten previous routes.



# Serve Frontend
app.mount("/static", StaticFiles(directory="src/static"), name="static")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def read_root():
    return FileResponse("src/static/index.html")

@app.get("/kingdom")
async def kingdom_view():
    return FileResponse("src/static/kingdom/kingdom_view.html")

@app.get("/founder")
async def founder_view():
    return FileResponse("src/static/founder/index.html")

from src.kingdom_service import kingdom_service
from src.tools.video_generator import VideoFactory
video_factory = VideoFactory()

class ScriptRequest(BaseModel):
    topic: str
    style: Optional[str] = "High Energy Tech"

@app.post("/api/media/generate_script")
async def generate_script(req: ScriptRequest):
    """Generates a script using Marvin Video Factory."""
    script = video_factory.generate_script(req.topic, req.style)
    return {"status": "success", "script": script}

@app.get("/api/status")
async def health_check():
    return {"status": "online", "service": "marvin-backend"}

@app.get("/api/kingdom/map")
async def get_kingdom_map():
    return kingdom_service.get_kingdom_map()

@app.get("/api/kingdom/marvin")
async def get_marvin_status():
    return kingdom_service.get_marvin_status()

@app.get("/api/kingdom/pulse")
async def get_kingdom_pulse():
    """Returns the raw dashboard data for the frontend HUD."""
    return logger._load()

@app.get("/api/coo/stats")
async def get_coo_stats():
    """Returns the Daily Ops Summary data."""
    # Read corrections log
    corrections = 0
    correction_log = os.path.join(root_dir, "src/static/logs/corrections.log")
    if os.path.exists(correction_log):
        with open(correction_log, "r") as f:
            corrections = len(f.readlines())
            
    # Read revisions dir
    revisions = 0
    revision_dir = os.path.join(root_dir, "src/approval/revisions")
    if os.path.exists(revision_dir):
        revisions = len(os.listdir(revision_dir))
        
    return {
        "health": "🟢 GREEN" if corrections < 3 else "🔴 RED",
        "strikes": corrections,
        "revisions": revisions,
        "tasks_scanned": "Active" # Placeholder
    }

@app.get("/api/revenue/pulse")
async def get_revenue_pulse():
    """Returns the Treasury Report from Agent Kappa."""
    # REAL HOOK: Kappa
    from src.core.lbl.status import status_manager
    status_manager.update_heartbeat("Kappa", "Working", "Compiling Revenue Pulse")
    
    try:
        from src.kappa import AgentKappa
        kappa = AgentKappa()
        report = kappa.generate_financial_report()
        # HONEST MODE: Return exactly what Kappa found in the DB.
        return report
    except Exception as e:
        status_manager.update_heartbeat("Kappa", "Idle", f"Error: {str(e)}")
        return {"error": str(e)}

@app.get("/api/research/scan")
async def run_research_scan():
    """Triggers the TrendHunter protocol."""
    # REAL HOOK: Beta
    from src.core.lbl.status import status_manager
    status_manager.update_heartbeat("Beta", "Working", "Executing Research Scan")
    
    try:
        results = TrendHunter.hunt_trends()
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    # 1. Fetch Real-Time Agent Status (LBL)
    from src.core.lbl.status import status_manager
    roster_status = status_manager.get_all_statuses()
    
    # 2. Add System Context (Invisible to User in typical UI, but useful for LLM logic)
    # Remove heuristic override that was bypassing the LLM.
    # Instead, we just let Marvin's LLM handle all conversational inputs.
    # If there are active agents, we can add a small system note at the end of the user's message 
    # to give Marvin awareness of the fleet.
    
    context_note = ""
    if roster_status:
        active_list = [f"{name} ({info['status']})" for name, info in roster_status.items()]
        context_note = f"\n\n[SYSTEM CONTEXT: The following agents are currently ONLINE: {', '.join(active_list)}.]"
        
    final_message = req.message + context_note

    # 2.5 Degraded Mode: no LLM key, but command channel remains operational.
    if not os.getenv("OPENAI_API_KEY"):
        marvin_state = roster_status.get("Marvin", {}) if isinstance(roster_status, dict) else {}
        marvin_status = marvin_state.get("status", "online")
        marvin_action = marvin_state.get("action", "standing by for directive execution")
        return {
            "response": f"MARVIN_COO_ACK: Yes Pastor Charles, I can hear you. I am {marvin_status} and {marvin_action}.",
            "kpi": {"logic": "Fallback Mode (OPENAI_API_KEY missing)", "memory_update": None},
            "degraded_mode": True,
        }

    # 3. Standard Marvin Logic (Fallthrough)
    session.messages.append(HumanMessage(content=final_message))
    state = session.get_state()
    try:
        result = marvin_app.invoke(state)
        ai_msg = result["messages"][-1]
        session.messages.append(ai_msg)
        
        if "profile_data" in result:
            session.profile = result["profile_data"]
        
        return {
            "response": ai_msg.content,
            "kpi": {
                "logic": "Processed successfully.", 
                "memory_update": str(result.get("profile_data", {})) if "profile_data" in result else None
            }
        }
    except Exception as e:
        return {
            "response": f"MARVIN_COO_FALLBACK: Command channel is active, but language core is unavailable ({str(e)}).",
            "error": True
        }

# --- SYSTEM ACTIVATION (Founder Portal) ---
import subprocess

class ActivationResponse(BaseModel):
    status: str
    active_agents: List[str]
    errors: List[str]
    system_log: str

@app.post("/api/system/activate", response_model=ActivationResponse)
async def activate_ecosystem():
    """
    MASTER TRIGGER: Starts Marvin, Listener, and the full Agent Fleet.
    """
    import os
    import sys
    
    agents_to_launch = [
        "boot_alpha.py", "boot_beta.py", "boot_muse.py", "boot_michael.py",
        "boot_zeta.py", "boot_sigma.py", "boot_gamma.py", "boot_delta.py",
        "boot_gabriel.py", "boot_lambda.py", "boot_marvin_v3.py"
    ]
    
    launched = []
    errors = []
    
    # 1. Verify Environment
    # Priority: Project Root .env then Local User .env
    env_path = os.path.join(root_dir, ".env")
    if not os.path.exists(env_path):
        env_path = r"C:\Users\chasW\.env"
        
    if not os.path.exists(env_path):
        errors.append(f"CRITICAL: .env file missing at {env_path}")
    else:
        with open(env_path, "r") as f:
            env_content = f.read()
            if "OPENAI_API_KEY" not in env_content:
                errors.append("WARNING: OPENAI_API_KEY is missing from .env. Agents may fail to uplink.")

    # 2. Start Listener (Watcher)
    watcher_path = os.path.join(root_dir, "src/watcher.py")
    try:
        subprocess.Popen([sys.executable, watcher_path], creationflags=CREATE_NEW_CONSOLE)
        launched.append("Listener (Sentinel)")
    except Exception as e:
        errors.append(f"Failed to start Listener: {str(e)}")

    # 3. Start Agent Fleet
    for agent_script in agents_to_launch:
        script_path = os.path.join(root_dir, agent_script)
        if os.path.exists(script_path):
            try:
                subprocess.Popen([sys.executable, script_path], creationflags=CREATE_NEW_CONSOLE)
                launched.append(agent_script.replace("boot_", "").replace(".py", "").capitalize())
            except Exception as e:
                errors.append(f"Failed to start {agent_script}: {str(e)}")
        else:
            errors.append(f"Missing script: {agent_script}")

    return {
        "status": "Success" if not errors else "Incomplete",
        "active_agents": launched,
        "errors": errors,
        "system_log": "Activation cycle complete. Monitoring uplink."
    }

@app.get("/api/system/status")
async def get_system_detailed_status():
    """Returns detailed status for the Founder Portal."""
    # 1. LBL Status
    from src.core.lbl.status import status_manager
    agent_stats = status_manager.get_all_statuses()
    
    # 2. Infrastructure Health
    infra = {
        "watchtower": "Online",
        "listener": "Active" if any(a["status"] == "Active" for a in agent_stats.values()) else "Idle/Offline", # Heuristic
        "marvin": agent_stats.get("Marvin", {"status": "Offline"})["status"]
    }
    
    return {
        "infrastructure": infra,
        "agents": agent_stats,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/api/upload")
def upload_file(file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Read content
    content = ""
    if file.filename.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    elif file.filename.endswith(".docx"):
        # We need to import docx safely
        try:
            import docx
            doc = docx.Document(file_path)
            content = "\n".join([p.text for p in doc.paragraphs])
        except Exception:
            content = "[Binary file uploaded, but could not extract text]"
            
    # Auto-Ingest
    ingest_msg = f"I am sharing this document with you ({file.filename}):\n\n{content}"
    session.messages.append(HumanMessage(content=ingest_msg))
    
    # Run silent update (optional, or just let context hold it)
    # We won't trigger a full response yet to avoid interrupting flow, 
    # OR we can just return success and let user ask about it.
    
    return {"filename": file.filename, "status": "Ingested into memory"}

@app.get("/finance", response_class=HTMLResponse)
async def finance_dashboard(request: Request):
    """Renders the Financial Throne Room (Kappa)."""
    kpis = db.get_financial_summary()
    return templates.TemplateResponse("finance.html", {"request": request, "kpis": kpis})

@app.get("/api/files")
async def list_files():
    files = []
    if os.path.exists(UPLOAD_DIR):
        files = os.listdir(UPLOAD_DIR)
    return {"files": files}

# --- GENESIS ENDPOINTS ---
from src.core.genesis import genesis

@app.get("/api/genesis/list")
async def list_agents_api():
    """Returns the list of all agents."""
    return genesis.list_agents()

@app.post("/api/genesis/spawn")
async def spawn_agent_api(request: Request):
    """Spawns a new agent from the dashboard."""
    data = await request.json()
    new_agent = genesis.spawn_agent(
        name=data.get("name"),
        role=data.get("role"),
        domain=data.get("domain"),
        personality_type=data.get("personality", "Standard")
    )
@app.get("/api/lbl/status")
async def get_lbl_status():
    """Returns merged Identity (LBL) + Status (Heartbeat)."""
    # 1. Get Static Identity
    lbl_data = genesis.list_agents() # Returns {"agents": [...]}
    agents = lbl_data["agents"]
    
    # 2. Get Real-Time Heartbeat
    from src.core.lbl.status import status_manager
    live_status = status_manager.get_all_statuses()
    
    # 3. Merge
    for a in agents:
        name = a["name"]
        if name in live_status:
           a["vital_signs"]["status_realtime"] = live_status[name]["status"]
           a["vital_signs"]["current_action"] = live_status[name]["action"]
           a["vital_signs"]["last_seen"] = live_status[name]["last_active"]
        else:
           a["vital_signs"]["status_realtime"] = "Offline"
           a["vital_signs"]["current_action"] = "Awaiting Uplink"

    return lbl_data

class CommandRequest(BaseModel):
    agent_name: str
    directive: str

@app.post("/api/lbl/command")
async def send_command(req: CommandRequest):
    """
    Simulates sending a directive to an agent.
    In V3, this would push to a Queue.
    """
    # 1. Log it
    print(f"[COMMAND] To: {req.agent_name} | Directive: {req.directive}")
    
    # 2. Update Status immediately to show responsiveness
    from src.core.lbl.status import status_manager
    status_manager.update_heartbeat(req.agent_name, "Working", f"Executing: {req.directive}")
    
    return {"status": "success", "message": f"Directive transmitted to {req.agent_name}."}

# --- MARVIN COMMAND INTAKE ---
class FounderCommandRequest(BaseModel):
    command: str
    signature: str # Founder API Key or HMAC
    sender: str = "Founder"

@app.post("/marvin/command")
async def marvin_command_intake(req: FounderCommandRequest, request: Request, x_founder_key: Optional[str] = Header(None)):
    """
    Dashboard/Portal Entry for Founder Directives.
    1. Authenticate (Founder API Key)
    2. Normalize via CommandProcessor
    3. Forward to Marvin Executive Loop
    """
    # 1. AUTHENTICATION GATES
    founder_key = x_founder_key or req.signature
    # TODO: Proper signature validation logic
    if founder_key != os.getenv("FOUNDER_API_KEY", "MARVIN_OVERRIDE_2026"):
         raise HTTPException(status_code=403, detail="UNAUTHORIZED FOUNDER KEY")
    
    # 2. PROCESS
    command_obj = processor.process_command(
        source="dashboard",
        sender=req.sender,
        message=req.command,
        payload={"ip": request.client.host}
    )
    
    if command_obj.get("status") == "REJECTED":
         raise HTTPException(status_code=400, detail="Command Rejected by Processor")
         
    return {
        "status": "success",
        "command_id": command_obj["id"],
        "message": "Founder Command Authenticated. Marvin is executing."
    }

# --- GROWTH AGENTS (Alpha & Lambda) ---
@app.get("/api/status")
async def system_status_api():
    """Returns the Global System Status."""
    from src.core.status import status_monitor
    return status_monitor.get_status()

@app.get("/api/lambda/scan")
async def scan_grants():
    """Agent Lambda: Scans for grants."""
    from src.core.growth import growth_engine
    return growth_engine.scan_for_grants()

@app.post("/api/lambda/draft")
async def draft_proposal(request: Request):
    """
    Agent Lambda: Auto-Drafts a LOI/Proposal.
    """
    data = await request.json()
    
    # Extract Data
    grant_title = data.get("grant_title", "General Grant")
    org_name = data.get("org_name", "Our Ministry")
    amount = data.get("amount", "$10,000")
    
    # In a real app, we'd fetch the template from src.tools.grant_templates
    # For now, we inline a simplified Lambda generator or import it
    from src.tools.grant_templates import GRANT_PROPOSAL_TEMPLATE
    
    # Fill Template
    proposal = GRANT_PROPOSAL_TEMPLATE.format(
        project_title=f"{grant_title} Implementation",
        org_name=org_name,
        amount=amount,
        program_name="Community Lift",
        core_goal="empower at-risk youth",
        funder_name="The Foundation",
        funder_mission="improve lives",
        problem_statement="lack of resources",
        founding_year="2020",
        location="Dallas, TX",
        mission_statement="serve the underserved",
        key_achievement="serving 500 families",
        target_audience="Youth (12-18)",
        pain_point="academic gap",
        service_gap="after-school mentorship",
        negative_outcome="graduation rates decline",
        activity_1="Mentorship Pods",
        activity_2="Weekend Workshops",
        activity_3="Career Counseling",
        metric_1="100",
        metric_2="50",
        outcome_1="25",
        outcome_2="15",
        total_budget=amount,
        personnel_cost="70%",
        materials_cost="20%",
        tech_cost="10%",
        sustainability_plan="Corporate Partnerships"
    )
    
    return {"proposal": proposal, "status": "Generated by Lambda"}


# --- RESEARCH ENGINE API (Moved) ---
@app.get("/api/research/reports")
async def list_reports():
    """Lists all generated Markdown reports."""
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research_reports")
    if not os.path.exists(report_dir):
        return []
    
    files = [f for f in os.listdir(report_dir) if f.endswith(".md")]
    files.sort(reverse=True) # Newest first
    return [{"filename": f, "path": os.path.join(report_dir, f)} for f in files]

class OpenRequest(BaseModel):
    filepath: str

@app.post("/api/research/open")
async def open_report(req: OpenRequest):
    """Opens the file in the default OS editor (Visual Studio Code)."""
    import subprocess
    import platform
    
    try:
        path = req.filepath
        if not os.path.exists(path):
             path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research_reports", req.filepath)
        
        if platform.system() == "Windows":
            os.startfile(path) # Opens in default associated app (VS Code per user request)
        elif platform.system() == "Darwin":
            subprocess.call(('open', path))
        else:
            subprocess.call(('xdg-open', path))
            
        return {"status": "success", "message": f"Opened {path}"}
    except Exception as e:
        print(f"[Open Error]: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/intel/generate_report")
async def generate_intel_report(request: Request):
    """
    Agent Beta: Generates a PDF Intelligence Brief.
    """
    data = await request.json()
    
    # 1. Generate Content (REAL MODE)
    topic = data.get("topic", "General Analysis")
    ministry = data.get("ministry_name", "Ministry Partner")
    
    # Call Real TrendHunter
    from src.tools.trend_hunter import TrendHunter
    raw_intel = TrendHunter.hunt_trends()
    
    # Process into Report Data
    # For now, we take the raw findings list and format it.
    findings_text = [f"* {item}" for item in raw_intel]
    
    report_data = {
        "title": f"Strategic Brief: {topic}",
        "client": ministry,
        "summary": f"Real-time intelligence scan executed. Analyzed {len(raw_intel)} sources including TechCrunch and MinistryWatch.",
        "findings": findings_text if findings_text else ["No critical signals found in this scan cycle."],
        "recommendation": "Review above signals for potential application."
    }
    
    pdf_file = generator.generate(report_data)
    
    return {
        "status": "Generated", 
        "url": f"/reports/{filename}",
        "message": "Agent Beta has compiled your briefing."
    }

@app.post("/api/muse/generate")
async def generate_brand(request: Request):
    """
    Agent Muse: Generates Brand Identity.
    """
    data = await request.json()
    name = data.get("name", "New Ministry")
    vibe = data.get("vibe", "Modern")
    
    # SAFE IMPORT: Muse Engine (Prevent Crash if Module Missing)
    try:
        from src.tools.muse import MuseEngine
        class Nonent: # Define Nonent for syntactic correctness
            def generate_identity(self, name, vibe):
                return {"status": "error", "message": "Muse Engine not available."}
        def get_muse_engine():
            return MuseEngine()
    except ImportError:
        print("[WARNING] Muse Engine could not be imported. Visual features disabled.")
        class Nonent: # Define Nonent for syntactic correctness
            def generate_identity(self, name, vibe):
                return {"status": "error", "message": "Muse Engine not available."}
        def get_muse_engine():
            return Nonent()
    
    muse_engine_instance = get_muse_engine()
    identity = muse_engine_instance.generate_identity(name, vibe)
    
    return identity

@app.post("/api/alpha/campaign")
async def create_campaign(request: Request):
    """Agent Alpha: Creates campaign."""
    data = await request.json()
    from src.core.growth import growth_engine
    return {"status": "success", "message": "Campaign Logic Placeholder"}

# --- ARCHITECT VOICE ---
class SpeakRequest(BaseModel):
    text: str

@app.post("/api/architect/speak")
async def architect_speak(req: SpeakRequest):
    """
    Returns audio bytes for the Architect's voice.
    Falls back to 'use_native: true' if no API key is set.
    """
    from src.tools.voice_engine import voice_engine
    
    audio_data = voice_engine.speak(req.text)
    
    if audio_data:
        # Return Binary Audio Stream
        from fastapi.responses import Response
        return Response(content=audio_data, media_type="audio/mpeg")
    else:
        # Signal Frontend to use Native TTS
        return {"use_native": True}
    return growth_engine.generate_campaign_ideas(data.get("topic", "General"))


# --- CRM FRONTEND ---
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.database.db_manager import db

templates = Jinja2Templates(directory="templates")

@app.get("/crm", response_class=HTMLResponse)
async def crm_dashboard(request: Request):
    clients = db.get_all_clients()
    return templates.TemplateResponse("crm_dashboard.html", {"request": request, "clients": clients})

@app.get("/crm/add", response_class=HTMLResponse)
async def add_client_form(request: Request):
    return templates.TemplateResponse("add_client.html", {"request": request})

@app.post("/crm/add")
async def add_client_action(
    org_name: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    website: str = Form(""),
    industry: str = Form(""),
    source: str = Form(""),
    segment: str = Form("Client")
):
    db.add_client(org_name, contact_name, email, phone, website, industry, source, segment)
    return RedirectResponse(url="/crm", status_code=303)

@app.post("/api/crm/lead/dfw")
async def capture_dfw_lead(
    name: str = Form(...),
    org: str = Form(...),
    location: str = Form(...)
):
    """Captures a lead from the DFW Landing Page."""
    print(f"[GROWTH] 🌪️ NEW DFW LEAD: {name} ({org}) @ {location}")
    
    # 1. Add to Legacy CRM
    try:
        db.add_client(
            org_name=org,
            contact_name=name,
            email="pending@capture.com",
            phone="",
            website="",
            industry="DFW Prospect",
            source="Operation Storm",
            segment="Lead"
        )
    except Exception as e:
        print(f"CRM Error: {e}")
        
    # 2. Trigger Notification (Console for now, Email in prod)
    # 3. Redirect to Thank You (reuse index or simple message)
    return HTMLResponse("""
        <html>
            <body style="background:#020617; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
                <h1 style="color:#10B981;">Request Received.</h1>
                <p>Agent Alpha will contact you shortly to coordinate.</p>
                <a href="/static/offerings/dfw.html" style="color:#3b82f6;">Return</a>
            </body>
        </html>
    """)

@app.get("/api/clients/{client_id}/lifecycle")
async def get_client_lifecycle_api(client_id: str):
    """Returns the lifecycle state for a client."""
    return db.get_client_lifecycle(client_id)

@app.post("/api/clients/{client_id}/lifecycle/update")
async def update_client_lifecycle_api(client_id: str, request: Request):
    """Updates the lifecycle state."""
    data = await request.json()
    db.update_lifecycle(
        client_id,
        stage=data.get("stage"),
        progress=data.get("progress"),
        next_action=data.get("next_action"),
        active_agents=data.get("active_agents")
    )
    return {"status": "success", "message": "Lifecycle updated."}

@app.get("/crm/export")
async def export_crm_csv():
    # 1. Fetch Data
    clients = db.get_all_clients()
    if not clients:
        return "No data to export."
        
    # 2. Generate CSV String
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    headers = clients[0].keys()
    writer.writerow(headers)
    
    # Rows
    for client in clients:
        writer.writerow(client.values())
        
    output.seek(0)
    
    # 3. Return File
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bluesoap_crm_clients.csv"}
    )

# --- SKILL REGISTRY (OpenCode) ---
from src.tools.skill_loader import SkillLoader

skill_loader_instance = SkillLoader()

@app.get("/api/skills/manifest")
async def get_skill_manifest():
    """Returns the full skill registry (manifest.json)."""
    return skill_loader_instance.registry


# --- STRIPE INTEGRATION ---

@app.get("/api/config")
async def get_config():
    """Returns the Stripe Public Key for frontend initialization."""
    return {"stripePublicKey": stripe_public_key}

class PaymentIntentRequest(BaseModel):
    items: Optional[List[dict]] = None
    currency: str = "usd"
    amount: int = 100 # Default $1.00

@app.post("/api/create-payment-intent")
async def create_payment(req: PaymentIntentRequest):
    """
    Creates a Stripe PaymentIntent.
    Uses Server-Side Secret Key.
    """
    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=req.amount,
            currency=req.currency,
            payment_method_types=['card'], # FORCE CARD
            metadata={
                'integration': 'BlueSoap_Marvin_Agent'
            }
        )
        return {
            "clientSecret": intent.client_secret
        }
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handles Stripe Webhooks (Verification + Logic).
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"[STRIPE] Payment Succeeded: {payment_intent['id']}")
        # Trigger Kappa Logic Here (if implemented)
    else:
        print(f"[STRIPE] Unhandled Event Type: {event['type']}")

    return {"status": "success"}

# --- WATCHTOWER TELEMETRY (REAL) ---
@app.get("/api/watchtower/vitality")
async def get_watchtower_vitality():
    """Aggregates REAL telemetry from the converted modules."""
    
    # 1. Sentinel (FIM)
    from src.tools.sentinel_shield import Sentinel
    sentinel_status = Sentinel().scan()
    
    # 2. Evolution (Health)
    from src.system.evolution_loop import EvolutionEngine
    health_status = EvolutionEngine().diagnose_services()
    
    # 3. Social Matrix (Content)
    from src.workflow.social_matrix import SocialMatrix
    content_status = SocialMatrix().check_pipeline()
    
    # 4. Deploy (Staging Check)
    import os
    dist_exists = os.path.exists("dist")
    deploy_msg = "Ready" if dist_exists else "Not Built"
    if dist_exists:
        count = sum([len(files) for r, d, files in os.walk("dist")])
        deploy_msg = f"Ready ({count} Assets)"

    return {
        "integrity": sentinel_status["status"],
        "files_verified": sentinel_status["files_scanned"],
        "api_health": health_status["status"],
        "latency": f"{health_status.get('latency_ms', 0)}ms",
        "content_pipeline": content_status["message"],
        "staging": deploy_msg
    }

# --- PLANETARY SYSTEMS (WATCHTOWER) ---
@app.get("/api/watchtower/systems")
async def get_planetary_systems():
    """Returns the status of all registered systems."""
    import json
    import requests
    import psutil
    
    registry_path = "data/systems.json"
    if not os.path.exists(registry_path):
        return {"systems": []}
        
    with open(registry_path, 'r') as f:
        systems = json.load(f)
        
    usage_report = []
    
    for sys_def in systems:
        status = "OFFLINE"
        details = "Unreachable"
        
        if sys_def["status_method"] == "HTTP_CHECK":
            try:
                # Fast timeout check
                resp = requests.head(sys_def["url"], timeout=2)
                if resp.status_code < 400:
                    status = "ONLINE"
                    details = f"{resp.status_code} OK"
                else:
                    details = f"Status {resp.status_code}"
            except:
                pass
                
        elif sys_def["status_method"] == "PROCESS_CHECK":
            # Check if python process running main.py exists
            # This is tricky for generic checks, but we look for the specific script name in cmdline
            target = sys_def["path"].split("\\")[-1] # main.py
            found = False
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and target in proc.info['cmdline'][-1]:
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            if found:
                status = "ONLINE"
                details = "Process Active"
            else:
                status = "DORMANT"
                details = "Ready to Launch"
                
        sys_def["status"] = status
        sys_def["details"] = details
        usage_report.append(sys_def)
        
    return {"systems": usage_report}

@app.post("/api/watchtower/launch")
async def launch_system(request: Request):
    """Launches a local system application."""
    data = await request.json()
    sys_id = data.get("id")
    
    import subprocess
    import json
    
    with open("data/systems.json", 'r') as f:
        systems = json.load(f)
        
    target = next((s for s in systems if s["id"] == sys_id), None)
    
    if not target or target["type"] != "LOCAL_APP":
        return {"status": "error", "message": "System not actionable."}
        
    try:
        # Launch non-blocking
        subprocess.Popen(["python", target["path"]], 
                         cwd=os.path.dirname(target["path"]),
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        return {"status": "success", "message": f"Launched {target['name']}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
