"""Utility functions for GitHub operations."""

import re
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timezone
from base64 import b64encode, b64decode
from urllib.parse import urlparse, urljoin

def encode_content(content: str, encoding: str = "utf-8") -> str:
    """Encode content for GitHub API.
    
    Args:
        content: Content to encode
        encoding: Content encoding (default: utf-8)
        
    Returns:
        Base64 encoded content
    """
    return b64encode(content.encode(encoding)).decode("utf-8")

def decode_content(content: str, encoding: str = "utf-8") -> str:
    """Decode content from GitHub API.
    
    Args:
        content: Base64 encoded content
        encoding: Content encoding (default: utf-8)
        
    Returns:
        Decoded content
    """
    return b64decode(content.encode("utf-8")).decode(encoding)

def format_datetime(dt: Optional[datetime] = None) -> str:
    """Format datetime for GitHub API.
    
    Args:
        dt: Datetime to format (default: current time)
        
    Returns:
        ISO 8601 formatted datetime string
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()

def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime from GitHub API.
    
    Args:
        dt_str: ISO 8601 formatted datetime string
        
    Returns:
        Parsed datetime
    """
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

def validate_branch_name(name: str) -> bool:
    """Validate branch name.
    
    Args:
        name: Branch name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Branch names must not:
    # - Start with '.'
    # - End with '/'
    # - Contain '..'
    # - Contain '@{'
    # - Contain ASCII control characters
    pattern = r"^(?!\.|\/)(?!.*\.\.)[^\000-\037\177 ~^:?*[\\]+[^.](?<!\.lock)$"
    return bool(re.match(pattern, name))

def validate_tag_name(name: str) -> bool:
    """Validate tag name.
    
    Args:
        name: Tag name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Tag names must not:
    # - Start with '.'
    # - Contain '..'
    # - Contain '@{'
    # - Contain ASCII control characters
    # - End with '.lock'
    pattern = r"^(?!\.)(?!.*\.\.)[^\000-\037\177 ~^:?*[\\]+[^.](?<!\.lock)$"
    return bool(re.match(pattern, name))

def validate_file_path(path: str) -> bool:
    """Validate file path.
    
    Args:
        path: File path to validate
        
    Returns:
        True if valid, False otherwise
    """
    # File paths must not:
    # - Start with '/'
    # - Contain '..'
    # - Contain ASCII control characters
    pattern = r"^(?!\/)(?!.*\.\.)[^\000-\037\177]+$"
    return bool(re.match(pattern, path))

def validate_commit_message(message: str) -> bool:
    """Validate commit message.
    
    Args:
        message: Commit message to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Commit messages must not:
    # - Be empty
    # - Contain only whitespace
    # - Start with '#'
    return bool(message.strip() and not message.strip().startswith("#"))

def validate_email(email: str) -> bool:
    """Validate email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Basic email validation pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def parse_repository_name(full_name: str) -> Tuple[str, str]:
    """Parse repository owner and name from full name.
    
    Args:
        full_name: Full repository name (owner/name)
        
    Returns:
        Tuple of (owner, name)
        
    Raises:
        ValueError: If the name format is invalid
    """
    parts = full_name.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Invalid repository name format. Expected: owner/name")
    return parts[0], parts[1]

def format_api_url(base_url: str, *path_segments: str, **params: str) -> str:
    """Format GitHub API URL.
    
    Args:
        base_url: Base API URL
        path_segments: URL path segments
        params: Query parameters
        
    Returns:
        Formatted URL
    """
    # Join path segments
    url = base_url.rstrip("/")
    for segment in path_segments:
        url = urljoin(url + "/", segment.lstrip("/"))
    
    # Add query parameters
    if params:
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        url = f"{url}?{query}"
    
    return url

def sanitize_ref_name(ref: str) -> str:
    """Sanitize Git reference name.
    
    Args:
        ref: Reference name to sanitize
        
    Returns:
        Sanitized reference name
    """
    # Remove refs/ prefix if present
    ref = ref.removeprefix("refs/")
    
    # Remove heads/ or tags/ prefix if present
    ref = ref.removeprefix("heads/").removeprefix("tags/")
    
    # Replace invalid characters
    ref = re.sub(r"[^\w.-]", "-", ref)
    
    # Remove consecutive dots
    ref = re.sub(r"\.+", ".", ref)
    
    # Remove leading/trailing special characters
    ref = ref.strip(".-")
    
    return ref

def parse_link_header(header: Optional[str]) -> Dict[str, str]:
    """Parse GitHub API Link header.
    
    Args:
        header: Link header value
        
    Returns:
        Dictionary of relation types to URLs
    """
    if not header:
        return {}
    
    links = {}
    for link in header.split(","):
        parts = link.strip().split(";")
        if len(parts) != 2:
            continue
        
        url = parts[0].strip("<>")
        rel = parts[1].strip().split("=")[1].strip('"')
        links[rel] = url
    
    return links 