# tracer.py
# ─────────────────────────────────────────────────────────────────────
# Langfuse Python SDK observability wrapper for MediaNova.
#
# SDK key facts:
#   - Client:    from langfuse import get_client  -> get_client()
#   - Tracing:   langfuse.start_as_current_observation(as_type="span", ...)
#                NOT langfuse.trace()  -- that method was removed in v3
#   - LangChain: from langfuse.langchain import CallbackHandler
#                NOT from langfuse.callback import CallbackHandler
#   - Env var:   LANGFUSE_BASE_URL  (NOT LANGFUSE_HOST)
#
# Zero-impact when LANGFUSE keys are not set --
# all methods become no-ops so the app runs normally in dev.
# ─────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import contextmanager, nullcontext
from typing import Any, Generator

logger = logging.getLogger(__name__)

# Try to import Langfuse.
try:
    from langfuse import get_client, propagate_attributes
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    _LANGFUSE_AVAILABLE = True
except ImportError:
    _LANGFUSE_AVAILABLE = False
    logger.info("[TRACER] langfuse not installed -- observability disabled.")


# ── Null implementations (used when Langfuse is unavailable/disabled) ─

class _NullSpan:
    def __init__(self): self.id = str(uuid.uuid4())
    def end(self, **kwargs): pass
    def update(self, **kwargs): pass
    def event(self, **kwargs): pass
    def score(self, **kwargs): pass
    def generation(self, **kwargs): return _NullSpan()
    def span(self, **kwargs): return _NullSpan()
    def __enter__(self): return self
    def __exit__(self, *a): pass


class _NullTracer:
    @contextmanager
    def trace(self, name: str, **kwargs):
        yield _NullSpan()
    def langchain_handler(self, **kwargs): return None
    def current_trace_id(self, fallback: str | None = None) -> str | None:
        return fallback
    @contextmanager
    def observation(self, name: str, **kwargs):
        yield _NullSpan()
    def log_guardrail_event(self, *args, **kwargs): pass
    def log_routing_decision(self, *args, **kwargs): pass
    def log_rag_retrieval(self, *args, **kwargs): pass
    def score_response(self, *args, **kwargs): pass
    def flush(self): pass


# ── Real Langfuse tracer ──────────────────────────────────────────────

