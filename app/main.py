from fastapi import FastAPI
from app.routes.example import router as example_router

app = FastAPI(title="My Backend API")

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

app.include_router(example_router)
