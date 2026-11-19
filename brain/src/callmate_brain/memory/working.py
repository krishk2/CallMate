"""Current call's turns, in-process only — never persisted directly (docs/HANDOFF.md §7.1.4).
`memory/writer.py` decides what, if anything, graduates to long-term storage after the call.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkingMemory:
    turns: list[tuple[str, str]] = field(default_factory=list)  # (role, text)

    def add_caller_turn(self, text: str) -> None:
        self.turns.append(("user", text))

    def add_agent_turn(self, text: str) -> None:
        self.turns.append(("assistant", text))

    def trim_last_agent_turn(self, actually_heard: str) -> None:
        """On agent.interrupted: replace the last agent turn with only what the caller
        actually heard before cutting in, so memory matches what really happened on the call.
        """
        for i in range(len(self.turns) - 1, -1, -1):
            if self.turns[i][0] == "assistant":
                self.turns[i] = ("assistant", actually_heard)
                return

    def recent(self, n: int) -> list[tuple[str, str]]:
        return self.turns[-n:]

    def transcript(self) -> str:
        return "\n".join(f"{role}: {text}" for role, text in self.turns)
