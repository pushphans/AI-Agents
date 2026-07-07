import sqlite3

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from app.core.state import AgentState


class CriticOutput(BaseModel):
    evaluation: str = Field(description="pass or fail")
    feedback: list[str] = Field(description="List of issues found, empty if pass")


def create_generator_node(llm: BaseChatModel):
    def generator(state: AgentState) -> dict:
        SYSTEM_PROMPT = f"""You are a SQL query generator. Given a database schema and a user question, write a valid SQLite SELECT query.

SCHEMA:
{state["schema"]}

RULES:
- Write only SELECT queries (no INSERT, UPDATE, DELETE)
- Always specify column names, never use SELECT *
- Always include a LIMIT clause (default 10)
- Use proper JOIN syntax when querying multiple tables
- Use indexed columns in WHERE clauses when possible
- Return ONLY the SQL query, no explanation"""

        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        if state.get("feedback"):
            feedback_text = "\n".join(state["feedback"])
            messages.append(
                HumanMessage(
                    content=f"Previous attempt failed with these issues:\n{feedback_text}\n\n"
                    f"Now generate a corrected SQL query for: {state['user_question']}"
                )
            )
        else:
            messages.append(HumanMessage(content=state["user_question"]))

        response = llm.invoke(messages)
        sql = response.content.strip()

        if sql.startswith("```sql"):
            sql = sql[7:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]

        return {"current_sql": sql.strip()}

    return generator


def create_crititc_node(llm: BaseChatModel):
    structured_llm = llm.with_structured_output(CriticOutput)

    def critic(state: AgentState) -> dict:
        SYSTEM_PROMPT = f"""You are a SQL query validator. Given a database schema, a SQL query, and the user's original question, validate the query.

SCHEMA:
{state["schema"]}

QUERY TO VALIDATE:
{state["current_sql"]}

USER QUESTION:
{state["user_question"]}

CHECK THESE 7 CONDITIONS:
1. Syntax: Is the SQL syntactically correct?
2. Schema Match: Do all tables and columns exist in the schema?
3. JOIN Logic: Are JOINs correct with proper ON conditions?
4. WHERE Safety: Is WHERE clause safe (no always-true bypass like WHERE 1=1)?
5. LIMIT Present: Does the query have a LIMIT clause?
6. Injection Safe: Any raw string concatenation or unsafe patterns?
7. Performance: Are indexed columns used in WHERE/JOIN?"""

        response = structured_llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content="Validate this SQL query."),
            ]
        )

        return {
            "evaluation": response.evaluation,
            "feedback": response.feedback,
        }

    return critic


def create_executor_node(conn: sqlite3.Connection):
    def executor(state: AgentState) -> dict:
        try:
            cursor = conn.cursor()
            cursor.execute(state["current_sql"])
            rows = cursor.fetchall()
            return {"query_results": [dict(row) for row in rows], "error": None}
        except Exception as e:
            return {"query_results": [], "error": str(e)}

    return executor


def router(state: AgentState) -> str:
    if state["evaluation"] == "pass":
        return "executor"
    if state["current_iteration"] < state["max_iterations"]:
        return "generator"
    return "executor"


def build_graph(llm: BaseChatModel, conn: sqlite3.Connection):
    generator = create_generator_node(llm)
    critic = create_crititc_node(llm)
    executor = create_executor_node(conn)

    graph = StateGraph(AgentState)

    graph.add_node("generator", generator)
    graph.add_node("critic", critic)
    graph.add_node("executor", executor)

    graph.add_edge(START, "generator")
    graph.add_edge("generator", "critic")

    graph.add_conditional_edges(
        "critic",
        router,
        {"generator": "generator", "executor": "executor"},
    )

    graph.add_edge("executor", END)

    return graph.compile()
