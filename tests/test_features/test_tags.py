from features.tags import process

def test_tags_process_with_handle_payload():
    handle_payload = {
        'rule': {'feature': ['tags']},
        'claude': {'prompt': '/tags todo help'}
    }

    result = process(handle_payload)

    assert isinstance(result, str)
    assert 'tags todo' in result.lower()

def test_tags_process_non_tags_command():
    handle_payload = {
        'rule': {},
        'claude': {'prompt': 'hello'}
    }

    result = process(handle_payload)
    assert result is None
