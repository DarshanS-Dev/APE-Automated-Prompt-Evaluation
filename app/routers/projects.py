from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user_from_api_key

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=schemas.ProjectResponse)
async def create_project(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user_from_api_key)):
    new_project = models.Project(name=project.name, endpoint_url=project.endpoint_url, user_id=current_user.id)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.post("/goldenpairs", response_model=schemas.GoldenPairResponse)
async def create_golden_pair(golden_pair: schemas.GoldenPairCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user_from_api_key)):
    result = await db.execute(select(models.Project).where(models.Project.id == golden_pair.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(404, "Project not found")

    if project.user_id != current_user.id:
        raise HTTPException(403, "Not your resource")

    new_golden_pair = models.GoldenPair(project_id=golden_pair.project_id, input_payload=golden_pair.input_payload, expected_output=golden_pair.expected_output)
    db.add(new_golden_pair)
    await db.commit()
    await db.refresh(new_golden_pair)
    return new_golden_pair

@router.post("/rubric", response_model=schemas.RubricResponse)
async def create_rubric(rubric: schemas.RubricCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user_from_api_key)):
    result = await db.execute(select(models.Project).where(models.Project.id == rubric.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(404, "Project not found")

    if project.user_id != current_user.id:
        raise HTTPException(403, "Not your resource")
    
    new_rubric = models.RubricRule(project_id=rubric.project_id, rule_text=rubric.rule)
    db.add(new_rubric)
    await db.commit()
    await db.refresh(new_rubric)
    return new_rubric