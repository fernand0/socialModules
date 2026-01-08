import time  # Import time for mocking getNextTime
from unittest.mock import MagicMock, patch

import pytest

from socialModules.moduleRules import ConfigError, moduleRules


@pytest.fixture
def mock_rules_args():
    """Provides a MagicMock args object for moduleRules tests."""
    mock_args = MagicMock()
    mock_args.verbose = False
    mock_args.timeSlots = 0
    mock_args.noWait = False
    mock_args.checkBlog = None
    mock_args.simmulate = False
    return mock_args


# Utility to create a temporary configuration file


def make_config_file(tmp_path, content):
    config_file = tmp_path / ".rssBlogs"
    config_file.write_text(content)
    return str(config_file)


def test_missing_url(tmp_path, mock_rules_args):
    # Missing 'url' key
    config_content = """
    [blog1]
    service = reddit
    reddit = user
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules(args=mock_rules_args)
    with pytest.raises(ConfigError):
        rules.checkRules(configFile=config_file)


def test_valid_config(tmp_path, mock_rules_args):
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = reddit
    reddit = user
    posts = posts
    direct = telegram
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules(args=mock_rules_args)
    rules.checkRules(configFile=config_file)
    # There should be a source named 'reddit' in available (service name)
    assert any("reddit" in v["name"] for v in rules.available.values())
    # There should be rules for reddit
    assert any("reddit" in str(src) for src in rules.rules)


def test_no_duplicates(tmp_path, mock_rules_args):
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = reddit
    reddit = user
    posts = posts
    direct = telegram
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules(args=mock_rules_args)
    rules.checkRules(configFile=config_file)
    # There should be no duplicates in sources
    srcs = [d["src"] for v in rules.available.values() for d in v["data"]]
    assert len(srcs) == len(set(srcs))


def test_empty_url(tmp_path, mock_rules_args):
    config_content = """
    [blog1]
    url =
    service = reddit
    reddit = user
    """
    config_file = make_config_file(tmp_path, config_content)
    rules = moduleRules(args=mock_rules_args)
    with pytest.raises(ConfigError):
        rules.checkRules(configFile=config_file)


def test_multiple_sections(tmp_path, mock_rules_args):
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
    rules = moduleRules(args=mock_rules_args)
    rules.checkRules(configFile=config_file)
    names = [v["name"] for v in rules.available.values()]
    assert "reddit" in names
    assert "mastodon" in names


def test_non_numeric_max(tmp_path, mock_rules_args):
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
    rules = moduleRules(args=mock_rules_args)
    rules.checkRules(configFile=config_file)
    more = [d["more"] for v in rules.available.values() for d in v["data"]]
    assert any("max" in m for m in more)


def test_duplicate_destinations(tmp_path, mock_rules_args):
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
    rules = moduleRules(args=mock_rules_args)
    # We expect a configuration error due to duplicate keys
    with pytest.raises(ConfigError):
        rules.checkRules(configFile=config_file)


def make_basic_rules(tmp_path, mock_rules_args):
    rules = moduleRules(args=mock_rules_args)
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = rss
    rss = src_nick
    posts = posts
    direct = telegram
    telegram = dst_account_1
    """
    config_file = make_config_file(tmp_path, config_content)
    rules.checkRules(configFile=config_file)
    rules.args = MagicMock(verbose=True)
    rules.args.checkBlog = ""
    rules.args.simmulate = False
    rules.args.noWait = True
    rules.args.timeSlots = 1
    return rules


# Mock API instance for consistent behavior across tests
mock_api_instance = MagicMock()
mock_api_instance.fileNameBase.return_value = "/tmp/mock_file"
mock_api_instance.getLastLink.return_value = "mock_last_link"
mock_api_instance.getNextTime.return_value = (
    time.time(),
    100.0,
)  # Mock current time and sleep time
mock_api_instance.getNick.return_value = "mock_nick"
mock_api_instance.getName.return_value = "mock_name"
mock_api_instance.getUrl.return_value = "http://mock.url"
mock_api_instance.getClient.return_value = MagicMock()  # Mock the client object
mock_api_instance.getTime.return_value = (
    60.0  # Mock getTime to return a float (e.g., 60 minutes)
)
mock_api_instance.getLastTimePublished.return_value = (
    time.time() - 3600
)  # Mock last published time (e.g., 1 hour ago)
mock_api_instance.setPostsType.return_value = None
mock_api_instance.setMoreValues.return_value = None
mock_api_instance.setUrl.return_value = None
mock_api_instance.getMax.return_value = 1


