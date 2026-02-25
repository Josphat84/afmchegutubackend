# Church equipment inventory register
# backend/app/routers/equipment.py

# Simple equipment router
# backend/app/routers/equipment.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.supabase_client import supabase
import uuid

router = APIRouter(prefix="/equipment", tags=["equipment"])

# =============== Pydantic Models ===============
class EquipmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    serial_number: Optional[str] = None
    model_number: Optional[str] = None
    manufacturer: Optional[str] = None
    status: Optional[str] = "available"
    condition: Optional[str] = "good"
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    notes: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(EquipmentBase):
    name: Optional[str] = None

class EquipmentResponse(EquipmentBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# =============== Helper Functions ===============
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

def format_equipment(data: dict) -> dict:
    """Format equipment data for response"""
    if not data:
        return {}
    
    def to_str(value):
        if value is None:
            return None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return str(value)
    
    return {
        "id": str(data.get("id", "")),
        "name": str(data.get("name", "")),
        "description": data.get("description"),
        "category": data.get("category"),
        "serial_number": data.get("serial_number"),
        "model_number": data.get("model_number"),
        "manufacturer": data.get("manufacturer"),
        "status": data.get("status", "available"),
        "condition": data.get("condition", "good"),
        "purchase_date": to_str(data.get("purchase_date")),
        "purchase_price": data.get("purchase_price"),
        "supplier": data.get("supplier"),
        "location": data.get("location"),
        "assigned_to": data.get("assigned_to"),
        "last_maintenance": to_str(data.get("last_maintenance")),
        "next_maintenance": to_str(data.get("next_maintenance")),
        "notes": data.get("notes"),
        "created_at": to_str(data.get("created_at")),
        "updated_at": to_str(data.get("updated_at")),
    }

# =============== API Endpoints ===============

@router.get("/", response_model=List[EquipmentResponse])
async def get_equipment(
    search: Optional[str] = Query(None, description="Search by name, serial, model"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned person"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get all equipment with optional filtering"""
    try:
        query = supabase.table("equipment").select("*")

        # Apply filters
        if search:
            query = query.or_(
                f"name.ilike.%{search}%,"
                f"serial_number.ilike.%{search}%,"
                f"model_number.ilike.%{search}%,"
                f"manufacturer.ilike.%{search}%"
            )
        
        if category:
            query = query.eq("category", category)
        
        if status:
            query = query.eq("status", status)
        
        if location:
            query = query.eq("location", location)
        
        if assigned_to:
            query = query.eq("assigned_to", assigned_to)

        # Pagination
        query = query.range(offset, offset + limit - 1).order("name")

        result = query.execute()
        
        if not result.data:
            return []
        
        return [format_equipment(item) for item in result.data]
    except Exception as e:
        print(f"Error in get_equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/count", response_model=int)
async def get_equipment_count(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
):
    """Get count of equipment matching filters"""
    try:
        query = supabase.table("equipment").select("*", count="exact", head=True)

        if search:
            query = query.or_(
                f"name.ilike.%{search}%,"
                f"serial_number.ilike.%{search}%,"
                f"model_number.ilike.%{search}%,"
                f"manufacturer.ilike.%{search}%"
            )
        
        if category:
            query = query.eq("category", category)
        
        if status:
            query = query.eq("status", status)
        
        if location:
            query = query.eq("location", location)
        
        if assigned_to:
            query = query.eq("assigned_to", assigned_to)

        result = query.execute()
        return result.count if hasattr(result, 'count') else 0
    except Exception as e:
        print(f"Error in get_equipment_count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment_by_id(equipment_id: str):
    """Get a single equipment item by ID"""
    try:
        result = supabase.table("equipment").select("*").eq("id", equipment_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        return format_equipment(result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_equipment_by_id: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=EquipmentResponse, status_code=201)
async def create_equipment(equipment: EquipmentCreate):
    """Create a new equipment item"""
    try:
        data = equipment.model_dump(exclude_unset=True)
        supabase_data = prepare_data_for_supabase(data)
        
        # Generate ID if not provided
        if "id" not in supabase_data:
            supabase_data["id"] = str(uuid.uuid4())
        
        result = supabase.table("equipment").insert(supabase_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create equipment")
        
        return format_equipment(result.data[0])
    except Exception as e:
        print(f"Error in create_equipment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(equipment_id: str, equipment: EquipmentUpdate):
    """Update an existing equipment item"""
    try:
        # Check if exists
        existing = supabase.table("equipment").select("*").eq("id", equipment_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        # Prepare update data
        update_data = equipment.model_dump(exclude_unset=True)
        supabase_data = prepare_data_for_supabase(update_data)
        
        if not supabase_data:
            return format_equipment(existing.data[0])
        
        result = supabase.table("equipment").update(supabase_data).eq("id", equipment_id).execute()
        
        return format_equipment(result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{equipment_id}", status_code=204)
async def delete_equipment(equipment_id: str):
    """Delete an equipment item"""
    try:
        result = supabase.table("equipment").delete().eq("id", equipment_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
async def get_equipment_stats():
    """Get overview statistics"""
    try:
        # Get all equipment
        result = supabase.table("equipment").select("*").limit(1000).execute()
        equipment = result.data if result.data else []
        
        total = len(equipment)
        available = sum(1 for e in equipment if e.get("status") == "available")
        in_use = sum(1 for e in equipment if e.get("status") == "in_use")
        maintenance = sum(1 for e in equipment if e.get("status") == "maintenance")
        damaged = sum(1 for e in equipment if e.get("status") == "damaged")
        
        # Need maintenance soon (next 30 days)
        today = date.today()
        need_maintenance = 0
        total_value = 0.0
        
        for e in equipment:
            if e.get("next_maintenance"):
                try:
                    maint_date = e["next_maintenance"]
                    if isinstance(maint_date, str):
                        maint_date = date.fromisoformat(maint_date)
                    days_until = (maint_date - today).days
                    if 0 <= days_until <= 30:
                        need_maintenance += 1
                except:
                    pass
            
            if e.get("purchase_price"):
                try:
                    total_value += float(e["purchase_price"])
                except:
                    pass
        
        return {
            "total": total,
            "available": available,
            "in_use": in_use,
            "maintenance": maintenance,
            "damaged": damaged,
            "need_maintenance_soon": need_maintenance,
            "total_value": round(total_value, 2),
        }
    except Exception as e:
        print(f"Error in get_equipment_stats: {e}")
        return {
            "total": 0,
            "available": 0,
            "in_use": 0,
            "maintenance": 0,
            "damaged": 0,
            "need_maintenance_soon": 0,
            "total_value": 0,
        }
