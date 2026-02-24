from fastapi import APIRouter

# Diese Zeile fehlt wahrscheinlich oder ist falsch benannt:
router = APIRouter()

@router.get("/")
def get_users_v2():
    return [
        {
            "id": 1, 
            "firstName": "Max", 
            "lastName": "Mustermann", 
            "info": "Dies sind neue V2 Daten!"
        }
    ]
