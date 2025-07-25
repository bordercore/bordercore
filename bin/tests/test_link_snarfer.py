"""
Unit tests for the link-snarfer email processing module.

These tests cover functionality for parsing YouTube and generic emails,
extracting links, filtering unwanted URLs (such as YouTube Shorts), and
ensuring proper submission of link metadata to the Bordercore API.
"""

from email.message import Message
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from link_snarfer import (get_youtube_content, handle_generic_email,
                          handle_youtube_email)

YOUTUBE_EMAIL_BODY = """SomeUploader
This is the video title
https://www.youtube.com/watch?v=abcd1234
"""

YOUTUBE_SHORTS_EMAIL_BODY = """SomeUploader
This is the video title
https://www.youtube.com/shorts/xyz987
"""

GENERIC_EMAIL = """Check this out:
https://example.com/awesome-link
"""

@pytest.fixture(autouse=True)
def suppress_logging() -> Generator[MagicMock, None, None]:
    """
    Automatically patch the logger used in link_snarfer to prevent real logging
    during test runs. This avoids polluting log files with test output.

    Yields:
        MagicMock: A mock logger object.
    """
    with patch("link_snarfer.logger") as mock_logger:
        yield mock_logger

@pytest.fixture
def mock_session() -> MagicMock:
    """
    Provide a mocked requests.Session object with `trust_env` set to None.
    Used to test functions that make HTTP requests without making real network calls.

    Returns:
        MagicMock: A mocked requests.Session instance.
    """
    session = MagicMock()
    session.trust_env = None
    return session

@pytest.fixture
def mock_token() -> str:
    """
    Provide a fake DRF token string to use in tests that require authentication.

    Returns:
        str: A dummy authentication token.
    """
    return "mocked-token"

def build_email_message(body: str) -> Message:
    """
    Create a simple plain-text email message with the given body.

    Args:
        body (str): The raw string payload to use as the message content.

    Returns:
        Message: A plain-text email message instance.
    """
    msg = Message()
    msg.set_payload(body)
    msg.add_header("Content-Type", "text/plain")
    return msg

def test_get_youtube_content_parses_expected_fields() -> None:
    """
    Test that get_youtube_content() correctly extracts the URL and title
    from a Blogtrottr-style YouTube email.
    """
    msg = build_email_message(YOUTUBE_EMAIL_BODY)
    msg.add_header("From", "Blogtrottr <no-reply@blogtrottr.com>")
    parsed = get_youtube_content(msg)
    assert parsed is not None
    assert parsed["url"].startswith("http")
    assert "SomeUploader" in parsed["subject"]
    assert "This is the video title" in parsed["subject"]

@patch("link_snarfer.add_to_bordercore")
def test_handle_youtube_email_calls_post(
    mock_add: MagicMock, mock_session: MagicMock, mock_token: str
) -> None:
    """
    Test that handle_youtube_email() calls add_to_bordercore() exactly once
    when a valid video link is present.
    """
    msg = build_email_message(YOUTUBE_EMAIL_BODY)
    msg.add_header("From", "Blogtrottr <no-reply@blogtrottr.com>")
    handle_youtube_email(msg, mock_session, mock_token)
    mock_add.assert_called_once()
    args, kwargs = mock_add.call_args
    assert args[0]["url"].startswith("http")
    assert args[1] is mock_session
    assert args[2] == mock_token

@patch("link_snarfer.add_to_bordercore")
def test_handle_youtube_shorts_email_calls_post(
        mock_add: MagicMock, mock_session: MagicMock, mock_token: str
) -> None:
    """
    Test that handle_youtube_email() skips calling add_to_bordercore()
    when the video URL is a YouTube Shorts link.
    """
    msg = build_email_message(YOUTUBE_SHORTS_EMAIL_BODY)
    msg.add_header("From", "Blogtrottr <no-reply@blogtrottr.com>")
    handle_youtube_email(msg, mock_session, mock_token)
    mock_add.assert_not_called()

@patch("link_snarfer.parse_title_from_url")
@patch("link_snarfer.add_to_bordercore")
def test_handle_generic_email(
        mock_add: MagicMock,
        mock_parse: MagicMock,
        mock_session: MagicMock,
        mock_token: str
) -> None:
    """
    Test that handle_generic_email() parses a valid link from the email
    body, ignores Shorts URLs, and passes the result to add_to_bordercore().
    """
    mock_parse.return_value = ("https://example.com/awesome-link", "Example Title")
    handle_generic_email(GENERIC_EMAIL, mock_session, mock_token)
    calls = mock_add.call_args_list
    assert len(calls) == 1
    assert "example.com" in calls[0][0][0]["url"]
    assert "youtube.com/shorts" not in calls[0][0][0]["url"]
