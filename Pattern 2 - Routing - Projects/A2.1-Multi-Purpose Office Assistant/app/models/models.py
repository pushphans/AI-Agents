from pydantic import BaseModel, Field


class RequestModel(BaseModel):
    query: str = Field(..., description="User's query")


class ResponseModel(BaseModel):
    answer: str = Field(..., description="Model's response")
    router: str = Field(description="Route chosen by the router")
