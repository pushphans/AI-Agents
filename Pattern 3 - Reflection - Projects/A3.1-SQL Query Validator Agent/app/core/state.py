from typing import Literal, Optional, TypedDict


class AgentState(TypedDict):
    user_question: str
    schema: str
    current_sql: str
    evaluation: Optional[Literal["pass", "fail"]]
    feedback: list[str]
    current_iteration: int
    max_iterations: int
    query_results: Optional[list[dict]]
    error: Optional[str]
