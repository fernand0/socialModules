import pytest
from moduleRules import moduleRules, ConfigError
import os

# Utilidad para crear un archivo de configuración temporal
def make_config_file(tmp_path, content):
    config_file = tmp_path / ".rssBlogs"
    config_file.write_text(content)
    return str(config_file)

def test_missing_url(tmp_path):
    # Falta la clave 'url'
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
    # Debe haber una fuente llamada 'blog1' en available
    assert any('blog1' in v['name'] for v in rules.available.values())
    # Debe haber reglas para reddit
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
    # No debe haber duplicados en las fuentes
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
    # Esperamos un error de configuración por claves duplicadas
    with pytest.raises(ConfigError):
        rules.checkRules(configFile=config_file) 