from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from app.agent.workflow import graph
from app.models.schemas import BlogRequest, BlogResponse

router = APIRouter(prefix="/api", tags=["blog"])


@router.post("/generate-blog", response_model=BlogResponse)
def generate_blog(request: BlogRequest):
    initial_state = {
        "messages": [HumanMessage(content=request.topic)],
        "current_iteration": 0,
        "max_iterations": request.max_iterations,
        "evaluation": "fail",
        "feedback": "",
    }

    result = graph.invoke(initial_state)

    messages = result["messages"]
    blog_content = next(
        (m.content for m in reversed(messages) if hasattr(m, "content") and m.content),
        None,
    )

    return BlogResponse(
        success=result["evaluation"] == "pass",
        blog_content=blog_content,
        iterations_taken=result["current_iteration"],
        evaluation=result["evaluation"],
        feedback=result.get("feedback"),
    )
