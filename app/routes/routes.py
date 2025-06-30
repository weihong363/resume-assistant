from fastapi import APIRouter

router = APIRouter()

@router.get("/tasks")
def get_tasks():
    return {
        "tasks": [
            {"name": "resumeParsing", "id": "a1"},
            {"name": "jdMatchingEngine", "id": "a2"},
            {"name": "interviewSimulationAPI", "id": "a3"},
        ]
    }
