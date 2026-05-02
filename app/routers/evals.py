from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app import schemas
from app.models import EvalRun, EvalStatus, EvalResult
from app.database import get_db
from app.runner import run_eval

router = APIRouter(prefix="/evals", tags=["evals"])

@router.post("/", response_model=schemas.TriggerEvalResponse)
async def trigger_eval(eval: schemas.TriggerEval, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
        eval_run = EvalRun(prompt_version_tag=eval.prompt_version_tag, project_id=eval.project_id)
        db.add(eval_run)
        await db.commit()
        await db.refresh(eval_run)
        background_tasks.add_task(run_eval, eval_run.id)
        return eval_run
        
@router.get("/{eval_id}/results", response_model=schemas.GetResultResponse)
async def get_result(eval_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EvalRun).where(EvalRun.id == eval_id))
    eval_run = result.scalar_one()
    status = eval_run.status

    if status == EvalStatus.completed:
        stmt = select(EvalResult).where(EvalResult.run_id == eval_id).options(joinedload(EvalResult.golden_pair))
        results = await db.execute(stmt)
        eval_results = results.scalars().all()
        results_out = [
            {
                "input_payload": r.golden_pair.input_payload,
                "expected_output": r.golden_pair.expected_output,
                "actual_output": r.actual_output,
                "passed": r.passed,
                "reason": r.reason
            }
            for r in eval_results
        ]
    else:
        results_out = []

    return {"eval_id": eval_id, "status": status, "results": results_out}