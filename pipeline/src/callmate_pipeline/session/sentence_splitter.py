"""Turns a streamed reply (reply.delta tokens) into speakable chunks, so TTS can start before
the full reply has arrived (docs/HANDOFF.md §6.1.6): emit as soon as a sentence ends, or —
for the very first chunk only — once at least `MIN_WORDS_BEFORE_SPEAKING` words have buffered.
"""

from __future__ import annotations

import re

MIN_WORDS_BEFORE_SPEAKING = 8
_SENTENCE_END_RE = re.compile(r"[.!?]+(?:\s|$)")


class SentenceSplitter:
    def __init__(self) -> None:
        self._buffer = ""
        self._emitted_first_chunk = False

    def feed(self, delta: str) -> list[str]:
        self._buffer += delta
        chunks: list[str] = []
        while (chunk := self._take_ready_chunk()) is not None:
            chunks.append(chunk)
        return chunks

    def flush(self) -> str | None:
        remaining = self._buffer.strip()
        self._buffer = ""
        return remaining or None

    def _take_ready_chunk(self) -> str | None:
        match = _SENTENCE_END_RE.search(self._buffer)
        if match:
            end = match.end()
            chunk, self._buffer = self._buffer[:end].strip(), self._buffer[end:]
            self._emitted_first_chunk = True
            return chunk or None

        if not self._emitted_first_chunk and len(self._buffer.split()) >= MIN_WORDS_BEFORE_SPEAKING:
            cut = self._buffer.rfind(" ")
            if cut == -1:
                return None
            chunk, self._buffer = self._buffer[:cut].strip(), self._buffer[cut:]
            self._emitted_first_chunk = True
            return chunk or None

        return None
