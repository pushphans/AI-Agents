import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)

# OpenAI pricing per 1K tokens (accurate for gpt-4o-mini)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}

DEFAULT_PRICING = {"input": 0.001, "output": 0.002}


def _get_pricing(model_name: str) -> Dict[str, float]:
    for key, pricing in MODEL_PRICING.items():
        if key in model_name:
            return pricing
    return DEFAULT_PRICING


class ObservabilityCallback(BaseCallbackHandler):
    """Tracks LLM calls, tool executions, latency, and token usage.

    Attach this to a run of the agent workflow to get full observability
    data for that request.
    """

    def __init__(self) -> None:
        self.llm_calls: List[Dict[str, Any]] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self._llm_starts: Dict[UUID, float] = {}
        self._tool_starts: Dict[UUID, float] = {}
        self._tool_names: Dict[UUID, str] = {}
        self.total_cost: float = 0.0
        self.total_tokens: int = 0
        self.start_time: Optional[float] = None

    # ── Chain (graph) tracking ──

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        if self.start_time is None:
            self.start_time = time.perf_counter()
            name = serialized.get("name", "graph")
            logger.info("[GRAPH START] %s | run_id=%s", name, run_id)

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        if self.start_time is not None:
            elapsed = time.perf_counter() - self.start_time
            self.start_time = None
            logger.info("[GRAPH END] latency=%.2fs | run_id=%s", elapsed, run_id)

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.error("[GRAPH ERROR] %s | run_id=%s", error, run_id)

    # ── Chat model / LLM tracking ──

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._llm_starts[run_id] = time.perf_counter()
        name = serialized.get("name", "chat_model")
        msg_count = len(messages[0]) if messages else 0
        logger.info("[LLM START] %s | messages=%d | run_id=%s", name, msg_count, run_id)

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        start = self._llm_starts.pop(run_id, None)
        elapsed = time.perf_counter() - start if start else 0.0

        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        model_name = llm_output.get("model_name", "unknown")

        prompt_tokens = token_usage.get("prompt_tokens", 0) or 0
        completion_tokens = token_usage.get("completion_tokens", 0) or 0
        total_tokens = (prompt_tokens + completion_tokens) or token_usage.get("total_tokens", 0) or 0

        pricing = _get_pricing(model_name)
        cost = (prompt_tokens / 1000.0 * pricing["input"]
                + completion_tokens / 1000.0 * pricing["output"])

        self.total_cost += cost
        self.total_tokens += total_tokens

        call_info = {
            "model": model_name,
            "latency_s": round(elapsed, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": round(cost, 6),
        }
        self.llm_calls.append(call_info)

        logger.info(
            "[LLM END] model=%s | tokens=%d (p=%d c=%d) | latency=%.2fs | cost=$%.6f",
            model_name, total_tokens, prompt_tokens, completion_tokens,
            elapsed, cost,
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._llm_starts.pop(run_id, None)
        logger.error("[LLM ERROR] %s | run_id=%s", error, run_id)

    # ── Tool tracking ──

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._tool_starts[run_id] = time.perf_counter()
        tool_name = serialized.get("name", "unknown")
        self._tool_names[run_id] = tool_name
        input_preview = input_str[:300] + "..." if len(input_str) > 300 else input_str
        logger.info("[TOOL START] %s | input=%s", tool_name, input_preview)

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        start = self._tool_starts.pop(run_id, None)
        tool_name = self._tool_names.pop(run_id, "unknown")
        elapsed = time.perf_counter() - start if start else 0.0

        output_str = str(output) if output is not None else ""
        output_preview = output_str[:300] + "..." if len(output_str) > 300 else output_str

        call_info = {
            "tool": tool_name,
            "latency_s": round(elapsed, 3),
        }
        self.tool_calls.append(call_info)

        logger.info("[TOOL END] %s | latency=%.2fs | output=%s",
                     tool_name, elapsed, output_preview)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        tool_name = self._tool_names.pop(run_id, "unknown")
        self._tool_starts.pop(run_id, None)
        logger.error("[TOOL ERROR] %s | %s", tool_name, error)

    # ── Summary ──

    def summary(self) -> Dict[str, Any]:
        """Return a structured summary of the entire request trace."""
        total_llm_latency = sum(c.get("latency_s", 0) for c in self.llm_calls)
        total_tool_latency = sum(c.get("latency_s", 0) for c in self.tool_calls)
        return {
            "total_llm_calls": len(self.llm_calls),
            "total_tool_calls": len(self.tool_calls),
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "total_llm_latency_s": round(total_llm_latency, 3),
            "total_tool_latency_s": round(total_tool_latency, 3),
        }
