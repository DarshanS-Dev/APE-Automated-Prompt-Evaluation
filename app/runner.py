from app.models import Project, GoldenPair, RubricRule, EvalRun, EvalResult
from app.database import AsyncSessionLocal
from app.judge import judge
from sqlalchemy import select
from app.models import EvalStatus
import asyncio, httpx


async def fetch_project_data(project_id: int, session):
    project = await session.execute(select(Project).where(Project.id== project_id))
    golden_pairs = await session.execute(select(GoldenPair).where(GoldenPair.project_id == project_id))
    rules = await session.execute(select(RubricRule).where(RubricRule.project_id == project_id))

    return project.scalars().first(), golden_pairs.scalars().all(), rules.scalars().all()

async def hit_endpoint(client, endpoint_url, input_payload):
    response = await client.post(endpoint_url, json=input_payload, timeout=60.0)
    return response.text

async def run_eval(eval_id):
    async with AsyncSessionLocal() as session:
        eval_run = None
        try:
            result = await session.execute(select(EvalRun).where(EvalRun.id==eval_id))
            eval_run = result.scalar_one()
            project_id = eval_run.project_id
            project, golden_pairs, rules = await fetch_project_data(project_id, session)
            rules = [rule.rule_text for rule in rules]
            endpoint_url = project.endpoint_url
            async with httpx.AsyncClient() as client:
                results = await asyncio.gather(
                    *[hit_endpoint(client, endpoint_url, golden_pair.input_payload) for golden_pair in golden_pairs]
                )

            verdicts = await asyncio.gather(
                *[judge(input_payload=golden_pair.input_payload, expected_behaviour=golden_pair.expected_output, actual_output=result, rules=rules) for golden_pair, result in zip(golden_pairs, results)]
            )
            for golden_pair, result, verdict in zip(golden_pairs, results, verdicts):
                is_passed, reasoning = verdict['passed'], verdict['reasoning']
                eval_result = EvalResult(actual_output=result, reason=reasoning, golden_pair_id=golden_pair.id, run_id=eval_run.id, passed=is_passed)
                session.add(eval_result)

            eval_run.status = EvalStatus.completed
            eval_run.score = sum(v["passed"] for v in verdicts)/ len(verdicts) if verdicts else 0.0
        except:
            await session.rollback()
            if eval_run:
                eval_run.status = EvalStatus.failed
        finally:
            await session.commit()