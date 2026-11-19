from callmate_pipeline.session.sentence_splitter import SentenceSplitter


def test_emits_on_sentence_end():
    splitter = SentenceSplitter()
    assert splitter.feed("Hi there.") == ["Hi there."]


def test_emits_first_chunk_after_min_words_without_punctuation():
    splitter = SentenceSplitter()
    chunks = splitter.feed("one two three four five six seven eight nine")
    assert chunks == ["one two three four five six seven eight"]


def test_does_not_emit_short_first_chunk_without_sentence_end():
    splitter = SentenceSplitter()
    assert splitter.feed("one two three") == []


def test_second_chunk_waits_for_sentence_end_even_if_long():
    splitter = SentenceSplitter()
    splitter.feed("First sentence here.")
    assert splitter.feed("one two three four five six seven eight nine ten") == []


def test_flush_returns_remaining_buffer():
    splitter = SentenceSplitter()
    splitter.feed("too short")
    assert splitter.flush() == "too short"
    assert splitter.flush() is None


def test_feed_across_multiple_deltas():
    splitter = SentenceSplitter()
    chunks: list[str] = []
    for token in ["Hi ", "there", ", ", "how are you", "?"]:
        chunks += splitter.feed(token)
    assert chunks == ["Hi there, how are you?"]
