
from fastapi import FastAPI
# Import für Version 1 
from project.api.v1.api_v1 import api_router as v1_router
# Import für Version 2 (neu)
from project.api.v2.api_v2 import api_router as v2_router

app = FastAPI(title="Blutzucker API - Multi-Version")

# Hier werden beide "Leitungen" freigeschaltet:
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

@app.get("/")
def home():
    return {
        "v1": "/api/v1/users",
        "v2": "/api/v2/users"
    }


