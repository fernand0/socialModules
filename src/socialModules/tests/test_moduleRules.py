import pytest
from socialModules.moduleRules import moduleRules, ConfigError
import os
from unittest.mock import patch, MagicMock
import time # Import time for mocking getNextTime

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
    # There should be a source named 'reddit' in available (service name)
    assert any("reddit" in v["name"] for v in rules.available.values())
    # There should be rules for reddit
    assert any("reddit" in str(src) for src in rules.rules)


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
    srcs = [d["src"] for v in rules.available.values() for d in v["data"]]
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
    names = [v["name"] for v in rules.available.values()]
    assert "reddit" in names
    assert "mastodon" in names


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
    more = [d["more"] for v in rules.available.values() for d in v["data"]]
    assert any("max" in m for m in more)


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
    rules.rules = {"src1": ["action1", "action2"], "src2": ["action3"]}
    rules.more = {"src1": {}, "src2": {}}
    rules.args = MagicMock()
    rules.args.checkBlog = ""
    rules.args.simmulate = False
    rules.args.noWait = True
    rules.args.timeSlots = 1
    return rules

# Mock API instance for consistent behavior across tests
mock_api_instance = MagicMock()
mock_api_instance.fileNameBase.return_value = "/tmp/mock_file"
mock_api_instance.getLastLink.return_value = "mock_last_link"
mock_api_instance.getNextTime.return_value = (time.time(), 100.0) # Mock current time and sleep time
mock_api_instance.getNick.return_value = "mock_nick"
mock_api_instance.getName.return_value = "mock_name"
mock_api_instance.getUrl.return_value = "http://mock.url"
mock_api_instance.getClient.return_value = MagicMock() # Mock the client object
mock_api_instance.getTime.return_value = 60.0 # Mock getTime to return a float (e.g., 60 minutes)
mock_api_instance.getLastTimePublished.return_value = time.time() - 3600 # Mock last published time (e.g., 1 hour ago)


@patch('socialModules.configMod.getModule', return_value=mock_api_instance)
@patch('socialModules.configMod.getApi', return_value=mock_api_instance)
def test_executeRules_calls_executeAction(mock_get_api, mock_get_module):
    rules = make_basic_rules()
    called = []

    def fake_single_action(scheduled_action):
        called.append(scheduled_action)
        return "ok"

    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules(max_workers=2)
    assert len(called) == 3  # 3 actions


@patch('socialModules.configMod.getModule', return_value=mock_api_instance)
@patch('socialModules.configMod.getApi', return_value=mock_api_instance)
def test_executeRules_respects_hold(mock_get_api, mock_get_module):
    rules = make_basic_rules()
    rules.more["src1"] = {"hold": "yes"}
    called = []

    def fake_single_action(scheduled_action):
        called.append(scheduled_action)
        return "ok"

    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules()
    assert len(called) == 1  # Only src2/action3


@patch('socialModules.configMod.getModule', return_value=mock_api_instance)
@patch('socialModules.configMod.getApi', return_value=mock_api_instance)
def test_executeRules_handles_exceptions(mock_get_api, mock_get_module):
    rules = make_basic_rules()

    def fake_single_action(scheduled_action):
        if scheduled_action["rule_action"] == "action2":
            raise Exception("fail")
        return "ok"

    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules()


@patch('socialModules.configMod.getModule', return_value=mock_api_instance)
@patch('socialModules.configMod.getApi', return_value=mock_api_instance)
def test_executeRules_with_checkBlog(mock_get_api, mock_get_module):
    rules = make_basic_rules()
    rules.args.checkBlog = "src1"
    called = []

    def fake_single_action(scheduled_action):
        called.append(scheduled_action)
        return "ok"

    with patch('socialModules.moduleRules.moduleRules._execute_single_action', side_effect=fake_single_action):
        rules.executeRules()
    # Only actions from src1
    assert all(a["rule_key"] == "src1" for a in called)

@patch('socialModules.moduleRules.getApi', return_value=None)
<<<<<<< HEAD
def test_readConfigSrc_fail(mock_get_api):
    rules = moduleRules()
    src = ('rss', 'set', 'some_nick', 'posts')
    more = {}
    apiSrc = rules.readConfigSrc('', src, more)
    assert apiSrc is None

@patch('socialModules.moduleRules.getApi', return_value=None)
def test_readConfigDst_fail(mock_get_api):
    rules = moduleRules()
    action = ('direct', 'post', 'some_service', 'some_account')
    more = {}
    apiSrc = MagicMock()
    apiDst = rules.readConfigDst('', action, more, apiSrc)
    assert apiDst is None

@patch('socialModules.moduleRules.moduleRules.readConfigSrc', return_value=None)
def test_prepare_actions_readConfigSrc_fail(mock_read_config_src):
    rules = make_basic_rules()
    scheduled_actions = rules._prepare_actions(rules.args, None)
    assert len(scheduled_actions) == 0

@patch('socialModules.moduleRules.moduleRules.readConfigSrc', return_value=MagicMock())
@patch('socialModules.moduleRules.moduleRules.readConfigDst', return_value=None)
def test_prepare_actions_readConfigDst_fail(mock_read_config_dst, mock_read_config_src):
    rules = make_basic_rules()
    scheduled_actions = rules._prepare_actions(rules.args, None)
    assert len(scheduled_actions) == 0
=======

def test_readConfigSrc_fail(mock_get_api):

    rules = moduleRules()

    src = ('rss', 'set', 'some_nick', 'posts')

    more = {}

    apiSrc = rules.readConfigSrc('', src, more)

    assert apiSrc is None



@patch('socialModules.moduleRules.getApi', return_value=None)



def test_readConfigDst_fail(mock_get_api):



    rules = moduleRules()



    action = ('direct', 'post', 'some_service', 'some_account')



    more = {}



    apiSrc = MagicMock()



    apiDst = rules.readConfigDst('', action, more, apiSrc)



    assert apiDst is None







@patch('socialModules.moduleRules.moduleRules.readConfigSrc', return_value=None)



def test_prepare_actions_readConfigSrc_fail(mock_read_config_src):



    rules = make_basic_rules()



    scheduled_actions = rules._prepare_actions(rules.args, None)



    assert len(scheduled_actions) == 0







@patch('socialModules.moduleRules.moduleRules.readConfigSrc', return_value=MagicMock())



@patch('socialModules.moduleRules.moduleRules.readConfigDst', return_value=None)



def test_prepare_actions_readConfigDst_fail(mock_read_config_dst, mock_read_config_src):



    rules = make_basic_rules()



    scheduled_actions = rules._prepare_actions(rules.args, None)



    assert len(scheduled_actions) == 0




>>>>>>> master
