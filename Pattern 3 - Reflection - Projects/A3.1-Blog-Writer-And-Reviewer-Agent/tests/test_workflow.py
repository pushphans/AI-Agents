from unittest.mock import patch
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage
import pytest

from main import app
from app.models.schemas import BlogRequest, BlogResponse, GeneratedBlog, EvaluationResult


class TestSchemas:
    def test_blog_request_defaults(self):
        req = BlogRequest(topic="AI")
        assert req.topic == "AI"
        assert req.max_iterations == 3

    def test_blog_request_custom_max_iterations(self):
        req = BlogRequest(topic="AI", max_iterations=5)
        assert req.max_iterations == 5

    def test_blog_response_success(self):
        resp = BlogResponse(
            success=True,
            blog_content="blog content",
            iterations_taken=2,
            evaluation="pass",
            feedback="looks good",
        )
        assert resp.success is True
        assert resp.blog_content == "blog content"

    def test_blog_response_failure(self):
        resp = BlogResponse(
            success=False,
            iterations_taken=3,
            evaluation="fail",
            feedback="needs improvement",
        )
        assert resp.success is False
        assert resp.blog_content is None

    def test_generated_blog(self):
        gb = GeneratedBlog(blog_content="some blog")
        assert gb.blog_content == "some blog"

    def test_evaluation_result_pass(self):
        er = EvaluationResult(evaluation="pass", feedback="good")
        assert er.evaluation == "pass"
        assert er.feedback == "good"

    def test_evaluation_result_fail(self):
        er = EvaluationResult(evaluation="fail", feedback="bad")
        assert er.evaluation == "fail"


class TestWorkflow:
    @patch("app.agent.workflow.generate_llm")
    @patch("app.agent.workflow.evaluate_llm")
    def test_pass_on_first_try(self, mock_eval_llm, mock_gen_llm):
        mock_gen_llm.invoke.return_value = GeneratedBlog(
            blog_content="This is a great blog about AI in healthcare."
        )
        mock_eval_llm.invoke.return_value = EvaluationResult(
            evaluation="pass", feedback="All criteria met."
        )

        from app.agent.workflow import graph

        result = graph.invoke({
            "messages": [HumanMessage(content="AI in healthcare")],
            "current_iteration": 0,
            "max_iterations": 3,
            "evaluation": "fail",
            "feedback": "",
        })

        assert result["evaluation"] == "pass"
        assert result["current_iteration"] == 1

    @patch("app.agent.workflow.generate_llm")
    @patch("app.agent.workflow.evaluate_llm")
    def test_fail_then_pass(self, mock_eval_llm, mock_gen_llm):
        mock_gen_llm.invoke.side_effect = [
            GeneratedBlog(blog_content="First draft of blog."),
            GeneratedBlog(blog_content="Improved version of the blog with more depth."),
        ]
        mock_eval_llm.invoke.side_effect = [
            EvaluationResult(evaluation="fail", feedback="Too short, needs more depth."),
            EvaluationResult(evaluation="pass", feedback="Now it meets all criteria."),
        ]

        from app.agent.workflow import graph

        result = graph.invoke({
            "messages": [HumanMessage(content="AI in healthcare")],
            "current_iteration": 0,
            "max_iterations": 3,
            "evaluation": "fail",
            "feedback": "",
        })

        assert result["evaluation"] == "pass"
        assert result["current_iteration"] == 2

    @patch("app.agent.workflow.generate_llm")
    @patch("app.agent.workflow.evaluate_llm")
    def test_max_retries_exhausted(self, mock_eval_llm, mock_gen_llm):
        mock_gen_llm.invoke.side_effect = [
            GeneratedBlog(blog_content="Blog draft 1."),
            GeneratedBlog(blog_content="Blog draft 2."),
            GeneratedBlog(blog_content="Blog draft 3."),
        ]
        mock_eval_llm.invoke.side_effect = [
            EvaluationResult(evaluation="fail", feedback="Poor quality."),
            EvaluationResult(evaluation="fail", feedback="Still poor."),
            EvaluationResult(evaluation="fail", feedback="Not good enough."),
        ]

        from app.agent.workflow import graph

        result = graph.invoke({
            "messages": [HumanMessage(content="AI in healthcare")],
            "current_iteration": 0,
            "max_iterations": 3,
            "evaluation": "fail",
            "feedback": "",
        })

        assert result["evaluation"] == "fail"
        assert result["current_iteration"] == 3


class TestAPI:
    @patch("app.agent.workflow.generate_llm")
    @patch("app.agent.workflow.evaluate_llm")
    def test_generate_blog_endpoint_pass(self, mock_eval_llm, mock_gen_llm):
        mock_gen_llm.invoke.return_value = GeneratedBlog(
            blog_content="This is a great blog about AI in healthcare."
        )
        mock_eval_llm.invoke.return_value = EvaluationResult(
            evaluation="pass", feedback="All criteria met."
        )

        client = TestClient(app)
        response = client.post(
            "/api/generate-blog",
            json={"topic": "AI in healthcare"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["iterations_taken"] == 1
        assert data["blog_content"] is not None
        assert data["evaluation"] == "pass"

    @patch("app.agent.workflow.generate_llm")
    @patch("app.agent.workflow.evaluate_llm")
    def test_generate_blog_endpoint_max_retries(self, mock_eval_llm, mock_gen_llm):
        mock_gen_llm.invoke.side_effect = [
            GeneratedBlog(blog_content="Blog draft 1."),
            GeneratedBlog(blog_content="Blog draft 2."),
            GeneratedBlog(blog_content="Blog draft 3."),
        ]
        mock_eval_llm.invoke.side_effect = [
            EvaluationResult(evaluation="fail", feedback="Poor quality."),
            EvaluationResult(evaluation="fail", feedback="Still poor."),
            EvaluationResult(evaluation="fail", feedback="Not good enough."),
        ]

        client = TestClient(app)
        response = client.post(
            "/api/generate-blog",
            json={"topic": "AI", "max_iterations": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["iterations_taken"] == 3
        assert data["evaluation"] == "fail"

    def test_generate_blog_missing_topic(self):
        client = TestClient(app)
        response = client.post(
            "/api/generate-blog",
            json={},
        )
        assert response.status_code == 422
