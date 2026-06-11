"""GitHub issue management tools for the helper agent."""

from typing import Optional

import httpx
from langchain_core.tools import tool

from app.core.config import settings
from app.schemas.tools import (
    AddCommentInput,
    AssignIssueInput,
    CloseIssueInput,
    CreateIssueInput,
    ListIssuesInput,
)

BASE_URL = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def _make_request(
    method: str, url: str, **kwargs
) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, headers=_headers(), **kwargs)
        if resp.is_success:
            return resp.text
        return f"GitHub API error {resp.status_code}: {resp.text[:500]}"
    except httpx.TimeoutException:
        return "Network timeout: GitHub API did not respond within 30 seconds."
    except httpx.ConnectError:
        return "Connection error: could not reach GitHub API. Check your network."
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


@tool(args_schema=ListIssuesInput)
async def list_issues(
    repo: str,
    status: str = "open",
    labels: str = "",
) -> str:
    """List issues from a GitHub repository."""
    print(f"  → Tool called: list_issues(repo={repo}, status={status}, labels={labels})")
    params = {"state": status, "per_page": 100}
    if labels:
        params["labels"] = labels
    return await _make_request("GET", f"{BASE_URL}/repos/{repo}/issues", params=params)


@tool(args_schema=CreateIssueInput)
async def create_issue(
    repo: str,
    title: str,
    body: str = "",
    labels: Optional[list[str]] = None,
) -> str:
    """Create a new issue in a GitHub repository."""
    print(f"  → Tool called: create_issue(repo={repo}, title={title}, labels={labels})")
    payload: dict = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    return await _make_request("POST", f"{BASE_URL}/repos/{repo}/issues", json=payload)


@tool(args_schema=CloseIssueInput)
async def close_issue(repo: str, issue_number: int) -> str:
    """Close an issue in a GitHub repository."""
    print(f"  → Tool called: close_issue(repo={repo}, issue_number={issue_number})")
    return await _make_request(
        "PATCH", f"{BASE_URL}/repos/{repo}/issues/{issue_number}", json={"state": "closed"}
    )


@tool(args_schema=AddCommentInput)
async def add_comment(repo: str, issue_number: int, comment: str) -> str:
    """Add a comment to an issue in a GitHub repository."""
    print(f"  → Tool called: add_comment(repo={repo}, issue_number={issue_number})")
    return await _make_request(
        "POST",
        f"{BASE_URL}/repos/{repo}/issues/{issue_number}/comments",
        json={"body": comment},
    )


@tool(args_schema=AssignIssueInput)
async def assign_issue(repo: str, issue_number: int, assignee: str) -> str:
    """Assign an issue to a user in a GitHub repository."""
    print(f"  → Tool called: assign_issue(repo={repo}, issue_number={issue_number}, assignee={assignee})")
    return await _make_request(
        "POST",
        f"{BASE_URL}/repos/{repo}/issues/{issue_number}/assignees",
        json={"assignees": [assignee]},
    )


TOOLS = [
    list_issues,
    create_issue,
    close_issue,
    add_comment,
    assign_issue,
]
