from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.ab_test import router as ab_test_router

app = FastAPI(title="Data Analyst Portfolio Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ab_test_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
