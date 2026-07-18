from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.core.config import settings
from app.models.schemas import GeneratedBlog, EvaluationResult

llm = ChatDeepSeek(
    api_key=settings.DEEPSEEK_API_KEY,
    model="deepseek-chat",
    max_retries=3,
    temperature=0.7,
)

generate_llm = llm.with_structured_output(GeneratedBlog)
evaluate_llm = llm.with_structured_output(EvaluationResult)


class BlogState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    current_iteration: int
    max_iterations: int
    evaluation: Literal["pass", "fail"]
    feedback: str


def generate_blog(state: BlogState) -> dict:
    topic = state["messages"][-1].content
    feedback = state.get("feedback", "")
    current_iter = state.get("current_iteration", 0)

    if feedback and current_iter > 0:
        prompt = (
            f"Improve the blog on topic: {topic}\n\n"
            f"Previous feedback to incorporate:\n{feedback}\n\n"
            "Generate an improved version of the blog addressing the feedback above."
        )
    else:
        prompt = (
            f"Write a comprehensive blog on the topic: {topic}\n\n"
            "Make sure to:\n"
            "- Cover the topic thoroughly\n"
            "- Write in clear, grammatically correct language\n"
            "- Use appropriate SEO keywords naturally\n"
            "- Ensure factual accuracy\n"
            "- Write for readability (short paragraphs, clear structure)\n"
            "- Aim for approximately 500 words"
        )

    result: GeneratedBlog = generate_llm.invoke([HumanMessage(content=prompt)])

    return {
        "messages": [AIMessage(content=result.blog_content)],
        "current_iteration": current_iter + 1,
    }


def evaluate_blog(state: BlogState) -> dict:
    blog_content = state["messages"][-1].content

    prompt = (
        "You are a strict blog critic. Evaluate the following blog against these criteria:\n\n"
        "1. **Length Check**: Is it approximately 500 words?\n"
        "2. **Topic Coverage**: Does it thoroughly cover the assigned topic?\n"
        "3. **Grammar/Clarity**: Is it grammatically correct and clear?\n"
        "4. **Factual Accuracy**: Are there any factual issues?\n"
        "5. **SEO Keywords**: Are relevant keywords used naturally?\n"
        "6. **Readability Score**: Is it well-structured and easy to read?\n\n"
        f"Blog to evaluate:\n{blog_content}\n\n"
        "Provide your evaluation result."
    )

    result: EvaluationResult = evaluate_llm.invoke([HumanMessage(content=prompt)])

    return {
        "evaluation": result.evaluation,
        "feedback": result.feedback,
    }


def should_continue(state: BlogState) -> Literal["generate_blog", "__end__"]:
    if state["evaluation"] == "pass":
        return END
    if state["current_iteration"] >= state["max_iterations"]:
        return END
    return "generate_blog"


workflow = StateGraph(BlogState)

workflow.add_node("generate_blog", generate_blog)
workflow.add_node("evaluate_blog", evaluate_blog)

workflow.add_edge(START, "generate_blog")
workflow.add_edge("generate_blog", "evaluate_blog")
workflow.add_conditional_edges("evaluate_blog", should_continue)

graph = workflow.compile()
