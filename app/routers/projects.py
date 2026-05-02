from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import models
from app.database import get_db
from app import schemas

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=schemas.ProjectResponse)
async def create_project(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_db)):
    new_project = models.Project(name=project.name, endpoint_url=project.endpoint_url)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.post("/goldenpairs", response_model=schemas.GoldenPairResponse)
async def create_golden_pair(golden_pair: schemas.GoldenPairCreate, db: AsyncSession = Depends(get_db)):
    new_golden_pair = models.GoldenPair(project_id=golden_pair.project_id, input_payload=golden_pair.input_payload, expected_output=golden_pair.expected_output)
    db.add(new_golden_pair)
    await db.commit()
    await db.refresh(new_golden_pair)
    return new_golden_pair

@router.post("/rubric", response_model=schemas.RubricResponse)
async def create_rubric(rubric: schemas.RubricCreate, db: AsyncSession = Depends(get_db)):
    new_rubric = models.RubricRule(project_id=rubric.project_id, rule_text=rubric.rule)
    db.add(new_rubric)
    await db.commit()
    await db.refresh(new_rubric)
    return new_rubric