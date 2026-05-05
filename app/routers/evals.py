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
async def get_result(eval_id: int, compared_to: int | None = None, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(EvalRun).where(EvalRun.id == eval_id))
    eval_run = result.scalar_one()
    project_id = eval_run.project_id

    if not compared_to:
        compared_to  = await db.scalar(select(EvalRun.id).where(EvalRun.project_id== project_id).where(EvalRun.triggered_at < eval_run.triggered_at).order_by(EvalRun.triggered_at.desc()).limit(1))
    
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

        if compared_to:
            stmt = select(EvalResult).where(EvalResult.run_id == compared_to).options(joinedload(EvalResult.golden_pair))
            outputs = await db.execute(stmt)
            compared_eval_results = outputs.scalars().all()

            run_1 = {e.golden_pair_id : e for e in eval_results}
            run_2 = {e.golden_pair_id : e for e in compared_eval_results}

            newly_failing = []
            newly_passing = []
            unchanged_failing = []
            unchanged_passing = []

            for key, pair_1 in run_1.items():
                pair_2 = run_2.get(key)

                if pair_2:
                    if pair_2.passed :
                        if pair_1.passed:
                            unchanged_passing.append(key)
                        else:
                            newly_failing.append(key)
                    else:
                        if pair_1.passed:
                            newly_passing.append(key)
                        else:
                            unchanged_failing.append(key)

            regression_item = schemas.RegressionItem(newly_failing = newly_failing, newly_passing= newly_passing, unchanged_failing = unchanged_failing, unchanged_passing = unchanged_passing)

            return {"eval_id": eval_id, "status": status, "results": results_out, "regression": regression_item}
        
    else:
        results_out = []



    return {"eval_id": eval_id, "status": status, "results": results_out}