class MediaNovaTracer:
    """
    Wrapper around the Langfuse Python SDK.

    v4 tracing API (langfuse.trace() no longer exists):
        langfuse = get_client()
        with langfuse.start_as_current_observation(as_type="span", name="...") as span:
            span.update(output="...")
        langfuse.flush()

    LangChain/LangGraph callback:
        from langfuse.langchain import CallbackHandler
        handler = CallbackHandler()
        graph.invoke(state, config={"callbacks": [handler]})
    """

    def __init__(self):
        self._client = get_client()
        logger.info("[TRACER] Langfuse observability initialized.")

    @contextmanager
    def trace(
        self,
        name: str,
        query: str = "",
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> Generator[Any, None, None]:
        """
        Context manager that wraps one application turn in a Langfuse agent trace.

        Usage:
            with tracer.trace("run_agent", query=q, session_id=sid) as span:
                handler = tracer.langchain_handler()
                graph.invoke(state, config={"callbacks": [handler]})
        """
        start = time.perf_counter()
        attributes = {
            "session_id": session_id,
            "metadata": {"application": "medianova", **(metadata or {})},
            "tags": ["medianova"],
            "environment": os.getenv("LANGFUSE_TRACING_ENVIRONMENT", "development"),
            "trace_name": name,
        }
        if user_id:
            attributes["user_id"] = user_id
        try:
            with propagate_attributes(**attributes):
                with self._client.start_as_current_observation(
                    as_type="agent",
                    name=name,
                    input={"query": query},
                    metadata=metadata or {},
                ) as root_span:
                    try:
                        yield root_span
                    except Exception as e:
                        root_span.update(
                            output={"error": str(e)},
                            level="ERROR",
                            status_message=str(e),
                        )
                        raise
                    finally:
                        elapsed = time.perf_counter() - start
                        root_span.update(
                            metadata={"latency_seconds": round(elapsed, 3)}
                        )
        finally:
            self.flush()

    def current_trace_id(self, fallback: str | None = None) -> str | None:
        """Return the active Langfuse trace ID for scores and UI feedback."""
        try:
            return self._client.get_current_trace_id() or fallback
        except Exception as e:
            logger.warning(f"[TRACER] Could not read active trace ID: {e}")
            return fallback

    @contextmanager
    def observation(
        self,
        name: str,
        *,
        as_type: str = "span",
        input: Any = None,
        metadata: dict | None = None,
        trace_context: dict[str, str] | None = None,
        session_id: str | None = None,
    ):
        attributes = (
            propagate_attributes(session_id=session_id)
            if session_id
            else nullcontext()
        )
        with attributes:
            with self._client.start_as_current_observation(
                trace_context=trace_context,
                as_type=as_type,
                name=name,
                input=input,
                metadata=metadata,
            ) as observation:
                    try:
                        yield observation
                    except Exception as e:
                        observation.update(level="ERROR", status_message=str(e))
                        raise

    def langchain_handler(
        self,
        trace_id: str | None = None,
        session_id: str | None = None,
        parent_span_id: str | None = None,
    ):
        """
        Returns a LangChain CallbackHandler for automatic LLM/tool tracing.
        Pass to graph.invoke(state, config={"callbacks": [handler]}).
        """
        try:
            trace_context = None
            if trace_id:
                trace_context = {"trace_id": trace_id}
                if parent_span_id:
                    trace_context["parent_span_id"] = parent_span_id
            return LangfuseCallbackHandler(trace_context=trace_context)
        except Exception as e:
            logger.warning(f"[TRACER] Could not create CallbackHandler: {e}")
            return None

    def log_guardrail_event(self, trace: Any, stage: str, passed: bool, reason: str = "") -> None:
        try:
            with self._client.start_as_current_observation(
                as_type="span",
                name=f"guardrail_{stage}",
                input={"stage": stage},
                level="DEFAULT" if passed else "WARNING",
            ) as span:
                span.update(output={"passed": passed, "reason": reason})
        except Exception as e:
            logger.debug(f"[TRACER] guardrail event failed: {e}")

    def log_routing_decision(self, trace: Any, query: str, decision: str, latency_ms: float) -> None:
        with self.observation(
            "route-query",
            as_type="span",
            input={"query": query},
            metadata={"latency_ms": round(latency_ms, 2)},
        ) as span:
            span.update(output={"routed_to": decision})

    def log_rag_retrieval(self, trace: Any, query: str, chunks: list[str], latency_ms: float) -> None:
        with self.observation(
            "retrieve-context",
            as_type="retriever",
            input={"query": query},
            metadata={"latency_ms": round(latency_ms, 2)},
        ) as span:
            span.update(output={
                "num_chunks": len(chunks),
                "context_characters": sum(len(chunk) for chunk in chunks),
            })

    def score_response(self, trace_id: str, name: str, value: float, comment: str = "") -> None:
        # Langfuse v4: .score() was renamed to .create_score()
        # .score() silently did nothing — scores appeared in terminal but never in dashboard
        try:
            self._client.create_score(
                trace_id=trace_id,
                name=name,
                value=value,
                data_type="NUMERIC",
                comment=comment,
            )
        except Exception as e:
            logger.warning(f"[TRACER] Could not record score '{name}': {e}")

    def flush(self) -> None:
        try:
            self._client.flush()
        except Exception as e:
            logger.warning(f"[TRACER] Could not flush Langfuse events: {e}")


# ── Singleton factory ──────────────────────────────────────────────────

_tracer: "MediaNovaTracer | _NullTracer | None" = None


def get_tracer() -> "MediaNovaTracer | _NullTracer":
    """
    Return the singleton tracer instance.

    Required env vars:
        LANGFUSE_PUBLIC_KEY = pk-lf-...
        LANGFUSE_SECRET_KEY = sk-lf-...
        LANGFUSE_BASE_URL   = https://cloud.langfuse.com   <- NOT LANGFUSE_HOST
    """
    global _tracer
    if _tracer is not None:
        return _tracer

    langfuse_configured = (
        _LANGFUSE_AVAILABLE
        and os.environ.get("LANGFUSE_SECRET_KEY")
        and os.environ.get("LANGFUSE_PUBLIC_KEY")
    )

    if langfuse_configured:
        try:
            _tracer = MediaNovaTracer()
        except Exception as e:
            logger.warning(f"[TRACER] Langfuse init failed, using null tracer: {e}")
            _tracer = _NullTracer()
    else:
        logger.info("[TRACER] Langfuse not configured -- using null tracer.")
        _tracer = _NullTracer()

    return _tracer