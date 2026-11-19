from callmate_pipeline.media.vad import BargeInDetector, VoiceActivityDetector


class ScriptedVAD(VoiceActivityDetector):
    def __init__(self, script: list[bool]) -> None:
        self._script = list(script)

    def is_speech(self, pcm16_chunk: bytes) -> bool:
        return self._script.pop(0)


def test_fires_once_after_min_consecutive_speech_frames():
    # 20ms frames, 250ms min -> round(250/20) frames needed; exact count isn't the point here
    detector = BargeInDetector(ScriptedVAD([True] * 20), frame_ms=20.0, min_speech_ms=250.0)
    fired_on = [i for i in range(20) if detector.feed(b"\x00\x00")]
    assert len(fired_on) == 1


def test_resets_on_silence():
    detector = BargeInDetector(ScriptedVAD([True, True, False, True, True]), min_speech_ms=60.0)
    results = [detector.feed(b"\x00\x00") for _ in range(5)]
    # 3 consecutive speech frames needed (60ms / 20ms); silence at index 2 resets the count
    assert results == [False, False, False, False, False]


def test_explicit_reset_clears_progress():
    detector = BargeInDetector(ScriptedVAD([True, True]), min_speech_ms=60.0)
    detector.feed(b"\x00\x00")
    detector.reset()
    assert detector.feed(b"\x00\x00") is False
