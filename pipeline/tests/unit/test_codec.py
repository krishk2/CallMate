from callmate_pipeline.media.codec import pcm16_to_ulaw, ulaw_to_pcm16


def test_ulaw_pcm_roundtrip_is_lossy_but_stable():
    # mu-law is a lossy codec; round-tripping twice should be a fixed point.
    original_ulaw = bytes([0x00, 0x7F, 0xFF, 0x80])
    pcm = ulaw_to_pcm16(original_ulaw)
    back_to_ulaw = pcm16_to_ulaw(pcm)
    assert pcm16_to_ulaw(ulaw_to_pcm16(back_to_ulaw)) == back_to_ulaw


def test_silence_byte_decodes_near_zero():
    pcm = ulaw_to_pcm16(bytes([0xFF]))
    sample = int.from_bytes(pcm, byteorder="little", signed=True)
    assert abs(sample) < 50
