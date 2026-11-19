from callmate_brain.persona.tone import build_tone_directives
from callmate_contracts.rest import ToneSettings


def test_low_conciseness_and_empathy_are_terse():
    directives = build_tone_directives(
        ToneSettings(conciseness=1, empathy=1), caller_is_known=True
    )
    assert "one short sentence" in directives[0]
    assert "neutral" in directives[1].lower()


def test_unknown_caller_defaults_to_formal_under_auto():
    directives = build_tone_directives(
        ToneSettings(formality="auto"), caller_is_known=False
    )
    assert any("formally" in d for d in directives)


def test_known_caller_under_auto_is_not_forced_formal():
    directives = build_tone_directives(
        ToneSettings(formality="auto"), caller_is_known=True
    )
    assert not any("formally" in d for d in directives)


def test_code_mixing_directive_only_with_multiple_languages():
    directives = build_tone_directives(
        ToneSettings(languages=["en-IN", "te-IN"], code_mixing=True),
        caller_is_known=True,
    )
    assert any("code-mixing" in d for d in directives)

    directives_single = build_tone_directives(
        ToneSettings(languages=["en-IN"], code_mixing=True), caller_is_known=True
    )
    assert not any("code-mixing" in d for d in directives_single)