@patch("socialModules.configMod.getModule", return_value=mock_api_instance)
@patch("socialModules.configMod.getApi", return_value=mock_api_instance)
@patch("socialModules.moduleRules.moduleRules._execute_single_action")
@patch("socialModules.moduleRules.moduleRules.readConfigSrc")
@patch("socialModules.moduleRules.moduleRules.readConfigDst")
def test_executeRules_calls_executeAction(
    mock_read_config_dst,
    mock_read_config_src,
    mock_execute_single_action,
    mock_get_api,
    mock_get_module,
    tmp_path,
    mock_rules_args,
):
    mock_api_src_instance = MagicMock()
    mock_api_src_instance.getUrl.return_value = "http://mock.url"
    mock_api_src_instance.setPostsType.return_value = None
    mock_api_src_instance.setMoreValues.return_value = None
    mock_api_src_instance.indent = ""
    mock_api_src_instance.getPostLink.return_value = "mock_post_link"
    mock_api_src_instance.getPosts.return_value = []
    mock_api_src_instance.getPostAction.return_value = "delete"

    mock_api_dst_instance = MagicMock()
    mock_api_dst_instance.getClient.return_value = MagicMock()
    mock_api_dst_instance.getNextTime.return_value = (time.time(), 100.0)
    mock_api_dst_instance.getTime.return_value = 60.0
    mock_api_dst_instance.getLastTimePublished.return_value = time.time() - 3600
    mock_api_dst_instance.setNextTime.return_value = None
    mock_api_dst_instance.getMax.return_value = 1
    mock_api_dst_instance.publishPost.return_value = "OK. Published!"
    mock_api_dst_instance.updateLastLink.return_value = "OK"
    mock_api_dst_instance.fileNameBase.return_value = "/tmp/mock_file"

    mock_read_config_src.return_value = mock_api_src_instance
    mock_read_config_dst.return_value = mock_api_dst_instance

    rules = make_basic_rules(tmp_path, mock_rules_args)
    rules.executeRules(max_workers=2)
    assert mock_execute_single_action.call_count == 1


@patch("socialModules.configMod.getModule", return_value=mock_api_instance)
@patch("socialModules.configMod.getApi", return_value=mock_api_instance)
@patch("socialModules.moduleRules.moduleRules._execute_single_action")
@patch("socialModules.moduleRules.moduleRules.readConfigSrc")
@patch("socialModules.moduleRules.moduleRules.readConfigDst")
def test_executeRules_respects_hold(
    mock_read_config_dst,
    mock_read_config_src,
    mock_execute_single_action,
    mock_get_api,
    mock_get_module,
    tmp_path,
    mock_rules_args,
):
    mock_api_src_instance = MagicMock()
    mock_api_src_instance.getUrl.return_value = "http://mock.url"
    mock_api_src_instance.setPostsType.return_value = None
    mock_api_src_instance.setMoreValues.return_value = None
    mock_api_src_instance.indent = ""
    mock_api_src_instance.getPostLink.return_value = "mock_post_link"
    mock_api_src_instance.getPosts.return_value = []
    mock_api_src_instance.getPostAction.return_value = "delete"

    mock_api_dst_instance = MagicMock()
    mock_api_dst_instance.getClient.return_value = MagicMock()
    mock_api_dst_instance.getNextTime.return_value = (time.time(), 100.0)
    mock_api_dst_instance.getTime.return_value = 60.0
    mock_api_dst_instance.getLastTimePublished.return_value = time.time() - 3600
    mock_api_dst_instance.setNextTime.return_value = None
    mock_api_dst_instance.getMax.return_value = 1
    mock_api_dst_instance.publishPost.return_value = "OK. Published!"
    mock_api_dst_instance.updateLastLink.return_value = "OK"
    mock_api_dst_instance.fileNameBase.return_value = "/tmp/mock_file"

    mock_read_config_src.return_value = mock_api_src_instance
    mock_read_config_dst.return_value = mock_api_dst_instance

    rules = make_basic_rules(tmp_path, mock_rules_args)
    rules.more[("rss", "set", "src_nick", "posts")] = {"hold": "yes"}
    rules.executeRules()
    assert mock_execute_single_action.call_count == 1


@patch("socialModules.configMod.getModule", return_value=mock_api_instance)
@patch("socialModules.configMod.getApi", return_value=mock_api_instance)
def test_executeRules_handles_exceptions(
    mock_get_api, mock_get_module, tmp_path, mock_rules_args
):
    rules = make_basic_rules(tmp_path, mock_rules_args)

    def fake_single_action(scheduled_action):
        if scheduled_action["rule_action"] == "action2":
            raise Exception("fail")
        return "ok"

    with patch(
        "socialModules.moduleRules.moduleRules._execute_single_action",
        side_effect=fake_single_action,
    ):
        rules.executeRules()


