from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import projects, evals

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(evals.router)