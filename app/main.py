from fastapi import FastAPI
from app.routers import projects, evals

app = FastAPI()

app.include_router(projects.router)
app.include_router(evals.router)