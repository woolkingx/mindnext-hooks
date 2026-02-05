from utils.matcher import match

def test_match_no_match_field():
    """沒有 match 欄位時，默認匹配"""
    handle_payload = {
        'rule': {'name': 'test'},
        'claude': {'prompt': 'test'}
    }
    assert match(handle_payload) == True

def test_match_string_regex():
    """字串 match 使用 regex"""
    handle_payload = {
        'rule': {'match': 'git.*commit'},
        'claude': {'tool_input': {'command': 'git commit -m "test"'}}
    }
    assert match(handle_payload) == True

    handle_payload['claude']['tool_input']['command'] = 'ls -la'
    assert match(handle_payload) == False
