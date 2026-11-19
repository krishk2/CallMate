from callmate_brain.reasoning.intent import classify_by_rules, render_classify_system_prompt
from callmate_contracts.enums import Intent


def test_keyword_rule_matches_delivery():
    result = classify_by_rules(
        caller_text="I'm a courier with a package for you",
        contact_relationship=None,
        repeat_calls_in_window=0,
    )
    assert result.intent == Intent.DELIVERY_LOGISTICS


def test_scam_keywords_take_priority_over_relationship():
    result = classify_by_rules(
        caller_text="please share the OTP for KYC verification",
        contact_relationship="family",
        repeat_calls_in_window=0,
    )
    assert result.intent == Intent.SCAM_SUSPECTED


def test_family_relationship_without_keywords_is_personal_casual():
    result = classify_by_rules(
        caller_text="hey what's up", contact_relationship="family", repeat_calls_in_window=0
    )
    assert result.intent == Intent.PERSONAL_CASUAL


def test_work_relationship_without_keywords_is_work():
    result = classify_by_rules(
        caller_text="can we sync tomorrow", contact_relationship="work", repeat_calls_in_window=0
    )
    assert result.intent == Intent.WORK


def test_unknown_caller_no_keywords_defers_to_llm():
    result = classify_by_rules(
        caller_text="hello there", contact_relationship=None, repeat_calls_in_window=0
    )
    assert result.intent is None


def test_classify_system_prompt_lists_all_intent_labels():
    prompt = render_classify_system_prompt()
    for intent in Intent:
        assert intent.value in prompt
