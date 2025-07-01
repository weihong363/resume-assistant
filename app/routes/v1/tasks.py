@router.get("/tasks", 
    summary="Get all tasks",
    description="Returns a list of all available resume processing tasks",
    response_description="List of tasks with IDs and names")
def get_tasks():
    return {"tasks": [...]}