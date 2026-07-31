"""
FoodFlow Chatbot Application Entrypoint
FastAPI server runner
"""

import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project.codebase.api.routes import router as api_router

app = FastAPI(
    title="FoodFlow AI Agent API",
    description="API Trợ lý AI Đặt đồ ăn & Tư vấn thực đơn ShopeeFood tại Vinhomes Ocean Park",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "app": "FoodFlow AI Agent Backend",
        "status": "running",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }


if __name__ == "__main__":
    uvicorn.run("project.codebase.main:app", host="0.0.0.0", port=8000, reload=True)
