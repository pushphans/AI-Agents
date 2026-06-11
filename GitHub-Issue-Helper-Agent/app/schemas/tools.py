"""Pydantic models for tool input validation."""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ListIssuesInput(BaseModel):
    repo: str = Field(description="Repository in format 'owner/repo'")
    status: str = Field(default="open", description="Issue state: open, closed, or all")
    labels: str = Field(default="", description="Comma-separated label names")

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: str) -> str:
        if not re.match(r"^[\w.-]+/[\w.-]+$", v):
            raise ValueError("repo must be in format 'owner/repo'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("open", "closed", "all"):
            raise ValueError("status must be 'open', 'closed', or 'all'")
        return v


class CreateIssueInput(BaseModel):
    repo: str = Field(description="Repository in format 'owner/repo'")
    title: str = Field(description="Issue title")
    body: str = Field(default="", description="Issue body/description")
    labels: Optional[list[str]] = Field(default=None, description="List of label names")

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: str) -> str:
        if not re.match(r"^[\w.-]+/[\w.-]+$", v):
            raise ValueError("repo must be in format 'owner/repo'")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title cannot be empty")
        return v.strip()


class CloseIssueInput(BaseModel):
    repo: str = Field(description="Repository in format 'owner/repo'")
    issue_number: int = Field(gt=0, description="Issue number to close")

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: str) -> str:
        if not re.match(r"^[\w.-]+/[\w.-]+$", v):
            raise ValueError("repo must be in format 'owner/repo'")
        return v


class AddCommentInput(BaseModel):
    repo: str = Field(description="Repository in format 'owner/repo'")
    issue_number: int = Field(gt=0, description="Issue number to comment on")
    comment: str = Field(description="Comment text")

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: str) -> str:
        if not re.match(r"^[\w.-]+/[\w.-]+$", v):
            raise ValueError("repo must be in format 'owner/repo'")
        return v

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("comment cannot be empty")
        return v.strip()


class AssignIssueInput(BaseModel):
    repo: str = Field(description="Repository in format 'owner/repo'")
    issue_number: int = Field(gt=0, description="Issue number to assign")
    assignee: str = Field(description="GitHub username to assign the issue to")

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: str) -> str:
        if not re.match(r"^[\w.-]+/[\w.-]+$", v):
            raise ValueError("repo must be in format 'owner/repo'")
        return v

    @field_validator("assignee")
    @classmethod
    def validate_assignee(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("assignee cannot be empty")
        return v.strip()
