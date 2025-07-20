import pytest
from socialModules.moduleRules import moduleRules, ConfigError
import os
from unittest.mock import patch, MagicMock

# Utility to create a temporary configuration file

def make_config_file(tmp_path, content):
    config_file = tmp_path / ".rssBlogs"
    config_file.write_text(content)
    return str(config_file)

def test_missing_url(tmp_path):
    # Missing 'url' key
    config_content = """
    [blog1]
    service = reddit
    reddit = user
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules()
    with pytest.raises(ConfigError):
        rules.checkRules(configFile=config_file)

def test_valid_config(tmp_path):
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = reddit
    reddit = user
    posts = posts
    direct = telegram
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules()
    rules.checkRules(configFile=config_file)
    # There should be a source named 'blog1' in available
    assert any('blog1' in v['name'] for v in rules.available.values())
    # There should be rules for reddit
    assert any('reddit' in str(src) for src in rules.rules)

def test_no_duplicates(tmp_path):
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = reddit
    reddit = user
    posts = posts
    direct = telegram
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules()
    rules.checkRules(configFile=config_file)
    # There should be no duplicates in sources
    srcs = [d['src'] for v in rules.available.values() for d in v['data']]
    assert len(srcs) == len(set(srcs))

def test_empty_url(tmp_path):
    config_content = """
    [blog1]
    url =
    service = reddit
    reddit = user
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules()
    with pytest.raises(ConfigError):
        rules.checkRules(configFile=config_file)

def test_multiple_sections(tmp_path):
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = reddit
    reddit = user
    posts = posts
    direct = telegram

    [blog2]
    url = http://another.com/rss
    service = mastodon
    mastodon = user2
    posts = posts
    direct = slack
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules()
    rules.checkRules(configFile=config_file)
    names = [v['name'] for v in rules.available.values()]
    assert 'blog1' in names
    assert 'blog2' in names

def test_non_numeric_max(tmp_path):
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = reddit
    reddit = user
    max = notanumber
    posts = posts
    direct = telegram
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules()
    rules.checkRules(configFile=config_file)
    more = [d['more'] for v in rules.available.values() for d in v['data']]
    assert any('max' in m for m in more)

def test_duplicate_destinations(tmp_path):
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = reddit
    reddit = user
    posts = posts
    direct = telegram
    direct = telegram
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules()
    # We expect a configuration error due to duplicate keys
    with pytest.raises(ConfigError):
        rules.checkRules(configFile=config_file)

def make_basic_rules():
    rules = moduleRules()
    # Simulate minimal rules and metadata
    rules.rules = {'src1': ['action1', 'action2'], 'src2': ['action3']}
    rules.more = {'src1': {}, 'src2': {}}
    rules.args = MagicMock()
    rules.args.checkBlog = ""
    rules.args.simmulate = False
    rules.args.noWait = False
    rules.args.timeSlots = 1
    return rules

def test_executeRules_calls_executeAction():
    rules = make_basic_rules()
    called = []
    def fake_single_action(scheduled_action):
        called.append(scheduled_action)
        return "ok"
    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules(max_workers=2)
    assert len(called) == 3  # 3 actions

def test_executeRules_respects_hold():
    rules = make_basic_rules()
    rules.more['src1'] = {"hold": "yes"}
    called = []
    def fake_single_action(scheduled_action):
        called.append(scheduled_action)
        return "ok"
    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules()
    assert len(called) == 1  # Only src2/action3

def test_executeRules_handles_exceptions():
    rules = make_basic_rules()
    def fake_single_action(scheduled_action):
        if scheduled_action['rule_action'] == 'action2':
            raise Exception("fail")
        return "ok"
    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules()

def test_executeRules_with_checkBlog():
    rules = make_basic_rules()
    rules.args.checkBlog = "src1"
    called = []
    def fake_single_action(scheduled_action):
        called.append(scheduled_action)
        return "ok"
    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules()
    # Only actions from src1
    assert all(a['rule_key'] == 'src1' for a in called) 