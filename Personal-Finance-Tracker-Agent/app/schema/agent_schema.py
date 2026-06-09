from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, description="User message for the finance agent")


class AgentResponse(BaseModel):
    response: str
