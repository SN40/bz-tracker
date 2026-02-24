
from fastapi import APIRouter
# WICHTIG: Prüfe, ob in project/api/v2/endpoints/users.py eine Variable 'router' existiert!
from project.api.v2.endpoints import users 

# Das ist die Variable, die main.py sucht:
api_router = APIRouter()

# Hier binden wir die Unter-Router ein
# Hier wird aus "/" (in users.py) -> "/users"
api_router.include_router(users.router, prefix="/users", tags=["V2"])
