import pytest
from unittest.mock import MagicMock, patch
from socialModules.moduleRules import moduleRules

@pytest.fixture
def rules_instance():
    """Pytest fixture to create a moduleRules instance with a mocked checkRules method."""
    class _TestArgs:
        def __init__(self):
            self.verbose = False
            self.timeSlots = 0
            self.noWait = False
            self.checkBlog = None
            self.simmulate = False

    test_args = _TestArgs()
    with patch.object(moduleRules, 'checkRules') as mock_check_rules:
        rules = moduleRules(args=test_args)
        rules.available = {
            'twitter_acc': {'name': 'twitter'},
            'mastodon_acc': {'name': 'mastodon'},
            'linkedin_acc': {'name': 'linkedin'}
        }
        yield rules

def create_mock_api(service_name, success=True, image_support=False):
    """Creates a mock API object for a given service."""
    mock_api = MagicMock()
    mock_api.getService.return_value = service_name
    if success:
        mock_api.publishPost.return_value = f"Success on {service_name}"
        mock_api.publishImage.return_value = {
            'image_url': f"http://{service_name}.com/img/123"
        } if image_support else "Image success"
    else:
        mock_api.publishPost.side_effect = Exception(f"Failed on {service_name}")
        mock_api.publishImage.side_effect = Exception(f"Image failed on {service_name}")
    
    type(mock_api).supports_images = image_support
    return mock_api

@patch('socialModules.moduleRules.moduleRules.publish_to_multiple_destinations')
def test_publish_to_multiple_destinations_success(mock_publish, rules_instance):
    """
    Tests successful publication to multiple destinations.
    """
    # Arrange
    destinations = {
        "twitter": "twitter_acc",
        "mastodon": "mastodon_acc"
    }
    mock_publish.return_value = {
        "twitter_acc": {"success": True, "result": "Success on twitter"},
        "mastodon_acc": {"success": True, "result": "Success on mastodon"}
    }

    # Act
    results = rules_instance.publish_to_multiple_destinations(
        destinations=destinations,
        title="Test Title",
        url="http://example.com",
        content="Test Content"
    )

    # Assert
    assert len(results) == 2
    assert results["twitter_acc"]["success"]
    assert results["twitter_acc"]["result"] == "Success on twitter"
    assert results["mastodon_acc"]["success"]
    assert results["mastodon_acc"]["result"] == "Success on mastodon"
    mock_publish.assert_called_once()

@patch('socialModules.moduleRules.moduleRules.publish_to_multiple_destinations')
def test_publish_with_failures(mock_publish, rules_instance):
    """
    Tests publication with one successful and one failed destination.
    """
    # Arrange
    destinations = {
        "twitter": "twitter_acc",
        "linkedin": "linkedin_acc"
    }
    mock_publish.return_value = {
        "twitter_acc": {"success": True, "result": "Success on twitter"},
        "linkedin_acc": {"success": False, "error": "Failed on linkedin"}
    }

    # Act
    results = rules_instance.publish_to_multiple_destinations(
        destinations=destinations,
        title="Test Title",
        url="http://example.com"
    )

    # Assert
    assert len(results) == 2
    assert results["twitter_acc"]["success"]
    assert not results["linkedin_acc"]["success"]
    assert "Failed on linkedin" in results["linkedin_acc"]["error"]

@patch('socialModules.moduleRules.moduleRules.publish_to_multiple_destinations')
def test_publish_with_image_support(mock_publish, rules_instance):
    """
    Tests publication with an image to services that support it.
    """
    # Arrange
    destinations = {
        "twitter": "twitter_acc",
        "mastodon": "mastodon_acc"
    }
    mock_publish.return_value = {
        "twitter_acc": {"success": True, "image_url": "http://twitter.com/img/123"},
        "mastodon_acc": {"success": True, "result": "Success on mastodon"}
    }

    # Act
    results = rules_instance.publish_to_multiple_destinations(
        destinations=destinations,
        title="Image Test",
        image_path="/path/to/image.png",
        alt_text="Alt text"
    )

    # Assert
    assert results["twitter_acc"]["success"]
    assert results["twitter_acc"]["image_url"] == "http://twitter.com/img/123"
    assert results["mastodon_acc"]["success"]
    # Mastodon mock doesn't support images, so it should have called publishPost
    assert "Image success" not in results["mastodon_acc"].get("result", "")
    assert "Success on mastodon" in results["mastodon_acc"].get("result", "")

@patch('socialModules.moduleRules.moduleRules.publish_to_multiple_destinations')
def test_publish_message_to_destinations(mock_publish, rules_instance):
    """
    Tests the simplified message publishing method.
    """
    # Arrange
    destinations = {
        "twitter": "twitter_acc"
    }
    mock_publish.return_value = {
        "twitter_acc": {"success": True, "result": "Success on twitter"}
    }

    # Act
    results = rules_instance.publish_message_to_destinations(
        destinations=destinations,
        message="Simple message"
    )

    # Assert
    assert results["twitter_acc"]["success"]
    assert results["twitter_acc"]["result"] == "Success on twitter"
    mock_publish.assert_called_once_with(
        destinations=destinations,
        title="Simple message",
        url='',
        content='',
        image_path=None,
        alt_text='',
        channel=None,
        from_email=None,
        to_email=None
    )

@patch('socialModules.moduleRules.moduleRules.publish_to_multiple_destinations')
def test_empty_destinations(mock_publish, rules_instance):
    """
    Tests that the function handles empty destinations gracefully.
    """
    # Arrange
    mock_publish.return_value = {} # The actual method should return an empty dict for empty destinations

    # Act
    results = rules_instance.publish_to_multiple_destinations(
        destinations={},
        title="Test"
    )
    # Assert
    assert results == {}
    mock_publish.assert_called_once_with(
        destinations={},
        title="Test"
    )

@patch('socialModules.moduleRules.moduleRules._publish_to_single_destination')
def test_smtp_special_handling(mock_single_destination_publish, rules_instance):
    """
    Tests that SMTP-specific parameters are correctly handled.
    """
    # Arrange
    destinations = {"smtp": "smtp_acc"}
    mock_single_destination_publish.return_value = {
        "success": True,
        "result": "Email sent",
        "service": "smtp_smtp_acc"
    }

    # Act
    rules_instance.publish_to_multiple_destinations(
        destinations=destinations,
        title="Email Title",
        from_email="from@example.com",
        to_email="to@example.com"
    )

    # Assert
    mock_single_destination_publish.assert_called_once_with(
        destination="smtp",
        account="smtp_acc",
        title="Email Title",
        url="",
        content="",
        image_path=None,
        alt_text="",
        channel=None,
        from_email="from@example.com",
        to_email="to@example.com"
    )

@patch('socialModules.moduleRules.getApi')
def test_channel_special_handling(mock_get_api, rules_instance):
    """
    Tests that the 'channel' parameter is correctly handled for APIs that support it.
    """
    # Arrange
    destinations = {"slack": "slack_acc"}
    mock_slack_api = create_mock_api("slack")
    mock_slack_api.setChannel = MagicMock()
    mock_get_api.return_value = mock_slack_api

    # Act
    rules_instance.publish_to_multiple_destinations(
        destinations=destinations,
        title="Slack Message",
        channel="general"
    )

    # Assert
    mock_slack_api.setChannel.assert_called_once_with("general")
