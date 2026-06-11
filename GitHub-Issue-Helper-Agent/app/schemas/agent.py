from pydantic import BaseModel


class AgentInput(BaseModel):
    message: str
    session_id: str


class AgentOutput(BaseModel):
    response: str
    session_id: str
