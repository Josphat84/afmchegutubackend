# Backend directory router
# backend/app/routers/directory.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.supabase_client import supabase

router = APIRouter(prefix="/directory", tags=["directory"])

# =============== Pydantic Models ===============
class MemberBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None  # 'male', 'female', 'other'
    date_of_birth: Optional[date] = None
    id_number: Optional[str] = None
    profession: Optional[str] = None
    workplace: Optional[str] = None
    address: Optional[str] = None
    home_address: Optional[str] = None
    next_of_kin: Optional[str] = None
    spouse_name: Optional[str] = None
    parents: Optional[str] = None
    departments: List[str] = []
    positions: List[str] = []
    baptism_date: Optional[date] = None
    joined_date: Optional[date] = None

class MemberCreate(MemberBase):
    pass

class MemberUpdate(MemberBase):
    full_name: Optional[str] = None

class MemberResponse(BaseModel):
    id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    id_number: Optional[str] = None
    profession: Optional[str] = None
    workplace: Optional[str] = None
    address: Optional[str] = None
    home_address: Optional[str] = None
    next_of_kin: Optional[str] = None
    spouse_name: Optional[str] = None
    parents: Optional[str] = None
    departments: List[str] = []
    positions: List[str] = []
    baptism_date: Optional[str] = None
    joined_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# =============== Helper function to convert Supabase response ===============
def format_member(data: dict) -> dict:
    """Convert Supabase response to consistent format with proper date serialization"""
    if not data:
        return {}
    
    # Helper to convert any date/datetime to ISO string
    def to_iso_str(value):
        if value is None:
            return None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return str(value)
    
    return {
        "id": str(data.get("id", "")),
        "full_name": str(data.get("full_name", "")),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "gender": data.get("gender"),
        "date_of_birth": to_iso_str(data.get("date_of_birth")),
        "id_number": data.get("id_number"),
        "profession": data.get("profession"),
        "workplace": data.get("workplace"),
        "address": data.get("address"),
        "home_address": data.get("home_address"),
        "next_of_kin": data.get("next_of_kin"),
        "spouse_name": data.get("spouse_name"),
        "parents": data.get("parents"),
        "departments": data.get("departments") or [],
        "positions": data.get("positions") or [],
        "baptism_date": to_iso_str(data.get("baptism_date")),
        "joined_date": to_iso_str(data.get("joined_date")),
        "created_at": to_iso_str(data.get("created_at")),
        "updated_at": to_iso_str(data.get("updated_at")),
    }

# =============== Helper to convert date objects in request data ===============
def prepare_data_for_supabase(data: dict) -> dict:
    """Convert all date/datetime objects to ISO strings for Supabase"""
    prepared = {}
    for key, value in data.items():
        if value is None or value == "":
            prepared[key] = None
        elif isinstance(value, (date, datetime)):
            prepared[key] = value.isoformat()
        elif isinstance(value, list):
            prepared[key] = value
        else:
            prepared[key] = value
    return prepared

# =============== API Endpoints ===============

@router.get("/", response_model=List[MemberResponse])
async def get_members(
    search: Optional[str] = Query(None, description="Search by name, email, phone, profession, ID"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    department: Optional[str] = Query(None, description="Filter by department"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get all members with optional filtering"""
    try:
        query = supabase.table("members").select("*")

        # Apply filters
        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,"
                f"email.ilike.%{search}%,"
                f"phone.ilike.%{search}%,"
                f"profession.ilike.%{search}%,"
                f"id_number.ilike.%{search}%"
            )
        
        if gender:
            query = query.eq("gender", gender)
        
        if department:
            query = query.contains("departments", [department])
        
        if position:
            query = query.contains("positions", [position])

        # Pagination
        query = query.range(offset, offset + limit - 1).order("full_name")

        result = query.execute()
        
        if not result.data:
            return []
        
        return [format_member(item) for item in result.data]
    except Exception as e:
        print(f"Error in get_members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/count", response_model=int)
async def get_members_count(
    search: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
):
    """Get count of members matching filters"""
    try:
        query = supabase.table("members").select("*", count="exact", head=True)

        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,"
                f"email.ilike.%{search}%,"
                f"phone.ilike.%{search}%,"
                f"profession.ilike.%{search}%,"
                f"id_number.ilike.%{search}%"
            )
        
        if gender:
            query = query.eq("gender", gender)
        
        if department:
            query = query.contains("departments", [department])
        
        if position:
            query = query.contains("positions", [position])

        result = query.execute()
        return result.count if hasattr(result, 'count') else 0
    except Exception as e:
        print(f"Error in get_members_count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(member_id: str):
    """Get a single member by ID"""
    try:
        result = supabase.table("members").select("*").eq("id", member_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Member not found")
        
        return format_member(result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=MemberResponse, status_code=201)
async def create_member(member: MemberCreate):
    """Create a new member"""
    try:
        # Get the data from the request
        data = member.model_dump(exclude_unset=True)
        
        # Prepare data for Supabase (convert dates to strings)
        supabase_data = prepare_data_for_supabase(data)
        
        print(f"Sending to Supabase: {supabase_data}")  # Debug log
        
        # Insert into Supabase
        result = supabase.table("members").insert(supabase_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create member")
        
        # Format and return the response
        return format_member(result.data[0])
    except Exception as e:
        print(f"Error in create_member: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(member_id: str, member: MemberUpdate):
    """Update an existing member"""
    try:
        # Check if member exists
        existing = supabase.table("members").select("*").eq("id", member_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Get update data
        update_data = member.model_dump(exclude_unset=True)
        
        # Prepare data for Supabase (convert dates to strings)
        supabase_data = prepare_data_for_supabase(update_data)
        
        if not supabase_data:
            return format_member(existing.data[0])
        
        print(f"Updating with data: {supabase_data}")  # Debug log
        
        # Update in Supabase
        result = supabase.table("members").update(supabase_data).eq("id", member_id).execute()
        
        return format_member(result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_member: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{member_id}", status_code=204)
async def delete_member(member_id: str):
    """Delete a member"""
    try:
        result = supabase.table("members").delete().eq("id", member_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Member not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
async def get_member_stats():
    """Get overview statistics"""
    try:
        # Get all members (limit to 1000 for performance)
        result = supabase.table("members").select("*").limit(1000).execute()
        members = result.data if result.data else []
        
        total = len(members)
        male = sum(1 for m in members if m.get("gender") == "male")
        female = sum(1 for m in members if m.get("gender") == "female")
        other = sum(1 for m in members if m.get("gender") == "other")
        baptised = sum(1 for m in members if m.get("baptism_date") is not None)
        
        # Members with any family info
        with_family = sum(1 for m in members if 
                         m.get("next_of_kin") is not None or 
                         m.get("spouse_name") is not None or 
                         m.get("parents") is not None)
        
        return {
            "total": total,
            "male": male,
            "female": female,
            "other": other,
            "baptised": baptised,
            "with_family": with_family,
            "upcoming_birthdays": 0,
        }
    except Exception as e:
        print(f"Error in get_member_stats: {e}")
        return {
            "total": 0,
            "male": 0,
            "female": 0,
            "other": 0,
            "baptised": 0,
            "with_family": 0,
            "upcoming_birthdays": 0,
        }