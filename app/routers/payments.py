# Backend payments router
# backend/app/routers/payments.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime
from app.supabase_client import supabase
import uuid

router = APIRouter(prefix="/payments", tags=["payments"])

# =============== Pydantic Models ===============

class PaymentBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    amount: float
    currency: str = "USD"
    reason: str
    reason_other: Optional[str] = None
    payment_method: str
    payment_reference: Optional[str] = None
    payment_date: date
    payment_time: time
    amount_in_words: Optional[str] = None
    received_by: str
    notes: Optional[str] = None
    church_name: Optional[str] = "AFM Chegutu Assembly"
    church_address: Optional[str] = "Phase 1, Chegutu, Zimbabwe"
    church_phone: Optional[str] = "+263 77 123 4567"
    church_email: Optional[str] = "info@afmchegutu.org"

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    reason: Optional[str] = None
    reason_other: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[date] = None
    payment_time: Optional[time] = None
    amount_in_words: Optional[str] = None
    received_by: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: str
    receipt_number: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StatsResponse(BaseModel):
    total: int
    total_amount: float
    today_total: float
    by_reason: dict
    by_method: dict

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
        elif isinstance(value, float):
            prepared[key] = round(value, 2)
        else:
            prepared[key] = value
    return prepared

def format_payment(data: dict) -> dict:
    """Format payment data for response"""
    return {
        "id": data["id"],
        "receipt_number": data["receipt_number"],
        "full_name": data["full_name"],
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address"),
        "amount": float(data["amount"]),
        "currency": data["currency"],
        "reason": data["reason"],
        "reason_other": data.get("reason_other"),
        "payment_method": data["payment_method"],
        "payment_reference": data.get("payment_reference"),
        "payment_date": data["payment_date"],
        "payment_time": data["payment_time"],
        "amount_in_words": data.get("amount_in_words"),
        "received_by": data["received_by"],
        "notes": data.get("notes"),
        "church_name": data.get("church_name"),
        "church_address": data.get("church_address"),
        "church_phone": data.get("church_phone"),
        "church_email": data.get("church_email"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }

# =============== API Endpoints ===============

@router.get("/", response_model=List[PaymentResponse])
async def get_payments(
    search: Optional[str] = Query(None, description="Search by name, receipt, email"),
    reason: Optional[str] = Query(None, description="Filter by reason"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get all payments with optional filtering"""
    try:
        query = supabase.table("payments").select("*")

        # Apply filters
        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,"
                f"receipt_number.ilike.%{search}%,"
                f"email.ilike.%{search}%,"
                f"phone.ilike.%{search}%"
            )
        
        if reason:
            query = query.eq("reason", reason)
        
        if payment_method:
            query = query.eq("payment_method", payment_method)
        
        if from_date:
            query = query.gte("payment_date", from_date.isoformat())
        
        if to_date:
            query = query.lte("payment_date", to_date.isoformat())

        # Pagination and sorting
        query = query.range(offset, offset + limit - 1).order("payment_date", desc=True).order("payment_time", desc=True)

        result = query.execute()
        
        if not result.data:
            return []
        
        return [format_payment(item) for item in result.data]
    except Exception as e:
        print(f"Error in get_payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/count", response_model=int)
async def get_payments_count(
    search: Optional[str] = Query(None),
    reason: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
):
    """Get count of payments matching filters"""
    try:
        query = supabase.table("payments").select("*", count="exact", head=True)

        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,"
                f"receipt_number.ilike.%{search}%,"
                f"email.ilike.%{search}%"
            )
        
        if reason:
            query = query.eq("reason", reason)
        
        if payment_method:
            query = query.eq("payment_method", payment_method)
        
        if from_date:
            query = query.gte("payment_date", from_date.isoformat())
        
        if to_date:
            query = query.lte("payment_date", to_date.isoformat())

        result = query.execute()
        return result.count if hasattr(result, 'count') else 0
    except Exception as e:
        print(f"Error in get_payments_count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str):
    """Get a single payment by ID"""
    try:
        result = supabase.table("payments").select("*").eq("id", payment_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return format_payment(result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=PaymentResponse, status_code=201)
async def create_payment(payment: PaymentCreate):
    """Create a new payment record and generate receipt number"""
    try:
        # Generate receipt number
        receipt_result = supabase.rpc("generate_receipt_number").execute()
        receipt_number = receipt_result.data if receipt_result.data else "0000001"
        
        # Prepare data
        data = payment.model_dump(exclude_unset=True)
        data["receipt_number"] = receipt_number
        data["id"] = str(uuid.uuid4())
        data = prepare_data(data)
        
        # Calculate amount in words if not provided
        if not data.get("amount_in_words"):
            # You can implement number to words conversion here
            # For now, leave it empty
            pass
        
        result = supabase.table("payments").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create payment")
        
        return format_payment(result.data[0])
    except Exception as e:
        print(f"Create error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(payment_id: str, payment: PaymentUpdate):
    """Update an existing payment"""
    try:
        # Check if exists
        existing = supabase.table("payments").select("*").eq("id", payment_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Prepare update data
        update_data = payment.model_dump(exclude_unset=True)
        update_data = prepare_data(update_data)
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return format_payment(existing.data[0])
        
        result = supabase.table("payments").update(update_data).eq("id", payment_id).execute()
        
        return format_payment(result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{payment_id}", status_code=204)
async def delete_payment(payment_id: str):
    """Delete a payment"""
    try:
        result = supabase.table("payments").delete().eq("id", payment_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview", response_model=StatsResponse)
async def get_payment_stats():
    """Get overview statistics"""
    try:
        today = date.today().isoformat()
        
        # Get all payments
        result = supabase.table("payments").select("*").execute()
        payments = result.data if result.data else []
        
        total = len(payments)
        total_amount = sum(float(p["amount"]) for p in payments)
        
        # Today's total
        today_payments = [p for p in payments if p.get("payment_date") == today]
        today_total = sum(float(p["amount"]) for p in today_payments)
        
        # By reason
        by_reason = {}
        for p in payments:
            reason = p["reason"]
            by_reason[reason] = by_reason.get(reason, 0) + float(p["amount"])
        
        # By method
        by_method = {}
        for p in payments:
            method = p["payment_method"]
            by_method[method] = by_method.get(method, 0) + float(p["amount"])
        
        return StatsResponse(
            total=total,
            total_amount=total_amount,
            today_total=today_total,
            by_reason=by_reason,
            by_method=by_method,
        )
    except Exception as e:
        print(f"Stats error: {e}")
        return StatsResponse(
            total=0,
            total_amount=0,
            today_total=0,
            by_reason={},
            by_method={},
        )

@router.get("/receipts/latest", response_model=str)
async def get_latest_receipt_number():
    """Get the latest receipt number"""
    try:
        result = supabase.table("payments").select("receipt_number").order("receipt_number", desc=True).limit(1).execute()
        if result.data:
            return result.data[0]["receipt_number"]
        return "0000000"
    except Exception as e:
        print(f"Error getting latest receipt: {e}")
        raise HTTPException(status_code=500, detail=str(e))