from typing import Literal

from pydantic import BaseModel


class BlogRequest(BaseModel):
    topic: str
    max_iterations: int = 3


class BlogResponse(BaseModel):
    success: bool
    blog_content: str | None = None
    iterations_taken: int
    evaluation: str
    feedback: str | None = None


class GeneratedBlog(BaseModel):
    blog_content: str


class EvaluationResult(BaseModel):
    evaluation: Literal["pass", "fail"]
    feedback: str
