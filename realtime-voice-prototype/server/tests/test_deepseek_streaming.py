import json

from app.providers.llm.deepseek_streaming import DeepSeekStreamingTextProvider
from app.providers.llm.turn_completion_judge import DeepSeekTurnCompletionJudge
from app.session.turn_completion import CompletionStatus, TurnCompletionDecision
from app.session.state import ConversationMessage


def test_deepseek_provider_parses_streaming_content_delta() -> None:
    provider = DeepSeekStreamingTextProvider(api_key="test-key")
    payload = {"choices": [{"delta": {"content": "hello"}}]}

    chunk = provider._parse_sse_line(f"data: {json.dumps(payload)}")

    assert chunk == "hello"


def test_deepseek_provider_ignores_null_streaming_content_delta() -> None:
    provider = DeepSeekStreamingTextProvider(api_key="test-key")
    payload = {"choices": [{"delta": {"content": None}}]}

    chunk = provider._parse_sse_line(f"data: {json.dumps(payload)}")

    assert chunk == ""


def test_deepseek_provider_builds_openai_compatible_messages() -> None:
    provider = DeepSeekStreamingTextProvider(api_key="test-key")

    payload = provider._messages_payload(
        [
            ConversationMessage(role="user", text="I want to practice project experience."),
            ConversationMessage(role="assistant", text="Start with one project."),
        ]
    )

    assert payload[0]["role"] == "system"
    assert payload[1] == {"role": "user", "content": "I want to practice project experience."}
    assert payload[2] == {"role": "assistant", "content": "Start with one project."}


def test_deepseek_provider_can_override_system_prompt_per_request() -> None:
    provider = DeepSeekStreamingTextProvider(api_key="test-key", system_prompt="default prompt")

    payload = provider._messages_payload([], system_prompt="structured prompt")

    assert payload[0] == {"role": "system", "content": "structured prompt"}


def test_deepseek_provider_disables_thinking_for_realtime_voice_payload() -> None:
    provider = DeepSeekStreamingTextProvider(api_key="test-key")
    payload = provider._chat_payload([])

    assert payload["thinking"] == {"type": "disabled"}


def test_deepseek_provider_does_not_cap_realtime_voice_tokens() -> None:
    provider = DeepSeekStreamingTextProvider(api_key="test-key")
    payload = provider._chat_payload([])

    assert "max_tokens" not in payload


def test_turn_completion_judge_parses_json_response() -> None:
    judge = DeepSeekTurnCompletionJudge(api_key="test-key")
    body = json.dumps(
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "completion": "incomplete",
                                "confidence": 0.83,
                                "suggested_wait_ms": 18000,
                                "reason": "candidate paused after a connector",
                            }
                        )
                    }
                }
            ]
        }
    )
    fallback = TurnCompletionDecision(CompletionStatus.UNCERTAIN, 0.5, 12000, "fallback")

    decision = judge._parse_response(body, fallback=fallback)

    assert decision.completion is CompletionStatus.INCOMPLETE
    assert decision.confidence == 0.83
    assert decision.suggested_wait_ms == 18000
