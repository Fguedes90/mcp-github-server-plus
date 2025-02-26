"""Tests for utility functions."""

import pytest
from datetime import datetime, timezone, timedelta
from base64 import b64encode, b64decode
from mcp_pygithub.common.utils import (
    encode_content,
    decode_content,
    format_datetime,
    parse_datetime,
    validate_branch_name,
    validate_file_path,
    validate_commit_message,
    validate_email,
    parse_repository_name,
    format_api_url,
    sanitize_ref_name,
    parse_link_header
)

def test_encode_content():
    """Test content encoding."""
    # Test basic encoding
    content = "Hello, World!"
    encoded = encode_content(content)
    assert encoded == b64encode(content.encode("utf-8")).decode("utf-8")
    
    # Test empty string
    assert encode_content("") == b64encode(b"").decode("utf-8")
    
    # Test different encoding
    content = "Hello, 世界!"
    encoded = encode_content(content, encoding="utf-16")
    assert encoded == b64encode(content.encode("utf-16")).decode("utf-8")
    
    # Test special characters
    content = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    encoded = encode_content(content)
    assert encoded == b64encode(content.encode("utf-8")).decode("utf-8")

def test_decode_content():
    """Test content decoding."""
    # Test basic decoding
    content = "Hello, World!"
    encoded = b64encode(content.encode("utf-8")).decode("utf-8")
    decoded = decode_content(encoded)
    assert decoded == content
    
    # Test empty string
    assert decode_content(b64encode(b"").decode("utf-8")) == ""
    
    # Test different encoding
    content = "Hello, 世界!"
    encoded = b64encode(content.encode("utf-16")).decode("utf-8")
    decoded = decode_content(encoded, encoding="utf-16")
    assert decoded == content
    
    # Test special characters
    content = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    encoded = b64encode(content.encode("utf-8")).decode("utf-8")
    decoded = decode_content(encoded)
    assert decoded == content
    
    # Test invalid base64
    with pytest.raises(Exception):
        decode_content("invalid-base64")

def test_validate_branch_name():
    """Test branch name validation."""
    # Test valid branch names
    assert validate_branch_name("main")
    assert validate_branch_name("feature/new-feature")
    assert validate_branch_name("fix-123")
    assert validate_branch_name("release-1.0.0")
    assert validate_branch_name("user/repo")
    
    # Test invalid branch names
    assert not validate_branch_name(".hidden")  # Starts with dot
    assert not validate_branch_name("branch/")  # Ends with slash
    assert not validate_branch_name("branch..name")  # Contains double dots
    assert not validate_branch_name("branch@{1}")  # Contains @{
    assert not validate_branch_name("branch\x00name")  # Contains control character
    assert not validate_branch_name("branch name")  # Contains space
    assert not validate_branch_name("branch~1")  # Contains tilde
    assert not validate_branch_name("branch^1")  # Contains caret
    assert not validate_branch_name("branch:1")  # Contains colon
    assert not validate_branch_name("branch?1")  # Contains question mark
    assert not validate_branch_name("branch*1")  # Contains asterisk
    assert not validate_branch_name("branch[1]")  # Contains square brackets

def test_validate_file_path():
    """Test file path validation."""
    # Test valid file paths
    assert validate_file_path("file.txt")
    assert validate_file_path("dir/file.txt")
    assert validate_file_path("path/to/file.txt")
    assert validate_file_path("file-with-dashes.txt")
    assert validate_file_path("file_with_underscores.txt")
    assert validate_file_path(".gitignore")  # Hidden files are allowed
    assert validate_file_path("path.with.dots/file.txt")
    
    # Test invalid file paths
    assert not validate_file_path("/absolute/path")  # Starts with slash
    assert not validate_file_path("path/../file")  # Contains parent directory reference
    assert not validate_file_path("path/./file")  # Contains current directory reference
    assert not validate_file_path("file\x00name")  # Contains control character
    assert not validate_file_path("")  # Empty path

def test_validate_commit_message():
    """Test commit message validation."""
    # Test valid commit messages
    assert validate_commit_message("Initial commit")
    assert validate_commit_message("Fix bug in login form")
    assert validate_commit_message("Add new feature\n\nDetailed description")
    assert validate_commit_message("Merge branch 'feature' into 'main'")
    assert validate_commit_message("  Commit with spaces  ")  # Spaces are trimmed
    
    # Test invalid commit messages
    assert not validate_commit_message("")  # Empty message
    assert not validate_commit_message("   ")  # Only whitespace
    assert not validate_commit_message("#comment")  # Starts with #
    assert not validate_commit_message("  #comment")  # Starts with # after trim

def test_format_datetime():
    """Test datetime formatting."""
    # Test with specific datetime
    dt = datetime(2024, 3, 14, 12, 34, 56, tzinfo=timezone.utc)
    assert format_datetime(dt) == "2024-03-14T12:34:56+00:00"
    
    # Test with current time
    now = datetime.now(timezone.utc)
    formatted = format_datetime()
    parsed = datetime.fromisoformat(formatted)
    assert (parsed - now).total_seconds() < 1  # Within 1 second
    
    # Test with different timezone
    dt = datetime(2024, 3, 14, 12, 34, 56, tzinfo=timezone(timedelta(hours=2)))
    assert format_datetime(dt) == "2024-03-14T12:34:56+02:00"

def test_parse_datetime():
    """Test datetime parsing."""
    # Test basic ISO format
    dt_str = "2024-03-14T12:34:56+00:00"
    dt = parse_datetime(dt_str)
    assert dt.year == 2024
    assert dt.month == 3
    assert dt.day == 14
    assert dt.hour == 12
    assert dt.minute == 34
    assert dt.second == 56
    assert dt.tzinfo == timezone.utc
    
    # Test with Z timezone
    dt_str = "2024-03-14T12:34:56Z"
    dt = parse_datetime(dt_str)
    assert dt.tzinfo == timezone.utc
    
    # Test with different timezone
    dt_str = "2024-03-14T12:34:56+02:00"
    dt = parse_datetime(dt_str)
    assert dt.tzinfo.utcoffset(None).total_seconds() == 7200  # 2 hours
    
    # Test with microseconds
    dt_str = "2024-03-14T12:34:56.789123+00:00"
    dt = parse_datetime(dt_str)
    assert dt.microsecond == 789123 