"""Lecture 1: ask the LLM questions, with token counts and conversation history.

Based on app/ask.py from the course repo (matsuolab/lecture-ai-engineering-2026).
Two changes from the original:

1. Lecture 1 exercise (the TODO): print the input and output token counts after
   every call, read from response.usage_metadata.
2. Homework 1, Implementation level: keep the conversation history so that
   follow-up questions work (interactive chat mode).

Usage:
    uv run python -m app.ask "What is LoRA?"          # one question, no history
    uv run python -m app.ask --chat                   # chat that remembers earlier turns
    uv run python -m app.ask --chat "What is LoRA?"   # ask one question, then keep chatting
    AIE_MODEL=gemini-3.8-flash uv run python -m app.ask --chat

Why the history has to be kept by us: the Gemini API is stateless. Every call
only knows what is inside `contents`, so a follow-up such as "explain that in
one sentence" only works if we send the earlier questions and answers again.
"""

import argparse
from dataclasses import dataclass

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

EXIT_COMMANDS = ("/exit", "/quit")

CHAT_HELP = (
    "Chat mode. The model remembers earlier turns.\n"
    "  /history  show the saved turns\n"
    "  /reset    forget the history and start over\n"
    "  /exit     quit (Ctrl-D also works)\n"
)


class EmptyResponseError(Exception):
    """The model returned no text (for example it was blocked or stopped early)."""


@dataclass
class TokenUsage:
    """Token counts for one call, or the running total for a session."""

    input: int = 0
    output: int = 0
    thinking: int = 0

    @classmethod
    def from_metadata(cls, usage) -> "TokenUsage":
        """Build from response.usage_metadata. Missing fields (or None) count as 0."""

        def count(name: str) -> int:
            return getattr(usage, name, None) or 0

        return cls(
            input=count("prompt_token_count"),
            output=count("candidates_token_count"),
            thinking=count("thoughts_token_count"),
        )

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            self.input + other.input,
            self.output + other.output,
            self.thinking + other.thinking,
        )

    def describe(self) -> str:
        text = f"input {self.input}, output {self.output}"
        if self.thinking:
            # Thinking tokens are billed as output but are not part of the visible answer.
            text += f" (+{self.thinking} thinking)"
        return text


def _turn(role: str, text: str) -> types.Content:
    return types.Content(role=role, parts=[types.Part.from_text(text=text)])


class Conversation:
    """A chat with the model that keeps its own history.

    A turn is only saved after the call succeeded, so a failed call (rate limit,
    503, empty answer) never leaves a dangling question in the history and the
    same question can simply be retried.
    """

    def __init__(self, client: genai.Client | None = None, model: str = MODEL):
        self.client = client if client is not None else genai.Client(api_key=get_api_key())
        self.model = model
        self.history: list[types.Content] = []
        self.last_usage = TokenUsage()
        self.total_usage = TokenUsage()

    @property
    def turns(self) -> int:
        """Number of saved question and answer pairs."""
        return len(self.history) // 2

    def reset(self) -> None:
        """Forget the history. The running token total is kept."""
        self.history.clear()

    def send(self, question: str) -> str:
        user_turn = _turn("user", question)
        response = self.client.models.generate_content(
            model=self.model,
            contents=[*self.history, user_turn],
        )

        # Tokens were spent even if the answer turns out to be empty, so count them first.
        self.last_usage = TokenUsage.from_metadata(response.usage_metadata)
        self.total_usage = self.total_usage + self.last_usage

        answer = response.text
        if not answer:
            raise EmptyResponseError("The model returned no text, so this turn was not saved.")

        self.history += [user_turn, _turn("model", answer)]
        return answer


def run_once(conversation: Conversation, question: str) -> str:
    """Single question: print the answer and its token counts."""
    answer = conversation.send(question)
    print(answer)
    print(f"\n[tokens] {conversation.last_usage.describe()}")
    return answer


def _shorten(text: str, width: int = 80) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 3] + "..."


def _print_history(conversation: Conversation) -> None:
    if not conversation.history:
        print("[history is empty]")
        return
    for content in conversation.history:
        who = "you  " if content.role == "user" else "model"
        print(f"  {who}: {_shorten(content.parts[0].text)}")


def chat_loop(conversation: Conversation, first_question: str | None = None, input_fn=input) -> None:
    """Interactive loop. `input_fn` can be replaced in tests."""
    print(CHAT_HELP)
    pending = first_question
    while True:
        if pending is not None:
            line, pending = pending, None
            print(f"you> {line}")
        else:
            try:
                line = input_fn("you> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

        line = line.strip()
        if not line:
            continue
        if line.lower() in EXIT_COMMANDS:
            break
        if line == "/reset":
            conversation.reset()
            print("[history cleared]")
            continue
        if line == "/history":
            _print_history(conversation)
            continue
        if line.startswith("/"):
            print(f"[unknown command: {line.split()[0]}]  (/history, /reset, /exit)")
            continue

        try:
            answer = conversation.send(line)
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            print("[the question was not saved to the history, so you can retry it]")
            continue
        except EmptyResponseError as e:
            print(f"[{e}]")
            continue
        except KeyboardInterrupt:
            print("\n[interrupted]")
            break

        print(f"\nmodel> {answer}\n")
        print(
            f"[tokens] this turn: {conversation.last_usage.describe()} | "
            f"session total: {conversation.total_usage.describe()} | "
            f"history: {conversation.turns} turn(s)\n"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the plain LLM a question")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument(
        "-c",
        "--chat",
        action="store_true",
        help="interactive chat that keeps the conversation history",
    )
    args = parser.parse_args()

    conversation = Conversation()
    print(f"[model] {MODEL}")

    if args.chat:
        chat_loop(conversation, first_question=args.question)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[question] {question}\n")
    try:
        run_once(conversation, question)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    except EmptyResponseError as e:
        print(e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
