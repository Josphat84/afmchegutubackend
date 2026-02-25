# Backend events router
# backend/app/routers/events.py

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time, datetime
from app.supabase_client import supabase
import uuid
import os

router = APIRouter(prefix="/events", tags=["events"])

# =============== Pydantic Models ===============

class EventBase(BaseModel):
    title: str
    content: Optional[str] = None
    excerpt: Optional[str] = None
    type: str = "event"
    category: Optional[str] = None
    
    # Event dates (all optional)
    event_start_date: Optional[date] = None
    event_end_date: Optional[date] = None
    event_start_time: Optional[time] = None
    event_end_time: Optional[time] = None
    all_day: Optional[bool] = False
    
    # Location (all optional)
    location: Optional[str] = None
    venue: Optional[str] = None
    address: Optional[str] = None
    is_online: Optional[bool] = False
    online_url: Optional[str] = None
    
    # Media
    featured_image: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    
    # Author
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    
    # Status
    is_published: bool = True
    is_featured: bool = False

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    title: Optional[str] = None

class EventResponse(EventBase):
    id: str
    views: int = 0
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    rsvp_count: int = 0

class RSVPBase(BaseModel):
    event_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    guests: int = 1
    notes: Optional[str] = None

class RSVPCreate(RSVPBase):
    pass

class RSVPResponse(RSVPBase):
    id: str
    created_at: Optional[str] = None

class StatsResponse(BaseModel):
    total_events: int
    published_events: int
    upcoming_events: int
    total_rsvps: int

# =============== Helper Functions ===============

def prepare_data(data: dict) -> dict:
    """Convert date/time objects to strings for Supabase"""
    prepared = {}
    for key, value in data.items():
        if value is None or value == "":
            prepared[key] = None
        elif isinstance(value, (date, datetime)):
            prepared[key] = value.isoformat()
        elif isinstance(value, time):
            prepared[key] = value.strftime("%H:%M:%S")
        elif isinstance(value, list):
            prepared[key] = value
        else:
            prepared[key] = value
    return prepared

def safe_execute(query_func, error_message: str = "Database error"):
    """Safely execute a Supabase query with error handling"""
    try:
        result = query_func()
        return result
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")