@patch("socialModules.configMod.getModule", return_value=mock_api_instance)
@patch("socialModules.configMod.getApi", return_value=mock_api_instance)
def test_executeRules_with_checkBlog(
    mock_get_api, mock_get_module, tmp_path, mock_rules_args
):
    rules = moduleRules(args=mock_rules_args)
    config_content = """
    [blog1]
    url = http://example.com/rss
    service = rss
    rss = src_nick
    posts = posts
    direct = telegram
    telegram = dst_account_1

    [blog2]
    url = http://another.com/rss
    service = mastodon
    mastodon = user2
    posts = posts
    direct = slack
    """
    config_file = make_config_file(tmp_path, config_content)
    rules.checkRules(configFile=config_file)
    rules.args = mock_rules_args
    rules.args.checkBlog = "rss0"  # Filter for rss0 (corresponding to blog1)
    rules.args.simmulate = False
    rules.args.noWait = True
    rules.args.timeSlots = 1

    called = []

    def fake_single_action(scheduled_action):
        called.append(scheduled_action)
        return "ok"

    with patch(
        "socialModules.moduleRules.moduleRules._execute_single_action",
        side_effect=fake_single_action,
    ):
        rules.executeRules()

    # Only actions from blog1 should be called
    assert len(called) == 1
    assert all(action["rule_metadata"]["section_name"] == "blog1" for action in called)


@patch("socialModules.moduleRules.getApi", return_value=None)
def test_readConfigSrc_fail(mock_get_api, mock_rules_args):
    rules = moduleRules(args=mock_rules_args)
    src = ("rss", "set", "some_nick", "posts")
    more = {}
    apiSrc = rules.readConfigSrc("", src, more)
    assert apiSrc is None


@patch("socialModules.moduleRules.getApi", return_value=None)
def test_readConfigDst_fail(mock_get_api, mock_rules_args):
    rules = moduleRules(args=mock_rules_args)
    action = ("direct", "post", "some_service", "some_account")
    more = {}
    apiSrc = MagicMock()
    apiDst = rules.readConfigDst("", action, more, apiSrc)
    assert apiDst is None


def make_basic_scheduled_action():
    # Helper to create a basic scheduled_action dictionary for testing
    return {
        "rule_key": ("rss", "set", "src_nick", "posts"),
        "rule_metadata": {},
        "rule_action": ("direct", "post", "telegram", "dst_account_1"),
        "rule_index": 0,
        "action_index": 0,
        "args": MagicMock(simmulate=False, timeSlots=1, noWait=True),
        "simmulate": False,
        "name_action": "[rss0]",
        "nameA": "----------[rss0]> Action 0:",
        "timeSlots": 1,
        "noWait": True,
    }


@patch("socialModules.moduleRules.moduleRules.readConfigSrc", return_value=None)
def test_execute_single_action_readConfigSrc_fail(
    mock_read_config_src, tmp_path, mock_rules_args
):
    rules = moduleRules(args=mock_rules_args)
    # Mock rules.args and rules.more as they are expected by _execute_single_action
    mock_rules_args.simmulate = False
    mock_rules_args.timeSlots = 1
    mock_rules_args.noWait = True
    rules.more = {}

    scheduled_action = make_basic_scheduled_action()
    result = rules._execute_single_action(scheduled_action)

    assert result["success"] is False
    assert "error" in result
    assert "Source Error. No client for" in result["error"] or "No execution" in result["error"]


@patch("socialModules.moduleRules.moduleRules.readConfigSrc", return_value=MagicMock())
@patch(
    "socialModules.moduleRules.moduleRules.readConfigDst",
    return_value=MagicMock(getClient=MagicMock(return_value=None)),
)
def test_execute_single_action_readConfigDst_fail(
    mock_read_config_dst, mock_read_config_src, tmp_path, mock_rules_args
):
    rules = moduleRules(args=mock_rules_args)
    # Mock rules.args and rules.more as they are expected by _execute_single_action
    mock_rules_args.simmulate = False
    mock_rules_args.timeSlots = 1
    mock_rules_args.noWait = True
    rules.more = {}

    scheduled_action = make_basic_scheduled_action()
    result = rules._execute_single_action(scheduled_action)

    assert result["success"] is False
    assert "error" in result
    assert "client for" in result["error"] or "No execution" in result["error"]
