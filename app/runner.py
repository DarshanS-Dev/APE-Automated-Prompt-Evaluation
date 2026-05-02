from app.models import Project, GoldenPair, RubricRule, EvalRun, EvalResult
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models import EvalStatus
import asyncio, httpx


async def fetch_project_data(project_id: int, session):
    project = await session.execute(select(Project).where(Project.id== project_id))
    golden_pairs = await session.execute(select(GoldenPair).where(GoldenPair.project_id == project_id))
    rules = await session.execute(select(RubricRule).where(RubricRule.project_id == project_id))

    return project.scalars().first(), golden_pairs.scalars().all(), rules.scalars().all()

async def hit_endpoint(client, endpoint_url, input_payload):
    response = await client.post(endpoint_url, json=input_payload)
    return response.text

async def run_eval(eval_id):
    async with AsyncSessionLocal() as session:
        eval_run = None
        try:
            result = await session.execute(select(EvalRun).where(EvalRun.id==eval_id))
            eval_run = result.scalar_one()
            project_id = eval_run.project_id
            project, golden_pairs, rules = await fetch_project_data(project_id, session)
            endpoint_url = project.endpoint_url
            async with httpx.AsyncClient() as client:
                results = await asyncio.gather(
                    *[hit_endpoint(client, endpoint_url, golden_pair.input_payload) for golden_pair in golden_pairs]
                )

            for golden_pair, result in zip(golden_pairs, results):
                eval_result = EvalResult(actual_output=result, reason="", golden_pair_id=golden_pair.id, run_id=eval_run.id, passed=True)
                session.add(eval_result)

            eval_run.status = EvalStatus.completed
        except Exception as e:
            print(f"run_eval failed: {e}")
            await session.rollback()
            if eval_run:
                eval_run.status = EvalStatus.failed
        finally:
            await session.commit()