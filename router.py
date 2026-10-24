import logging
import re
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

logger = logging.getLogger(__name__)

AgentName = Literal[
    "summarize_agent",
    "highlight_agent",
    "social_agent",
    "qa_agent",
]


class RoutingDecision(BaseModel):
    agent: AgentName


def keyword_route(query: str) -> AgentName:
    """Route a query by intent keywords when the LLM router is unavailable."""
    text = re.sub(r"\s+", " ", query.casefold()).strip()

    social_terms = (
        "social media", "socail media", "linkedin", "linkdin", "instagram",
        "instgram", "insta", "facebook", "tweet", "twitter", "twiter",
        "hashtag", "hashtags", "caption", "captions", "post", "posts",
        "reel", "reels",
    )
    highlight_terms = (
        "highlight", "highlights", "key point", "key points", "key takeaway",
        "key takeaways", "main takeaway", "main takeaways", "best moment",
        "best moments", "top moment", "top moments", "clip", "clips",
        "timestamp", "timestamps", "extract", "notable quote",
        "important moment", "important moments", "main points", "insight",
        "insights",
    )
    question_terms = (
        "what", "why", "how", "who", "when", "where", "which", "explain",
        "define", "tell me", "kya", "kyun", "kaise", "kaun",
    )
    summary_terms = (
        "summarize", "sumarize", "summary", "summery", "recap", "overview",
        "brief", "tl;dr", "gist", "saar", "whole episode", "full episode",
        "whole conversation", "full interview",
    )

    def contains_term(terms: tuple[str, ...]) -> bool:
        return any(
            re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text)
            for term in terms
        )

    if contains_term(social_terms):
        return "social_agent"
    negated_highlight = re.search(
        r"\b(?:don't need|do not need|no|not)\b.{0,24}\b(?:highlights?|clips?)\b",
        text,
    )
    if contains_term(highlight_terms) and not negated_highlight:
        return "highlight_agent"
    negated_summary = re.search(
        r"\b(?:no|not|don't need|do not need)\b.{0,24}\b"
        r"(?:summarize|summary|summaries|recap|recaps)\b",
        text,
    )
    if contains_term(summary_terms) and not negated_summary:
        return "summarize_agent"
    if text.endswith("?") or contains_term(question_terms):
        return "qa_agent"
    return "summarize_agent"


def route(query: str) -> AgentName:
    """Use Groq structured output to select an agent, falling back to keywords."""
    try:
        from llm import get_llm

        structured_llm = get_llm(mode="precise").with_structured_output(
            RoutingDecision
        )
        decision = structured_llm.invoke([
            SystemMessage(
                content=(
                    "Classify the user's request into exactly one agent. "
                    "Use summarize_agent for an overview or recap, "
                    "highlight_agent for key moments or extracted points, "
                    "social_agent for social-media content, and qa_agent "
                    "for a specific question."
                )
            ),
            HumanMessage(content=query),
        ])
        return decision.agent
    except Exception as exc:
        logger.warning(
            "[ROUTER] Structured routing failed; using keyword fallback: %s",
            exc,
        )
        return keyword_route(query)
