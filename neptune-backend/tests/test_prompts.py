from app.services import prompts


def test_topic_prompt_includes_ids():
    notes = [{"id": "1", "content": "alpha"}, {"id": "2", "content": "beta"}]
    prompt = prompts.topic_extraction_prompt(notes)
    assert "NoteID: 1" in prompt
    assert "NoteID: 2" in prompt


def test_relationship_prompt_pairs():
    pairs = [{"a": "foo", "b": "bar"}]
    prompt = prompts.relationship_prompt(pairs)
    assert "foo | bar" in prompt
