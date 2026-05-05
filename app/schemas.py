from pydantic import BaseModel
from app.models import EvalStatus
from typing import Optional

class EvalResultItem(BaseModel):
    input_payload: dict
    expected_output: str
    actual_output: str
    passed: bool
    reason: str

class RegressionItem(BaseModel):
    newly_failing: list[int]
    newly_passing: list[int]
    unchanged_failing: list[int]
    unchanged_passing: list[int]

class ProjectCreate(BaseModel):
    name: str
    endpoint_url: str

class ProjectResponse(BaseModel):
    id: int 
    name: str
    endpoint_url: str

class GoldenPairCreate(BaseModel):
    project_id: int
    input_payload: dict
    expected_output: str

class GoldenPairResponse(BaseModel):
    id: int
    input_payload: dict
    expected_output: str

class RubricCreate(BaseModel):
    project_id: int
    rule: str

class RubricResponse(BaseModel):
    id: int
    rule_text: str

class TriggerEval(BaseModel):
    project_id: int
    prompt_version_tag: str

class TriggerEvalResponse(BaseModel):
    id: int
    prompt_version_tag: str
    status: EvalStatus

class GetResultResponse(BaseModel):
    eval_id: int
    status: EvalStatus
    results: list[EvalResultItem]
    regression: Optional[RegressionItem] = None