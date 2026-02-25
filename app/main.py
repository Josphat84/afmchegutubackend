from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import directory, equipment, events, payments
from datetime import datetime

app = FastAPI(title="AFM Chegutu API")

# Configure CORS - allow all for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(directory.router)
app.include_router(equipment.router)
app.include_router(events.router)
app.include_router(payments.router)

@app.get("/")
async def root():
    return {"message": "AFM Chegutu API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": str(datetime.now())}