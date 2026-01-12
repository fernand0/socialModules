import pytest
import email
from email.message import EmailMessage
from unittest.mock import MagicMock, patch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from socialModules.moduleSmtp import moduleSmtp


class TestModuleSmtp:
    """Test class for moduleSmtp functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.smtp_module = moduleSmtp()
        self.smtp_module.indent = "  "
        self.smtp_module.user = "test_user"
        self.smtp_module.fromaddr = "test@example.com"
        self.smtp_module.to = "recipient@example.com"
        self.smtp_module.server = "smtp.example.com"
        self.smtp_module.port = "465"
        self.smtp_module.password = "test_password"

    @patch('smtplib.SMTP_SSL')
    def test_publish_api_post_with_title_and_link(self, mock_smtp):
        """Test publishApiPost with title and link arguments."""
        # Mock the SMTP client
        mock_client = MagicMock()
        mock_smtp.return_value = mock_client
        mock_client.sendmail.return_value = {}

        # Set up the module with a mock client
        self.smtp_module.client = mock_client

        # Call publishApiPost with title and link
        title = "Test Title"
        link = "https://example.com"
        comment = "Test comment"
        
        result = self.smtp_module.publishApiPost(title, link, comment)

        # Verify the SMTP client was called correctly
        mock_client.sendmail.assert_called_once()
        args, kwargs = mock_client.sendmail.call_args
        from_addr, to_addr, msg_string = args
        
        # Verify the from and to addresses
        assert from_addr == "test@example.com"
        # When using positional args, destaddr is taken from self.destaddr or self.user
        # Since destaddr wasn't set, it defaults to self.user
        assert to_addr == "test_user"

        # Parse the message to check its content
        msg = email.message_from_string(msg_string)
        assert msg['Subject'] == title
        assert msg['X-URL'] == link

        # Verify the result
        assert result['success'] is True
        assert result['post_url'] == f"mailto:test_user"

    @patch('smtplib.SMTP_SSL')
    def test_publish_api_post_with_kwargs(self, mock_smtp):
        """Test publishApiPost with keyword arguments."""
        import email
        from email.mime.text import MIMEText
        
        # Mock the SMTP client
        mock_client = MagicMock()
        mock_smtp.return_value = mock_client
        mock_client.sendmail.return_value = {}

        # Set up the module with a mock client
        self.smtp_module.client = mock_client

        # Create a mock API and post
        mock_api = MagicMock()
        mock_post = MagicMock()
        mock_api.getPostTitle.return_value = "Test Title from API"
        mock_api.getPostLink.return_value = "https://example.com/api"
        
        # Call publishApiPost with kwargs
        result = self.smtp_module.publishApiPost(post=mock_post, api=mock_api)

        # Verify the SMTP client was called
        mock_client.sendmail.assert_called_once()
        args, kwargs = mock_client.sendmail.call_args
        from_addr, to_addr, msg_string = args
        
        # Verify the from and to addresses
        assert from_addr == "test@example.com"
        assert to_addr == "recipient@example.com"
        
        # Parse the message to check its content
        msg = email.message_from_string(msg_string)
        assert msg['Subject'] == "Test Title from API"
        assert msg['X-URL'] == "https://example.com/api"
        
        # Verify the result
        assert result['success'] is True
        assert result['post_url'] == f"mailto:recipient@example.com"

    @patch('smtplib.SMTP_SSL')
    def test_publish_api_post_with_empty_content(self, mock_smtp):
        """Test publishApiPost with empty content."""
        # Mock the SMTP client
        mock_client = MagicMock()
        mock_smtp.return_value = mock_client

        # Set up the module with a mock client
        self.smtp_module.client = mock_client

        # Call publishApiPost with empty content
        result = self.smtp_module.publishApiPost("", "", "")

        # Verify that error was returned
        assert result['success'] is False
        assert 'error_message' in result
        # When using positional args, the check for empty content happens later
        # after the message is constructed, so the error will be different
        # The sendmail method is still called but returns an error
        mock_client.sendmail.assert_called_once()

    @patch('smtplib.SMTP_SSL')
    def test_publish_api_post_smtp_error(self, mock_smtp):
        """Test publishApiPost when SMTP server returns errors."""
        # Mock the SMTP client to return errors
        mock_client = MagicMock()
        mock_smtp.return_value = mock_client
        mock_client.sendmail.return_value = {"recipient@example.com": (550, "User not found")}

        # Set up the module with a mock client
        self.smtp_module.client = mock_client

        # Call publishApiPost
        result = self.smtp_module.publishApiPost("Test Title", "https://example.com", "Test content")

        # Verify the result contains error information
        assert result['success'] is False
        assert 'error_message' in result
        assert 'SMTP server returned errors' in result['error_message']

    @patch('smtplib.SMTP_SSL')
    def test_publish_api_post_exception_handling(self, mock_smtp):
        """Test publishApiPost exception handling."""
        # Mock the SMTP client to raise an exception
        mock_client = MagicMock()
        mock_smtp.return_value = mock_client
        mock_client.sendmail.side_effect = Exception("SMTP connection failed")

        # Set up the module with a mock client
        self.smtp_module.client = mock_client

        # Call publishApiPost
        result = self.smtp_module.publishApiPost("Test Title", "https://example.com", "Test content")

        # Verify the result contains error information
        assert result['success'] is False
        assert 'error_message' in result
        assert 'failed!' in result['error_message']