# =============== Image Upload Endpoint ===============

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image to Supabase Storage 'images' bucket"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/heic", "image/heif"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Check file size (limit to 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        if not file_ext:
            file_ext = ".jpg"  # Default extension
        file_name = f"{uuid.uuid4()}{file_ext}"
        
        # Upload to Supabase Storage 'images' bucket
        upload_result = supabase.storage.from_("images").upload(
            file_name,
            content,
            {"content-type": file.content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_("images").get_public_url(file_name)
        
        return {"url": public_url, "filename": file_name}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

# =============== Event Endpoints ===============

@router.get("/", response_model=List[EventResponse])
async def get_events(
    search: Optional[str] = Query(None, description="Search by title or content"),
    type: Optional[str] = Query(None, description="Filter by event type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    featured: Optional[bool] = Query(None, description="Show only featured events"),
    upcoming: Optional[bool] = Query(None, description="Show only upcoming events"),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
):
    """Get events with filtering"""
    try:
        query = supabase.table("events").select("*")

        # Apply filters
        if search:
            query = query.or_(f"title.ilike.%{search}%,content.ilike.%{search}%")
        
        if type:
            query = query.eq("type", type)
        
        if category:
            query = query.eq("category", category)
        
        if featured is not None:
            query = query.eq("is_featured", featured)
        
        if upcoming:
            today = date.today().isoformat()
            query = query.gte("event_start_date", today).eq("type", "event")
        
        # Only show published events
        query = query.eq("is_published", True)
        
        # Pagination and sorting
        query = query.range(offset, offset + limit - 1).order("published_at", desc=True)

        result = query.execute()
        
        if not result.data:
            return []
        
        # Get RSVP counts for each event
        events_data = []
        for item in result.data:
            rsvp_result = supabase.table("event_rsvps").select("*", count="exact", head=True).eq("event_id", item["id"]).execute()
            item["rsvp_count"] = rsvp_result.count if hasattr(rsvp_result, 'count') else 0
            events_data.append(item)
        
        return events_data
    except Exception as e:
        print(f"Error in get_events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    """Get a single event by ID"""
    try:
        # Increment view count
        update_result = supabase.table("events").update({"views": supabase.raw("views + 1")}).eq("id", event_id).execute()
        
        # Get event details
        result = supabase.table("events").select("*").eq("id", event_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get RSVP count
        rsvp_result = supabase.table("event_rsvps").select("*", count="exact", head=True).eq("event_id", event_id).execute()
        result.data[0]["rsvp_count"] = rsvp_result.count if hasattr(rsvp_result, 'count') else 0
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(event: EventCreate):
    """Create a new event/notice"""
    try:
        data = event.model_dump(exclude_unset=True)
        data["id"] = str(uuid.uuid4())
        data["published_at"] = datetime.now().isoformat()
        data = prepare_data(data)
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = supabase.table("events").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create event")
        
        return result.data[0]
    except Exception as e:
        print(f"Create error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, event: EventUpdate):
    """Update an existing event"""
    try:
        # Check if exists
        existing = supabase.table("events").select("*").eq("id", event_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Prepare update data
        update_data = event.model_dump(exclude_unset=True)
        update_data = prepare_data(update_data)
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return existing.data[0]
        
        result = supabase.table("events").update(update_data).eq("id", event_id).execute()
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: str):
    """Delete an event"""
    try:
        # First delete associated RSVPs
        supabase.table("event_rsvps").delete().eq("event_id", event_id).execute()
        
        # Then delete the event
        result = supabase.table("events").delete().eq("id", event_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============== RSVP Endpoints ===============

@router.get("/{event_id}/rsvps", response_model=List[RSVPResponse])
async def get_event_rsvps(event_id: str):
    """Get all RSVPs for an event"""
    try:
        result = supabase.table("event_rsvps").select("*").eq("event_id", event_id).order("created_at").execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"RSVP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rsvps", response_model=RSVPResponse, status_code=201)
async def create_rsvp(rsvp: RSVPCreate):
    """Create an RSVP for an event"""
    try:
        # Check if event exists
        event = supabase.table("events").select("*").eq("id", rsvp.event_id).execute()
        if not event.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        data = rsvp.model_dump()
        data["id"] = str(uuid.uuid4())
        
        result = supabase.table("event_rsvps").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create RSVP")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"RSVP create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/rsvps/{rsvp_id}", status_code=204)
async def delete_rsvp(rsvp_id: str):
    """Cancel an RSVP"""
    try:
        result = supabase.table("event_rsvps").delete().eq("id", rsvp_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="RSVP not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"RSVP delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============== Stats Endpoint ===============

@router.get("/stats/overview", response_model=StatsResponse)
async def get_event_stats():
    """Get overview statistics"""
    try:
        today = date.today().isoformat()
        
        # Get all events
        events_result = supabase.table("events").select("*").execute()
        events = events_result.data if events_result.data else []
        
        total = len(events)
        published = sum(1 for e in events if e.get("is_published", False))
        
        # Upcoming events
        upcoming = sum(1 for e in events 
                      if e.get("type") == "event" 
                      and e.get("event_start_date") 
                      and e["event_start_date"] >= today
                      and e.get("is_published", False))
        
        # Total RSVPs
        rsvps_result = supabase.table("event_rsvps").select("*", count="exact", head=True).execute()
        total_rsvps = rsvps_result.count if hasattr(rsvps_result, 'count') else 0
        
        return StatsResponse(
            total_events=total,
            published_events=published,
            upcoming_events=upcoming,
            total_rsvps=total_rsvps,
        )
    except Exception as e:
        print(f"Stats error: {e}")
        return StatsResponse(
            total_events=0,
            published_events=0,
            upcoming_events=0,
            total_rsvps=0,
        )