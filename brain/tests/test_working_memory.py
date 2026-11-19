from callmate_brain.memory.working import WorkingMemory


def test_trim_last_agent_turn_replaces_most_recent_assistant_turn():
    memory = WorkingMemory()
    memory.add_caller_turn("hi")
    memory.add_agent_turn("Hello there, how can I help you today")
    memory.trim_last_agent_turn("Hello there, how")
    assert memory.turns[-1] == ("assistant", "Hello there, how")


def test_trim_does_not_touch_caller_turns():
    memory = WorkingMemory()
    memory.add_caller_turn("hi")
    memory.add_agent_turn("hello")
    memory.trim_last_agent_turn("he")
    assert memory.turns[0] == ("user", "hi")


def test_recent_returns_last_n_in_order():
    memory = WorkingMemory()
    for i in range(5):
        memory.add_caller_turn(f"turn {i}")
    assert memory.recent(2) == [("user", "turn 3"), ("user", "turn 4")]


def test_transcript_joins_roles_and_text():
    memory = WorkingMemory()
    memory.add_caller_turn("hi")
    memory.add_agent_turn("hello")
    assert memory.transcript() == "user: hi\nassistant: hello"
