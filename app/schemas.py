from pydantic import BaseModel
from app.models import EvalStatus

class EvalResultItem(BaseModel):
    input_payload: dict
    expected_output: dict
    actual_output: dict
    passed: bool
    reason: str

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
    expected_output: dict

class GoldenPairResponse(BaseModel):
    id: int
    input_payload: dict
    expected_output: dict

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