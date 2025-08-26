from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json
import logging
import io
import asyncio
try:
    from cerebras.cloud.sdk import Cerebras
except ImportError:
    Cerebras = None
    logging.warning("Cerebras SDK not available. Using mock responses.")

# Import export service
from services.export_service import ExportService
from services.auth_service import (
    auth_service, get_current_user, get_admin_user,
    UserCreate, UserUpdate, PasswordChange, LoginRequest, TokenResponse,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from services.kenya_law_service import kenya_law_db
from services.ai_prompt_service import advanced_prompt_engine
from services.document_template_service import document_template_manager, DocumentType, DocumentFormat
from services.realtime_service import realtime_service, notify_client_created, notify_ai_suggestion_ready, notify_document_generated

# Import session management
from services.session_service import session_manager, SessionInfo, SessionStatus
from middleware.session_middleware import (
    SessionMiddleware, SessionAPI, AuditLogger, cleanup_expired_sessions,
    get_current_session, admin_required, lawyer_or_admin, any_authenticated,
    read_clients_required, write_clients_required, delete_clients_required,
    manage_users_required, view_reports_required, export_data_required
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HNC Legal Questionnaire API",
    description="API for the HNC Legal Services digital questionnaire system",
    version="1.0.0"
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    excluded_paths=[
        "/",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/health",
        "/auth/login",
        "/auth/register",
        "/favicon.ico"
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Data Models
class Asset(BaseModel):
    type: str = Field(..., description="Type of asset")
    description: str = Field(..., description="Asset description")
    value: float = Field(..., ge=0, description="Asset value in KES")

class ClientBioData(BaseModel):
    fullName: str = Field(..., min_length=1, description="Client full name")
    maritalStatus: str = Field(..., description="Marital status")
    spouseName: Optional[str] = Field(None, description="Spouse name if married")
    spouseId: Optional[str] = Field(None, description="Spouse ID if married")
    children: str = Field("", description="Children details")

class FinancialData(BaseModel):
    assets: List[Asset] = Field(default_factory=list, description="List of assets")
    liabilities: str = Field("", description="Liabilities description")
    incomeSources: str = Field("", description="Income sources")

class EconomicContext(BaseModel):
    economicStanding: str = Field(..., description="Economic standing")
    distributionPrefs: str = Field("", description="Asset distribution preferences")

class ClientObjectives(BaseModel):
    objective: str = Field(..., description="Primary objective")
    details: str = Field("", description="Objective details")

class QuestionnaireData(BaseModel):
    bioData: ClientBioData
    financialData: FinancialData
    economicContext: EconomicContext
    objectives: ClientObjectives
    lawyerNotes: str = Field("", description="Lawyer notes")
    savedAt: Optional[str] = Field(None, description="Save timestamp")

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    token: str
    username: str
    loginTime: str

class AIProposalRequest(BaseModel):
    questionnaireData: QuestionnaireData
    distributionPrefs: str

class AIProposalResponse(BaseModel):
    suggestion: str
    legalReferences: List[str]
    consequences: List[str]
    nextSteps: List[str]

class ExportRequest(BaseModel):
    clientIds: List[str] = Field(..., description="List of client IDs to export")
    format: str = Field(..., description="Export format: 'pdf' or 'excel'")
    includeAIProposals: bool = Field(default=True, description="Include AI proposals in export")
    includeSummary: bool = Field(default=True, description="Include summary sheet for Excel exports")

class ExportResponse(BaseModel):
    downloadUrl: str
    filename: str
    expiresAt: str
    message: str

# Initialize services
export_service = ExportService(data_dir=os.getenv("DATA_DIR", "data"))

# Utility Functions
def get_data_file_path() -> str:
    """Get the path to the client data file"""
    data_dir = os.getenv("DATA_DIR", "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "client_data.json")

def get_client_file_path(client_id: str) -> str:
    """Get the path to a specific client's data file"""
    data_dir = os.getenv("DATA_DIR", "data")
    clients_dir = os.path.join(data_dir, "clients")
    os.makedirs(clients_dir, exist_ok=True)
    return os.path.join(clients_dir, f"{client_id}.json")

def get_proposals_file_path() -> str:
    """Get the path to the AI proposals file"""
    data_dir = os.getenv("DATA_DIR", "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "ai_proposals.json")

def generate_client_id(full_name: str) -> str:
    """Generate a unique client ID from full name and timestamp"""
    import hashlib
    import time
    
    # Create a unique identifier
    unique_string = f"{full_name.lower().replace(' ', '_')}_{int(time.time())}"
    # Generate short hash for uniqueness
    hash_obj = hashlib.md5(unique_string.encode())
    return f"client_{hash_obj.hexdigest()[:8]}"

def save_client_data(data: dict, client_id: str = None) -> tuple[bool, str]:
    """Save client data to individual client file and update master index"""
    try:
        # Generate client ID if not provided
        if not client_id:
            client_id = generate_client_id(data.get('bioData', {}).get('fullName', 'unknown'))
        
        # Save individual client file
        client_file_path = get_client_file_path(client_id)
        data['clientId'] = client_id
        data['lastUpdated'] = datetime.now().isoformat()
        
        with open(client_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Update master index
        update_client_index(client_id, data)
        
        logger.info(f"Client data saved successfully: {client_id}")
        return True, client_id
        
    except Exception as e:
        logger.exception(f"Failed to save client data: {e}")
        return False, ""

def update_client_index(client_id: str, data: dict) -> bool:
    """Update the master client index for search and retrieval"""
    try:
        index_file_path = os.path.join(os.getenv("DATA_DIR", "data"), "client_index.json")
        
        # Load existing index or create new
        if os.path.exists(index_file_path):
            with open(index_file_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {"clients": {}, "lastUpdated": datetime.now().isoformat()}
        
        # Update client entry in index
        bio_data = data.get('bioData', {})
        index["clients"][client_id] = {
            "fullName": bio_data.get('fullName', ''),
            "maritalStatus": bio_data.get('maritalStatus', ''),
            "objective": data.get('objectives', {}).get('objective', ''),
            "createdAt": data.get('savedAt', datetime.now().isoformat()),
            "lastUpdated": data.get('lastUpdated', datetime.now().isoformat()),
            "submittedBy": data.get('submittedBy', '')
        }
        index["lastUpdated"] = datetime.now().isoformat()
        
        # Save updated index
        with open(index_file_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        logger.exception(f"Failed to update client index: {e}")
        return False

def load_client_data(client_id: str = None) -> dict:
    """Load client data - specific client or all clients"""
    try:
        if client_id:
            # Load specific client
            client_file_path = get_client_file_path(client_id)
            if os.path.exists(client_file_path):
                with open(client_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        else:
            # Load client index for overview
            index_file_path = os.path.join(os.getenv("DATA_DIR", "data"), "client_index.json")
            if os.path.exists(index_file_path):
                with open(index_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"clients": {}, "lastUpdated": datetime.now().isoformat()}
            
    except Exception as e:
        logger.exception(f"Failed to load client data: {e}")
        return {}

def save_ai_proposal(client_id: str, proposal_data: dict) -> bool:
    """Save AI proposal with client association"""
    try:
        proposals_file = get_proposals_file_path()
        
        # Load existing proposals
        if os.path.exists(proposals_file):
            with open(proposals_file, "r", encoding="utf-8") as f:
                proposals = json.load(f)
        else:
            proposals = {"proposals": [], "lastUpdated": datetime.now().isoformat()}
        
        # Add new proposal
        proposal_entry = {
            "clientId": client_id,
            "proposalId": f"proposal_{len(proposals['proposals']) + 1:04d}",
            "generatedAt": datetime.now().isoformat(),
            "proposal": proposal_data
        }
        
        proposals["proposals"].append(proposal_entry)
        proposals["lastUpdated"] = datetime.now().isoformat()
        
        # Save updated proposals
        with open(proposals_file, "w", encoding="utf-8") as f:
            json.dump(proposals, f, ensure_ascii=False, indent=2)
        
        logger.info(f"AI proposal saved for client: {client_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to save AI proposal: {e}")
        return False

def search_clients(query: str) -> dict:
    """Search clients by name, objective, or other criteria"""
    try:
        index = load_client_data()
        clients = index.get("clients", {})
        
        if not query:
            return {"results": list(clients.values()), "total": len(clients)}
        
        query_lower = query.lower()
        results = []
        
        for client_id, client_info in clients.items():
            # Search in name, objective, marital status
            searchable_text = (
                f"{client_info.get('fullName', '').lower()} "
                f"{client_info.get('objective', '').lower()} "
                f"{client_info.get('maritalStatus', '').lower()}"
            )
            
            if query_lower in searchable_text:
                results.append({**client_info, "clientId": client_id})
        
        return {"results": results, "total": len(results), "query": query}
        
    except Exception as e:
        logger.exception(f"Failed to search clients: {e}")
        return {"results": [], "total": 0, "error": str(e)}

def load_ai_proposals(client_id: str) -> dict:
    """Load AI proposals for a specific client"""
    try:
        proposals_dir = os.path.join(os.getenv("DATA_DIR", "data"), "ai_proposals")
        os.makedirs(proposals_dir, exist_ok=True)
        proposals_file = os.path.join(proposals_dir, f"{client_id}.json")
        
        if os.path.exists(proposals_file):
            with open(proposals_file, "r", encoding="utf-8") as f:
                return json.load(f)
        
        return {"proposals": [], "lastUpdated": datetime.now().isoformat()}
        
    except Exception as e:
        logger.exception(f"Error loading AI proposals for {client_id}: {e}")
        return {"proposals": [], "error": str(e)}

def get_relevant_legal_references(client_context: Dict[str, Any]) -> List[str]:
    """Get relevant legal references from Kenya Law database"""
    try:
        # Get references from the Kenya Law database
        references = kenya_law_db.get_legal_references_for_context(client_context)
        
        # Format references for AI consumption
        formatted_refs = []
        for ref in references[:5]:  # Limit to top 5 most relevant
            formatted_ref = kenya_law_db.format_legal_reference_for_ai(ref)
            formatted_refs.append(formatted_ref)
        
        return formatted_refs
        
    except Exception as e:
        logger.error(f"Error retrieving legal references: {e}")
        # Fallback to basic references
        return [
            "Succession Act (Cap 160) - Section 5: Requirements for Valid Will",
            "Law of Succession Act - Section 32: Intestate Succession Rules",
            "Income Tax Act (Cap 470) - Section 3(2)(a): Inheritance Tax Exemption"
        ]

def build_ai_prompt(data: QuestionnaireData, distribution_prefs: str) -> str:
    """Build sophisticated AI prompt using advanced prompt engineering"""
    
    # Convert Pydantic model to dict for analysis
    client_data = {
        'bioData': data.bioData.dict(),
        'financialData': data.financialData.dict(),
        'economicContext': data.economicContext.dict(),
        'objectives': data.objectives.dict()
    }
    
    # Use advanced prompt engine for sophisticated prompt generation
    try:
        enhanced_prompt = advanced_prompt_engine.generate_enhanced_prompt(
            client_data, distribution_prefs
        )
        
        logger.info(f"Generated enhanced AI prompt for client: {data.bioData.fullName}")
        return enhanced_prompt
        
    except Exception as e:
        logger.error(f"Error generating enhanced prompt: {e}")
        # Fallback to basic prompt if advanced engine fails
        return build_fallback_prompt(data, distribution_prefs)

def build_fallback_prompt(data: QuestionnaireData, distribution_prefs: str) -> str:
    """Fallback prompt generation if advanced engine fails"""
    
    # Extract key information
    assets_summary = []
    total_value = 0
    for asset in data.financialData.assets:
        assets_summary.append(f"{asset.type}: {asset.description} (KES {asset.value:,})")
        total_value += asset.value
    
    assets_text = "; ".join(assets_summary) if assets_summary else "No assets specified"
    
    # Get basic legal references
    client_context = {
        'bioData': data.bioData.dict(),
        'financialData': data.financialData.dict(),
        'economicContext': data.economicContext.dict(),
        'objectives': data.objectives.dict()
    }
    
    legal_references = get_relevant_legal_references(client_context)
    legal_refs_text = "\n".join([f"- {ref}" for ref in legal_references])
    
    # Get tax implications
    tax_info = kenya_law_db.get_tax_implications(total_value)
    
    # Build fallback prompt
    prompt = f"""You are a legal AI assistant specializing in Kenyan law and estate planning.

**CLIENT PROFILE**:
- Name: {data.bioData.fullName}
- Marital Status: {data.bioData.maritalStatus}
- Children: {data.bioData.children or 'None specified'}
- Primary Objective: {data.objectives.objective}
- Asset Value: KES {total_value:,}

**RELEVANT LEGAL REFERENCES**:
{legal_refs_text}

**TAX IMPLICATIONS**:
- {tax_info['advice']}
- Applicable Law: {tax_info['applicable_law']}

**REQUEST**: Provide comprehensive legal guidance addressing:
1. Legal recommendations for achieving the stated objective
2. Specific consequences under Kenyan law
3. Required procedures and documentation
4. Risk mitigation strategies
5. Next steps with legal references

**Important**: Provide informational guidance only, not formal legal advice."""
    
    return prompt

async def generate_cerebras_ai_response(prompt: str) -> AIProposalResponse:
    """Generate AI response using Cerebras API"""
    try:
        if not Cerebras:
            raise ImportError("Cerebras SDK not available")
            
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not found in environment variables")
        
        client = Cerebras(api_key=api_key)
        
        response = client.chat.completions.create(
            model="llama3.1-70b",  # Use Cerebras's Llama model
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal AI assistant specializing in Kenyan law. Provide structured, informative responses about legal options and procedures. Always emphasize that your responses are informational and not formal legal advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        ai_content = response.choices[0].message.content
        
        # Parse the AI response into structured format
        return parse_ai_response(ai_content)
        
    except Exception as e:
        logger.exception(f"Error calling Cerebras API: {e}")
        # Fallback to enhanced mock response
        return generate_enhanced_mock_ai_response()

def parse_ai_response(ai_content: str) -> AIProposalResponse:
    """Parse AI response into structured format"""
    try:
        # For now, return the full content as suggestion
        # In production, you could implement more sophisticated parsing
        lines = ai_content.split('\n')
        
        suggestion = ai_content
        legal_references = [
            "Succession Act (Cap 160)",
            "Law of Succession Act",
            "Income Tax Act - Inheritance provisions"
        ]
        
        consequences = []
        next_steps = []
        
        # Simple parsing logic - look for numbered lists or bullet points
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('• '):
                if 'consequence' in line.lower() or 'implication' in line.lower():
                    consequences.append(line[2:])
                elif 'step' in line.lower() or 'action' in line.lower():
                    next_steps.append(line[2:])
        
        # Fallback if no structured content found
        if not consequences:
            consequences = [
                "Review all legal implications with qualified legal counsel",
                "Ensure compliance with Kenyan succession laws",
                "Consider tax implications for estate planning"
            ]
        
        if not next_steps:
            next_steps = [
                "Consult with a qualified Kenyan lawyer",
                "Gather all required documentation",
                "Review and finalize legal documents"
            ]
        
        return AIProposalResponse(
            suggestion=suggestion,
            legalReferences=legal_references,
            consequences=consequences,
            nextSteps=next_steps
        )
        
    except Exception as e:
        logger.exception(f"Error parsing AI response: {e}")
        return generate_enhanced_mock_ai_response()

def generate_enhanced_mock_ai_response() -> AIProposalResponse:
    """Generate enhanced mock AI response with better legal content"""
    return AIProposalResponse(
        suggestion=(
            "Based on Kenyan law analysis:\n\n"
            "**LEGAL RECOMMENDATIONS:**\n"
            "For will creation under the Succession Act (Cap 160), consider the following:\n\n"
            "1. **Will Requirements**: Must be in writing, signed by testator, and witnessed by two independent witnesses\n"
            "2. **Asset Distribution**: Direct beneficiary designation can minimize probate delays\n"
            "3. **Tax Considerations**: Estates over KES 5M may be subject to inheritance tax under current regulations\n"
            "4. **Probate Process**: Will must be registered and probated through the High Court\n\n"
            "**IMPORTANT**: This is informational guidance only. Consult qualified legal counsel for formal advice."
        ),
        legalReferences=[
            "Succession Act (Cap 160) - Sections 5-15 (Will requirements)",
            "Law of Succession Act - Probate procedures",
            "Income Tax Act - Schedule 7 (Inheritance tax)",
            "Registration of Documents Act (Cap 285)"
        ],
        consequences=[
            "Inheritance tax liability if estate value exceeds KES 5M threshold",
            "Probate process required - typically 6-12 months duration",
            "Will contestation risk if not properly witnessed or executed",
            "Potential delays if beneficiaries are minors (guardianship required)",
            "Asset freezing during probate period affecting business operations"
        ],
        nextSteps=[
            "Draft will document with qualified legal counsel specializing in succession law",
            "Arrange proper witnessing with two independent adult witnesses",
            "Register will with relevant authorities (optional but recommended)",
            "Prepare supporting documentation (asset valuations, beneficiary identification)",
            "Review and update will periodically (recommended every 3-5 years)",
            "Consider establishing family trust if estate value is substantial"
        ]
    )

# Update get_current_user to use new auth service (already imported from auth_service)
# The function is now imported from services.auth_service

# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "HNC Legal Questionnaire API is running", "version": "1.0.0"}

@app.get("/dashboard/statistics")
async def get_dashboard_statistics(
    session: SessionInfo = Depends(any_authenticated)
):
    """Get comprehensive dashboard statistics"""
    try:
        from services.client_service import client_service
        from datetime import datetime, timedelta
        import os
        from pathlib import Path
        
        # Get client statistics
        client_stats = client_service.get_client_statistics()
        
        # Count completed questionnaires (same as total clients for now)
        completed_questionnaires = client_stats.get('total_clients', 0)
        
        # Count AI proposals generated (check data/ai_proposals directory)
        ai_proposals_count = 0
        ai_proposals_dir = Path(os.getenv("DATA_DIR", "data")) / "ai_proposals"
        if ai_proposals_dir.exists():
            ai_proposals_count = len(list(ai_proposals_dir.glob("*.json")))
        
        # Count documents created (check generated_documents directory)
        documents_count = 0
        documents_dir = Path("generated_documents")
        if documents_dir.exists():
            documents_count = len(list(documents_dir.glob("*.html"))) + len(list(documents_dir.glob("*.pdf")))
        
        # Get active users count
        active_users_response = await get_active_users(session)
        active_users_count = active_users_response.get('total_active', 0)
        
        # Calculate system uptime (approximate from session start)
        # For now, we'll use a simple calculation
        uptime_days = 7  # Default placeholder
        
        # Get recent activity (last 5 client submissions)
        recent_activities = []
        clients_data = client_service.get_all_clients(5)  # Get last 5 clients
        
        for client_data in clients_data:
            bio_data = client_data.get('bioData', {})
            client_name = bio_data.get('fullName', 'Unknown Client')
            created_at = client_data.get('savedAt', '')
            
            if created_at:
                try:
                    # Parse the timestamp and calculate time ago
                    created_datetime = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_diff = datetime.now() - created_datetime.replace(tzinfo=None)
                    
                    if time_diff.days > 0:
                        time_ago = f"{time_diff.days} day{'s' if time_diff.days != 1 else ''} ago"
                    elif time_diff.seconds > 3600:
                        hours = time_diff.seconds // 3600
                        time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
                    else:
                        minutes = time_diff.seconds // 60
                        time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                    
                    recent_activities.append({
                        'type': 'questionnaire_completed',
                        'description': f'New questionnaire completed by {client_name}',
                        'time_ago': time_ago,
                        'color': 'green'
                    })
                except Exception as e:
                    logger.warning(f"Error parsing timestamp {created_at}: {e}")
        
        # Add some system activities
        if active_users_count > 0:
            recent_activities.append({
                'type': 'system_activity',
                'description': f'{active_users_count} user{"s" if active_users_count != 1 else ""} currently active',
                'time_ago': 'now',
                'color': 'blue'
            })
        
        # Sort by most recent and limit to 10
        recent_activities = recent_activities[:10]
        
        return {
            "statistics": {
                "totalClients": client_stats.get('total_clients', 0),
                "completedQuestionnaires": completed_questionnaires,
                "aiProposalsGenerated": ai_proposals_count,
                "documentsCreated": documents_count,
                "activeUsers": active_users_count,
                "systemUptime": f"{uptime_days} days",
                "recentClients": client_stats.get('recent_clients', 0)
            },
            "recent_activities": recent_activities,
            "clients_by_objective": client_stats.get('clients_by_objective', {}),
            "requested_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error getting dashboard statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get dashboard statistics"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request):
    """Authenticate user and create session"""
    try:
        # Extract client info
        ip_address = req.client.host if req.client else "unknown"
        user_agent = req.headers.get("user-agent", "unknown")
        
        # Authenticate user
        user_data = auth_service.authenticate_user(request.username, request.password)
        if not user_data:
            # Log failed attempt
            AuditLogger.log_access_attempt(
                ip_address, user_agent, request.username, 
                False, "Invalid credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create tokens
        token_data = {"sub": user_data["username"], "role": user_data["role"]}
        
        access_token = auth_service.create_access_token(token_data)
        refresh_token = auth_service.create_refresh_token(token_data)
        
        # Create session with session manager
        from services.auth_service import UserRole
        user_role = UserRole(user_data["role"])
        
        session = session_manager.create_session(
            user_id=user_data["id"],
            username=user_data["username"],
            role=user_role,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log successful login
        AuditLogger.log_access_attempt(
            ip_address, user_agent, request.username, True
        )
        AuditLogger.log_session_event(
            session, "session_created", 
            {"login_method": "password", "remember_me": getattr(request, "remember_me", False)}
        )
        
        # Prepare user data for response (exclude sensitive fields)
        user_response = {
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "role": user_data["role"],
            "last_login": user_data.get("last_login"),
            "session_id": session.session_id,
            "permissions": session.permissions
        }
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@app.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user data
        user_data = auth_service.get_user_by_username(username)
        if not user_data or not user_data.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        token_data = {"sub": username, "role": user_data["role"]}
        new_access_token = auth_service.create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Token refresh error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@app.post("/auth/logout")
async def logout(session: SessionInfo = Depends(get_current_session)):
    """Logout user and terminate session"""
    try:
        # Terminate current session
        success = session_manager.terminate_session(
            session.session_id, 
            SessionStatus.TERMINATED
        )
        
        if success:
            # Log session termination
            AuditLogger.log_session_event(
                session, "session_terminated", 
                {"logout_method": "user_initiated"}
            )
            
            logger.info(f"User {session.username} logged out successfully")
            return {
                "message": "Logout successful",
                "session_terminated": True
            }
        else:
            return {
                "message": "Logout completed",
                "session_terminated": False,
                "note": "Session may have already been terminated"
            }
            
    except Exception as e:
        logger.exception("Logout error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@app.post("/auth/register")
async def register_user(user_data: UserCreate, current_user: dict = Depends(get_admin_user)):
    """Register new user (admin only)"""
    try:
        new_user = auth_service.create_user(user_data)
        return {
            "message": "User created successfully",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "role": new_user.role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("User registration error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "first_name": current_user["first_name"],
            "last_name": current_user["last_name"],
            "role": current_user["role"],
            "is_active": current_user["is_active"],
            "created_at": current_user["created_at"],
            "last_login": current_user.get("last_login")
        }
    }

@app.put("/auth/profile")
async def update_profile(updates: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    try:
        updated_user = auth_service.update_user(current_user["username"], updates)
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "first_name": updated_user.first_name,
                "last_name": updated_user.last_name,
                "role": updated_user.role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Profile update error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@app.post("/auth/change-password")
async def change_password(password_change: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change user password"""
    try:
        success = auth_service.change_password(current_user["username"], password_change)
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Password change error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@app.get("/auth/users")
async def list_users(current_user: dict = Depends(get_admin_user)):
    """List all users (admin only)"""
    try:
        users = []
        users_dir = Path(os.getenv("DATA_DIR", "data")) / "users"
        
        for user_file in users_dir.glob("*.json"):
            try:
                with open(user_file, 'r') as f:
                    user_data = json.load(f)
                
                # Exclude password hash
                user_data.pop("password_hash", None)
                users.append(user_data)
                
            except Exception as e:
                logger.error(f"Error loading user file {user_file}: {e}")
        
        return {"users": users, "total": len(users)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("List users error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@app.post("/questionnaire/submit")
async def submit_questionnaire(
    data: QuestionnaireData, 
    current_user: dict = Depends(get_current_user)
):
    """Submit questionnaire data with enhanced persistence"""
    try:
        from services.client_service import client_service
        
        # Add timestamp and user info
        data.savedAt = datetime.now().isoformat()
        
        # Convert to dict and add metadata
        data_dict = data.dict()
        data_dict["submittedBy"] = current_user["username"]
        data_dict["submissionType"] = "questionnaire"
        
        # Save with enhanced persistence using ClientService
        success, message, file_path = client_service.save_client_data(data_dict)
        
        if success:
            # Extract client_id from the message
            client_id = message.split(": ")[-1] if ": " in message else data_dict.get('clientId', '')
            
            return {
                "message": "Questionnaire submitted successfully",
                "clientId": client_id,
                "savedAt": data.savedAt
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to save questionnaire data: {message}")
            
    except Exception as e:
        logger.exception("Error submitting questionnaire")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/questionnaire/data")
async def get_questionnaire_data(
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get questionnaire data - specific client or all clients index"""
    try:
        data = load_client_data(client_id)
        return {
            "data": data,
            "clientId": client_id,
            "requestedBy": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception("Error loading questionnaire data")
        raise HTTPException(status_code=500, detail="Failed to load questionnaire data")

@app.get("/clients")
async def get_all_clients_endpoint(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all clients with pagination and optional search"""
    try:
        from services.client_service import client_service
        
        if search:
            # Search clients
            clients_data = client_service.search_clients(search, limit)
        else:
            # Get all clients
            clients_data = client_service.get_all_clients(limit)
        
        # Transform data to match frontend expectations
        clients = []
        for client_data in clients_data:
            bio_data = client_data.get('bioData', {})
            contact_data = client_data.get('contactData', {})
            
            client = {
                'id': client_data.get('clientId', ''),
                'fullName': bio_data.get('fullName', ''),
                'maritalStatus': bio_data.get('maritalStatus', ''),
                'email': contact_data.get('emailAddress', ''),
                'phone': contact_data.get('phoneNumber', ''),
                'status': 'completed',
                'createdAt': client_data.get('savedAt', ''),
                'lastUpdated': client_data.get('lastUpdated', client_data.get('savedAt', ''))
            }
            clients.append(client)
        
        total = len(clients)
        
        return {
            "clients": clients,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit,
            "accessedBy": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception("Error getting clients")
        raise HTTPException(status_code=500, detail="Failed to get clients")

@app.get("/clients/search")
async def search_clients_endpoint(
    q: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Search clients by name, objective, or other criteria"""
    try:
        from services.client_service import client_service
        results_data = client_service.search_clients(q or "")
        
        # Transform data to match frontend expectations
        clients = []
        for client_data in results_data:
            bio_data = client_data.get('bioData', {})
            contact_data = client_data.get('contactData', {})
            
            client = {
                'id': client_data.get('clientId', ''),
                'fullName': bio_data.get('fullName', ''),
                'maritalStatus': bio_data.get('maritalStatus', ''),
                'email': contact_data.get('emailAddress', ''),
                'phone': contact_data.get('phoneNumber', ''),
                'status': 'completed',
                'createdAt': client_data.get('savedAt', ''),
                'lastUpdated': client_data.get('lastUpdated', client_data.get('savedAt', ''))
            }
            clients.append(client)
        
        return {
            "clients": clients,
            "total": len(clients),
            "searchedBy": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception("Error searching clients")
        raise HTTPException(status_code=500, detail="Failed to search clients")

@app.delete("/clients/{client_id}")
async def delete_client_endpoint(
    client_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific client"""
    try:
        from services.client_service import client_service
        success, message = client_service.delete_client(client_id)
        
        if success:
            return {
                "message": message,
                "clientId": client_id,
                "deletedBy": current_user["username"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting client {client_id}")
        raise HTTPException(status_code=500, detail="Failed to delete client")

@app.get("/clients/{client_id}")
async def get_client_details(
    client_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information for a specific client"""
    try:
        from services.client_service import client_service
        
        client_data = client_service.load_client_data(client_id)
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return {
            "clientData": client_data,
            "clientId": client_id,
            "accessedBy": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting client details for {client_id}")
        raise HTTPException(status_code=500, detail="Failed to get client details")

@app.post("/ai/generate-proposal", response_model=AIProposalResponse)
async def generate_ai_proposal(
    request: AIProposalRequest,
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI legal proposal using Cerebras API or enhanced mock"""
    try:
        # Build comprehensive prompt
        prompt = build_ai_prompt(request.questionnaireData, request.distributionPrefs)
        
        # Check if Cerebras API is available and configured
        api_key = os.getenv("CEREBRAS_API_KEY")
        
        if api_key and Cerebras:
            logger.info("Generating AI proposal using Cerebras API")
            try:
                response = await generate_cerebras_ai_response(prompt)
            except Exception as e:
                logger.error(f"Cerebras API call failed: {e}")
                logger.info("Falling back to enhanced mock response")
                response = generate_enhanced_mock_ai_response()
        else:
            logger.info("Cerebras API not configured, using enhanced mock response")
            response = generate_enhanced_mock_ai_response()
        
        # Save the proposal if client_id is provided
        if client_id:
            proposal_data = {
                "prompt": prompt,
                "response": response.dict(),
                "generatedBy": current_user["username"],
                "distributionPrefs": request.distributionPrefs
            }
            save_ai_proposal(client_id, proposal_data)
        
        return response
            
    except Exception as e:
        logger.exception("Error generating AI proposal")
        raise HTTPException(status_code=500, detail="Failed to generate AI proposal")

@app.get("/assets/summary")
async def get_assets_summary(current_user: dict = Depends(get_current_user)):
    """Get summary of client assets"""
    try:
        data = load_client_data()
        
        if not data or "financialData" not in data:
            return {"totalValue": 0, "assetCount": 0, "assets": []}
            
        assets = data["financialData"].get("assets", [])
        total_value = sum(asset.get("value", 0) for asset in assets)
        
        return {
            "totalValue": total_value,
            "assetCount": len(assets),
            "assets": assets
        }
    except Exception as e:
        logger.exception("Error getting assets summary")
        raise HTTPException(status_code=500, detail="Failed to get assets summary")

# Export Endpoints
@app.post("/export/pdf", response_model=ExportResponse)
async def export_client_pdf(
    request: ExportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Export client data to PDF format"""
    try:
        if request.format.lower() != 'pdf':
            raise HTTPException(status_code=400, detail="Invalid format for PDF export")
        
        if len(request.clientIds) != 1:
            raise HTTPException(status_code=400, detail="PDF export supports only single client")
        
        client_id = request.clientIds[0]
        client_data = load_client_data(client_id)
        
        if not client_data:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
        
        # Load AI proposal if requested
        if request.includeAIProposals:
            ai_proposals = load_ai_proposals(client_id)
            if ai_proposals:
                client_data['aiProposal'] = ai_proposals.get('proposals', [{}])[-1]  # Latest proposal
        
        # Generate PDF
        pdf_data = await export_service.export_client_to_pdf(client_data, request.includeAIProposals)
        
        # Save to file
        client_name = client_data.get('bioData', {}).get('fullName', 'Unknown_Client')
        filename = export_service.get_export_filename(client_name, 'pdf')
        file_path = await export_service.save_export_file(pdf_data, filename)
        
        # Calculate expiry time (24 hours from now)
        from datetime import timedelta
        expiry_time = datetime.now() + timedelta(hours=24)
        
        return ExportResponse(
            downloadUrl=f"/downloads/{filename}",
            filename=filename,
            expiresAt=expiry_time.isoformat(),
            message="PDF export generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error exporting to PDF")
        raise HTTPException(status_code=500, detail="Failed to generate PDF export")

@app.post("/export/excel", response_model=ExportResponse)
async def export_clients_excel(
    request: ExportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Export client data to Excel format"""
    try:
        if request.format.lower() not in ['excel', 'xlsx']:
            raise HTTPException(status_code=400, detail="Invalid format for Excel export")
        
        # Load client data for all requested clients
        clients_data = []
        missing_clients = []
        
        for client_id in request.clientIds:
            client_data = load_client_data(client_id)
            if client_data:
                # Load AI proposal if requested
                if request.includeAIProposals:
                    ai_proposals = load_ai_proposals(client_id)
                    if ai_proposals:
                        client_data['aiProposal'] = ai_proposals.get('proposals', [{}])[-1]
                
                clients_data.append(client_data)
            else:
                missing_clients.append(client_id)
        
        if not clients_data:
            raise HTTPException(status_code=404, detail="No valid clients found")
        
        if missing_clients:
            logger.warning(f"Some clients not found: {missing_clients}")
        
        # Generate Excel
        excel_data = await export_service.export_clients_to_excel(clients_data, request.includeSummary)
        
        # Save to file
        if len(clients_data) == 1:
            client_name = clients_data[0].get('bioData', {}).get('fullName', 'Single_Client')
        else:
            client_name = f"Multiple_Clients_{len(clients_data)}"
        
        filename = export_service.get_export_filename(client_name, 'xlsx')
        file_path = await export_service.save_export_file(excel_data, filename)
        
        # Calculate expiry time (24 hours from now)
        from datetime import timedelta
        expiry_time = datetime.now() + timedelta(hours=24)
        
        message = f"Excel export generated successfully for {len(clients_data)} clients"
        if missing_clients:
            message += f" (Note: {len(missing_clients)} clients not found)"
        
        return ExportResponse(
            downloadUrl=f"/downloads/{filename}",
            filename=filename,
            expiresAt=expiry_time.isoformat(),
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error exporting to Excel")
        raise HTTPException(status_code=500, detail="Failed to generate Excel export")

@app.get("/downloads/{filename}")
async def download_export_file(filename: str, current_user: dict = Depends(get_current_user)):
    """Download exported file"""
    try:
        file_path = export_service.exports_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        # Determine content type
        if filename.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename.endswith('.xlsx'):
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            media_type = 'application/octet-stream'
        
        # Read file data
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Create streaming response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error downloading file {filename}")
        raise HTTPException(status_code=500, detail="Failed to download file")

@app.get("/export/history")
async def get_export_history(current_user: dict = Depends(get_current_user)):
    """Get list of available export files"""
    try:
        export_files = []
        
        if export_service.exports_dir.exists():
            for file_path in export_service.exports_dir.glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    export_files.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "downloadUrl": f"/downloads/{file_path.name}"
                    })
        
        # Sort by creation time (newest first)
        export_files.sort(key=lambda x: x['created'], reverse=True)
        
        return {
            "files": export_files,
            "totalFiles": len(export_files),
            "requestedBy": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception("Error getting export history")
        raise HTTPException(status_code=500, detail="Failed to get export history")

@app.delete("/export/cleanup")
async def cleanup_expired_exports(current_user: dict = Depends(get_current_user)):
    """Clean up expired export files"""
    try:
        deleted_count = 0
        
        if export_service.exports_dir.exists():
            # Delete files older than 24 hours
            cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)  # 24 hours ago
            
            for file_path in export_service.exports_dir.glob("*"):
                if file_path.is_file() and file_path.stat().st_ctime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
        
        return {
            "message": f"Cleanup completed. {deleted_count} expired files removed.",
            "deletedFiles": deleted_count,
            "cleanedBy": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception("Error cleaning up exports")
        raise HTTPException(status_code=500, detail="Failed to cleanup expired exports")

# Kenya Law Database Endpoints
@app.get("/legal/search")
async def search_legal_references(
    query: str,
    areas: Optional[List[str]] = None,
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Search Kenya Law database for legal references"""
    try:
        if not query or len(query.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 3 characters long"
            )
        
        # Search the legal database
        results = kenya_law_db.search_legal_references(query, areas)
        
        return {
            "query": query,
            "areas_filter": areas,
            "total_results": len(results),
            "results": results,
            "searched_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error searching legal references: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search legal references"
        )

@app.get("/legal/references/{client_id}")
async def get_client_legal_references(
    client_id: str,
    session: SessionInfo = Depends(read_clients_required)
):
    """Get relevant legal references for a specific client"""
    try:
        # Load client data
        client_data = load_client_data(client_id)
        if not client_data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get relevant legal references
        references = kenya_law_db.get_legal_references_for_context(client_data)
        
        # Get tax implications
        total_assets = sum(
            asset.get('value', 0) 
            for asset in client_data.get('financialData', {}).get('assets', [])
        )
        tax_info = kenya_law_db.get_tax_implications(total_assets)
        
        return {
            "client_id": client_id,
            "client_name": client_data.get('bioData', {}).get('fullName', 'Unknown'),
            "total_asset_value": total_assets,
            "tax_implications": tax_info,
            "legal_references": references,
            "reference_count": len(references),
            "generated_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting client legal references: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get legal references for client"
        )

@app.get("/legal/tax-calculator")
async def calculate_tax_implications(
    asset_value: float,
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Calculate tax implications for given asset value"""
    try:
        if asset_value < 0:
            raise HTTPException(
                status_code=400,
                detail="Asset value must be non-negative"
            )
        
        tax_info = kenya_law_db.get_tax_implications(asset_value)
        
        return {
            "asset_value": asset_value,
            "tax_implications": tax_info,
            "calculated_by": session.username,
            "timestamp": datetime.now().isoformat(),
            "disclaimer": "This is an indicative calculation. Consult a tax advisor for accurate assessment."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating tax implications: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate tax implications"
        )

@app.get("/legal/database/stats")
async def get_legal_database_statistics(
    session: SessionInfo = Depends(admin_required)
):
    """Get Kenya Law database statistics (admin only)"""
    try:
        stats = kenya_law_db.get_database_statistics()
        
        return {
            "database_statistics": stats,
            "requested_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error getting database statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get database statistics"
        )

@app.get("/legal/areas")
async def get_legal_areas(
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Get available legal areas for filtering"""
    try:
        stats = kenya_law_db.get_database_statistics()
        areas = stats.get('coverage_areas', [])
        
        return {
            "legal_areas": sorted(areas),
            "total_areas": len(areas),
            "description": "Available legal areas for filtering search results",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error getting legal areas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get legal areas"
        )

# AI Prompt Engineering Endpoints
@app.post("/ai/analyze-client")
async def analyze_client_complexity(
    client_data: QuestionnaireData,
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Analyze client complexity and determine optimal AI approach"""
    try:
        # Convert to dict for analysis
        client_dict = {
            'bioData': client_data.bioData.dict(),
            'financialData': client_data.financialData.dict(),
            'economicContext': client_data.economicContext.dict(),
            'objectives': client_data.objectives.dict()
        }
        
        # Analyze client profile
        client_profile = advanced_prompt_engine.client_analyzer.analyze_client_profile(client_dict)
        
        # Determine optimal template
        template_type = advanced_prompt_engine._select_optimal_template(client_profile)
        
        return {
            "client_analysis": {
                "name": client_profile.name,
                "complexity_score": client_profile.complexity_score,
                "complexity_level": advanced_prompt_engine._get_complexity_level(client_profile.complexity_score),
                "risk_factors": client_profile.risk_factors,
                "legal_areas": [area.value for area in client_profile.legal_areas],
                "special_considerations": client_profile.special_considerations
            },
            "recommended_template": template_type,
            "analysis_summary": {
                "total_assets": client_profile.total_assets,
                "primary_risks": len(client_profile.risk_factors),
                "legal_areas_count": len(client_profile.legal_areas)
            },
            "analyzed_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error analyzing client complexity: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze client complexity"
        )

@app.get("/ai/prompt-templates")
async def get_available_prompt_templates(
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Get available AI prompt templates"""
    try:
        templates = advanced_prompt_engine.template_manager.list_available_templates()
        
        template_descriptions = {
            "basic_will": "Standard will creation and succession planning",
            "complex_trust": "Advanced trust structures and high net worth planning",
            "matrimonial_planning": "Family law and matrimonial property considerations",
            "business_succession": "Business succession and corporate planning",
            "tax_optimization": "Tax planning and optimization strategies"
        }
        
        template_info = [
            {
                "template_id": template,
                "description": template_descriptions.get(template, "Specialized legal planning template"),
                "complexity_level": "High" if "complex" in template else "Medium" if "business" in template or "tax" in template else "Standard"
            }
            for template in templates
        ]
        
        return {
            "available_templates": template_info,
            "total_templates": len(templates),
            "requested_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error getting prompt templates: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get prompt templates"
        )

@app.post("/ai/preview-prompt")
async def preview_ai_prompt(
    client_data: QuestionnaireData,
    distribution_prefs: str = "",
    template_override: Optional[str] = None,
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Preview the AI prompt that would be generated for a client"""
    try:
        # Generate the prompt
        if template_override:
            # Use specific template if requested
            client_dict = {
                'bioData': client_data.bioData.dict(),
                'financialData': client_data.financialData.dict(),
                'economicContext': client_data.economicContext.dict(),
                'objectives': client_data.objectives.dict()
            }
            
            template = advanced_prompt_engine.template_manager.get_template(template_override)
            client_profile = advanced_prompt_engine.client_analyzer.analyze_client_profile(client_dict)
            legal_references = kenya_law_db.get_legal_references_for_context(client_dict)
            tax_implications = kenya_law_db.get_tax_implications(client_profile.total_assets)
            
            context = advanced_prompt_engine._build_prompt_context(
                client_profile, legal_references, tax_implications
            )
            
            prompt = advanced_prompt_engine._format_prompt(
                template, context, client_dict, distribution_prefs
            )
        else:
            # Use automatic template selection
            prompt = build_ai_prompt(client_data, distribution_prefs)
        
        # Calculate prompt statistics
        word_count = len(prompt.split())
        char_count = len(prompt)
        
        return {
            "prompt_preview": prompt,
            "prompt_statistics": {
                "word_count": word_count,
                "character_count": char_count,
                "estimated_tokens": word_count * 1.3,  # Rough estimate
                "template_used": template_override or "auto-selected"
            },
            "client_info": {
                "name": client_data.bioData.fullName,
                "objective": client_data.objectives.objective
            },
            "generated_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error previewing AI prompt: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate prompt preview"
        )

# ============================================================================
# DOCUMENT TEMPLATE ENDPOINTS
# ============================================================================

@app.post("/documents/generate")
async def generate_document(
    request: Dict[str, Any],
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Generate a legal document based on client data and document type"""
    try:
        document_type_str = request.get('document_type')
        client_data = request.get('client_data', {})
        additional_data = request.get('additional_data', {})
        format_type_str = request.get('format', 'html')
        
        if not document_type_str:
            raise HTTPException(status_code=400, detail="Document type is required")
        
        # Validate document type
        try:
            document_type = DocumentType(document_type_str.lower())
        except ValueError:
            available_types = [dt.value for dt in DocumentType]
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid document type. Available types: {available_types}"
            )
        
        # Validate format type
        try:
            format_type = DocumentFormat(format_type_str.lower())
        except ValueError:
            available_formats = [df.value for df in DocumentFormat]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format type. Available formats: {available_formats}"
            )
        
        # Generate document
        result = document_template_manager.generate_document(
            document_type=document_type,
            client_data=client_data,
            additional_data=additional_data,
            format_type=format_type
        )
        
        if result.get('success'):
            result['generated_by'] = session.username
            result['timestamp'] = datetime.now().isoformat()
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Document generation failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate document")


@app.get("/documents/{document_id}")
async def get_document(
    document_id: str, 
    format: str = "html",
    session: SessionInfo = Depends(read_clients_required)
):
    """Retrieve a generated document by ID"""
    try:
        # Validate format
        try:
            format_type = DocumentFormat(format.lower())
        except ValueError:
            available_formats = [df.value for df in DocumentFormat]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Available formats: {available_formats}"
            )
        
        result = document_template_manager.get_document(document_id, format_type)
        
        if result.get('success'):
            result['accessed_by'] = session.username
            result['access_timestamp'] = datetime.now().isoformat()
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get('error', 'Document not found'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@app.get("/documents")
async def list_documents(
    client_name: str = None,
    session: SessionInfo = Depends(read_clients_required)
):
    """List all generated documents, optionally filtered by client name"""
    try:
        documents = document_template_manager.list_documents(client_name)
        return {
            "documents": documents,
            "total_count": len(documents),
            "filter_applied": client_name is not None,
            "requested_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    session: SessionInfo = Depends(write_clients_required)
):
    """Delete a generated document"""
    try:
        result = document_template_manager.delete_document(document_id)
        
        if result.get('success'):
            result['deleted_by'] = session.username
            result['deletion_timestamp'] = datetime.now().isoformat()
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get('error', 'Document not found'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@app.get("/documents/types")
async def get_document_types(
    session: SessionInfo = Depends(any_authenticated)
):
    """Get available document types and formats"""
    try:
        document_types = [{
            "value": dt.value,
            "name": dt.value.replace('_', ' ').title(),
            "description": _get_document_type_description(dt)
        } for dt in DocumentType]
        
        document_formats = [{
            "value": df.value,
            "name": df.value.upper(),
            "description": _get_format_description(df)
        } for df in DocumentFormat]
        
        return {
            "document_types": document_types,
            "document_formats": document_formats,
            "requested_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting document types: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document types")


def _get_document_type_description(document_type: DocumentType) -> str:
    """Get description for document type"""
    descriptions = {
        DocumentType.WILL: "Last Will and Testament for estate distribution",
        DocumentType.TRUST_DEED: "Trust deed for asset protection and management",
        DocumentType.POWER_OF_ATTORNEY: "Power of Attorney for legal representation",
        DocumentType.LEGAL_OPINION: "Professional legal opinion and analysis",
        DocumentType.ASSET_DECLARATION: "Comprehensive asset and liability declaration",
        DocumentType.SUCCESSION_CERTIFICATE: "Court application for succession certificate",
        DocumentType.MARRIAGE_CONTRACT: "Pre-nuptial or post-nuptial agreement",
        DocumentType.BUSINESS_SUCCESSION_PLAN: "Comprehensive business succession planning"
    }
    return descriptions.get(document_type, "Legal document")


def _get_format_description(format_type: DocumentFormat) -> str:
    """Get description for format type"""
    descriptions = {
        DocumentFormat.DOCX: "Microsoft Word document format",
        DocumentFormat.PDF: "Portable Document Format (read-only)",
        DocumentFormat.HTML: "Web-friendly HTML format",
        DocumentFormat.TXT: "Plain text format"
    }
    return descriptions.get(format_type, "Document format")


@app.post("/documents/preview")
async def preview_document(
    request: Dict[str, Any],
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Generate a preview of a document without saving it"""
    try:
        document_type_str = request.get('document_type')
        client_data = request.get('client_data', {})
        additional_data = request.get('additional_data', {})
        
        if not document_type_str:
            raise HTTPException(status_code=400, detail="Document type is required")
        
        # Validate document type
        try:
            document_type = DocumentType(document_type_str.lower())
        except ValueError:
            available_types = [dt.value for dt in DocumentType]
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid document type. Available types: {available_types}"
            )
        
        # Prepare template data (without saving)
        template_data = document_template_manager._prepare_template_data(
            document_type, client_data, additional_data
        )
        
        # Get legal references
        legal_references = document_template_manager._get_relevant_legal_references(
            document_type, client_data
        )
        template_data['legal_references'] = legal_references
        
        # Generate preview content
        if document_template_manager.jinja_env:
            content = document_template_manager._generate_with_jinja(document_type, template_data)
        else:
            content = document_template_manager._generate_with_basic_template(document_type, template_data)
        
        # Return preview (first 1000 characters)
        preview = content[:1000] + "..." if len(content) > 1000 else content
        
        return {
            "success": True,
            "document_type": document_type.value,
            "preview": preview,
            "full_length": len(content),
            "legal_references_count": len(legal_references),
            "previewed_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating document preview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate document preview")


@app.post("/documents/bulk-generate")
async def bulk_generate_documents(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    session: SessionInfo = Depends(lawyer_or_admin)
):
    """Generate multiple documents for a client in bulk"""
    try:
        client_data = request.get('client_data', {})
        document_types = request.get('document_types', [])
        additional_data = request.get('additional_data', {})
        format_type_str = request.get('format', 'html')
        
        if not client_data:
            raise HTTPException(status_code=400, detail="Client data is required")
        
        if not document_types:
            raise HTTPException(status_code=400, detail="At least one document type is required")
        
        # Validate document types
        validated_types = []
        for doc_type_str in document_types:
            try:
                validated_types.append(DocumentType(doc_type_str.lower()))
            except ValueError:
                available_types = [dt.value for dt in DocumentType]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid document type '{doc_type_str}'. Available types: {available_types}"
                )
        
        # Validate format
        try:
            format_type = DocumentFormat(format_type_str.lower())
        except ValueError:
            available_formats = [df.value for df in DocumentFormat]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format type. Available formats: {available_formats}"
            )
        
        # Start bulk generation in background
        task_id = f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        def bulk_generation_task():
            results = []
            for doc_type in validated_types:
                try:
                    result = document_template_manager.generate_document(
                        document_type=doc_type,
                        client_data=client_data,
                        additional_data=additional_data,
                        format_type=format_type
                    )
                    results.append({
                        "document_type": doc_type.value,
                        "success": result.get('success', False),
                        "document_id": result.get('document_id'),
                        "error": result.get('error')
                    })
                except Exception as e:
                    results.append({
                        "document_type": doc_type.value,
                        "success": False,
                        "error": str(e)
                    })
            
            # Save bulk generation results
            try:
                bulk_results_dir = Path("data/bulk_generation_results")
                bulk_results_dir.mkdir(parents=True, exist_ok=True)
                
                with open(bulk_results_dir / f"{task_id}.json", 'w') as f:
                    json.dump({
                        "task_id": task_id,
                        "client_name": client_data.get('bioData', {}).get('fullName', 'Unknown'),
                        "generated_by": session.username,
                        "started_at": datetime.now().isoformat(),
                        "completed_at": datetime.now().isoformat(),
                        "total_documents": len(validated_types),
                        "successful_documents": len([r for r in results if r['success']]),
                        "results": results
                    }, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save bulk generation results: {e}")
        
        background_tasks.add_task(bulk_generation_task)
        
        return {
            "task_id": task_id,
            "message": "Bulk document generation started",
            "document_types": [dt.value for dt in validated_types],
            "total_documents": len(validated_types),
            "client_name": client_data.get('bioData', {}).get('fullName', 'Unknown'),
            "initiated_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating bulk document generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate bulk document generation")


@app.get("/documents/bulk-status/{task_id}")
async def get_bulk_generation_status(
    task_id: str,
    session: SessionInfo = Depends(read_clients_required)
):
    """Get status of bulk document generation task"""
    try:
        bulk_results_dir = Path("data/bulk_generation_results")
        result_file = bulk_results_dir / f"{task_id}.json"
        
        if not result_file.exists():
            raise HTTPException(status_code=404, detail="Bulk generation task not found")
        
        with open(result_file, 'r') as f:
            results = json.load(f)
        
        results['accessed_by'] = session.username
        results['access_timestamp'] = datetime.now().isoformat()
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bulk generation status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get bulk generation status")

# Session Management Endpoints
@app.get("/session/info")
async def get_session_info(session: SessionInfo = Depends(get_current_session)):
    """Get current session information"""
    return await SessionAPI.get_current_session_info(session)

@app.post("/session/extend")
async def extend_session(extension_hours: int = 8, session: SessionInfo = Depends(get_current_session)):
    """Extend current session"""
    return await SessionAPI.extend_current_session(session, extension_hours)

@app.get("/session/list")
async def list_user_sessions(session: SessionInfo = Depends(get_current_session)):
    """List all sessions for current user"""
    return await SessionAPI.get_user_sessions(session)

@app.delete("/session/{session_id}")
async def terminate_specific_session(
    session_id: str, 
    session: SessionInfo = Depends(get_current_session)
):
    """Terminate a specific session"""
    return await SessionAPI.terminate_session(session, session_id)

@app.delete("/session/others")
async def terminate_other_sessions(session: SessionInfo = Depends(get_current_session)):
    """Terminate all other sessions for current user"""
    return await SessionAPI.terminate_other_sessions(session)

@app.get("/session/statistics")
async def get_session_statistics(session: SessionInfo = Depends(admin_required)):
    """Get session statistics (admin only)"""
    stats = session_manager.get_session_statistics()
    return {
        "statistics": stats,
        "timestamp": datetime.now().isoformat(),
        "requested_by": session.username
    }

@app.post("/session/cleanup")
async def manual_session_cleanup(
    background_tasks: BackgroundTasks,
    session: SessionInfo = Depends(admin_required)
):
    """Manually trigger session cleanup (admin only)"""
    background_tasks.add_task(cleanup_expired_sessions)
    return {
        "message": "Session cleanup task initiated",
        "initiated_by": session.username,
        "timestamp": datetime.now().isoformat()
    }

# Periodic session cleanup task
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks and real-time service on startup"""
    # Initialize real-time service
    await realtime_service.initialize()
    
    # Schedule periodic session cleanup
    import asyncio
    
    async def periodic_cleanup():
        while True:
            try:
                await asyncio.sleep(15 * 60)  # Run every 15 minutes
                cleaned_count = await cleanup_expired_sessions()
                if cleaned_count > 0:
                    logger.info(f"Automatically cleaned up {cleaned_count} expired sessions")
            except Exception as e:
                logger.error(f"Error in periodic session cleanup: {e}")
    
    # Start the cleanup task
    asyncio.create_task(periodic_cleanup())
    logger.info("Session management, real-time service, and periodic cleanup initialized")


# ============================================================================
# WEBSOCKET AND REAL-TIME ENDPOINTS
# ============================================================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication"""
    connection_id = None
    try:
        # For demo purposes, we'll use simple authentication
        # In production, you should validate the user via proper token authentication
        await websocket.accept()
        
        # Extract user info from query parameters or token
        query_params = dict(websocket.query_params)
        username = query_params.get('username', user_id)
        role = query_params.get('role', 'user')
        
        # Connect user to real-time service
        connection_id = await realtime_service.connect_user(
            websocket, user_id, username, role
        )
        
        # Main message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get('type') == 'user_activity':
                    await realtime_service.update_user_activity(
                        connection_id, message.get('data', {})
                    )
                
                elif message.get('type') == 'start_auto_save':
                    client_id = message.get('client_id')
                    interval = message.get('interval', 30)
                    if client_id:
                        await realtime_service.start_auto_save(
                            connection_id, client_id, interval
                        )
                
                elif message.get('type') == 'stop_auto_save':
                    await realtime_service.stop_auto_save(connection_id)
                
                elif message.get('type') == 'ping':
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }))
                
                # Update last activity
                await realtime_service.update_user_activity(
                    connection_id, {'last_message': datetime.now().isoformat()}
                )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Internal server error'
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # Cleanup connection
        if connection_id:
            await realtime_service.disconnect_user(connection_id)


@app.get("/realtime/active-users")
async def get_active_users(session: SessionInfo = Depends(any_authenticated)):
    """Get list of currently active users"""
    try:
        active_users = await realtime_service.get_active_users()
        return {
            "active_users": active_users,
            "total_active": len(active_users),
            "requested_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active users")


@app.post("/realtime/broadcast")
async def broadcast_message(
    request: Dict[str, Any],
    session: SessionInfo = Depends(admin_required)
):
    """Broadcast message to all connected users (admin only)"""
    try:
        message = request.get('message', '')
        priority = request.get('priority', 'medium')
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        from services.realtime_service import notify_system_alert, Priority
        
        # Map priority string to enum
        priority_map = {
            'low': Priority.LOW,
            'medium': Priority.MEDIUM,
            'high': Priority.HIGH,
            'urgent': Priority.URGENT
        }
        
        priority_enum = priority_map.get(priority.lower(), Priority.MEDIUM)
        
        await notify_system_alert(message, priority_enum)
        
        return {
            "message": "Broadcast sent successfully",
            "broadcast_message": message,
            "priority": priority,
            "sent_by": session.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


# Update existing endpoints to include real-time notifications

# Override the existing client submission endpoint to add real-time notifications
async def enhanced_save_client_data(data: dict, client_id: str = None, submitted_by: str = None) -> tuple[bool, str]:
    """Enhanced client data saving with real-time notifications"""
    try:
        success, saved_client_id = save_client_data(data, client_id)
        
        if success and submitted_by:
            # Send real-time notification
            client_name = data.get('bioData', {}).get('fullName', 'Unknown Client')
            await notify_client_created(saved_client_id, client_name, submitted_by)
        
        return success, saved_client_id
        
    except Exception as e:
        logger.error(f"Error in enhanced_save_client_data: {e}")
        return False, ""

# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)