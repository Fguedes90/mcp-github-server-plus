"""Common types and validators for GitHub MCP tools."""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

# Tipos comuns
SortDirection = Literal["asc", "desc"]
GitRef = str  # Branch, tag ou commit SHA
IsoDateTime = str  # Data/hora no formato ISO 8601
CommitSha = str  # SHA de commit (7-40 caracteres)
TreeSha = str  # SHA de tree (40 caracteres)

# Regex patterns comuns
COMMIT_SHA_PATTERN = r"^[a-f0-9]{7,40}$"  # SHA-1 hash format (7-40 chars)
TREE_SHA_PATTERN = r"^[a-f0-9]{40}$"  # SHA-1 hash format (40 chars)
RELATIVE_PATH_PATTERN = r"^[^/].*"  # Não pode começar com /
ISO_DATETIME_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"  # ISO 8601
BRANCH_NAME_PATTERN = r"^(?:feature/|bugfix/|release/|hotfix/)[a-zA-Z0-9-_/]+$"
FILE_EXTENSION_PATTERN = r"^\.?[a-zA-Z0-9]+$"

# Campos comuns
def sha_field(*, description: str, min_length: int = 7, max_length: int = 40, pattern: str = COMMIT_SHA_PATTERN, **kwargs) -> Field:
    """Campo para SHA de Git."""
    field_kwargs = {
        "description": description,
        "validate_default": True,
        "pre": True,
        "strict": True,
        "min_length": min_length,
        "max_length": max_length,
        "pattern": pattern,
    }
    field_kwargs.update(kwargs)
    return Field(**field_kwargs)

def path_field(*, description: str, pattern: str = RELATIVE_PATH_PATTERN, **kwargs) -> Field:
    """Campo para caminhos relativos."""
    field_kwargs = {
        "description": description,
        "validate_default": True,
        "pre": True,
        "strict": True,
        "min_length": 1,
        "pattern": pattern,
    }
    field_kwargs.update(kwargs)
    return Field(**field_kwargs)

def date_field(*, description: str, pattern: str = ISO_DATETIME_PATTERN, **kwargs) -> Field:
    """Campo para datas ISO 8601."""
    field_kwargs = {
        "description": description,
        "validate_default": True,
        "pre": True,
        "strict": True,
        "pattern": pattern,
    }
    field_kwargs.update(kwargs)
    return Field(**field_kwargs)

def string_field(*, description: str, min_length: int = 1, max_length: Optional[int] = None, **kwargs) -> Field:
    """Campo para strings com validação básica."""
    field_kwargs = {
        "description": description,
        "validate_default": True,
        "pre": True,
        "strict": True,
        "min_length": min_length,
    }
    if max_length is not None:
        field_kwargs["max_length"] = max_length
    field_kwargs.update(kwargs)
    return Field(**field_kwargs)

def list_field(*, description: str, min_items: int = 1, item_type: Any = str, **kwargs) -> Field:
    """Campo para listas."""
    field_kwargs = {
        "description": description,
        "validate_default": True,
        "pre": True,
        "strict": True,
        "min_items": min_items,
        "item_type": item_type,
    }
    field_kwargs.update(kwargs)
    return Field(**field_kwargs)

# Classes base comuns
class BaseInput(BaseModel):
    """Classe base para todos os inputs."""
    
    model_config = {
        "json_schema_extra": {
            "examples": []  # Deve ser sobrescrito nas classes filhas
        }
    }

class GitRefInput(BaseInput):
    """Input com referência Git (branch/tag/commit)."""
    ref: Optional[GitRef] = string_field(
        description="Git reference (branch, tag, commit)",
        json_schema_extra={"examples": ["main"]},
        validation_alias="ref",
        default=None
    )

class DateRangeInput(BaseInput):
    """Input com intervalo de datas."""
    since: Optional[IsoDateTime] = date_field(
        description="Start date (ISO 8601 format)",
        json_schema_extra={"examples": ["2024-01-01T00:00:00Z"]},
        validation_alias="since",
        default=None
    )
    until: Optional[IsoDateTime] = date_field(
        description="End date (ISO 8601 format)",
        json_schema_extra={"examples": ["2024-02-29T23:59:59Z"]},
        validation_alias="until",
        default=None
    )

class SortableInput(BaseInput):
    """Input com ordenação."""
    direction: Optional[SortDirection] = Field(
        default="desc",
        description="Sort direction"
    )

class PersonInfo(BaseModel):
    """Informações de pessoa (autor/committer)."""
    name: str = string_field(
        description="Person's name",
        json_schema_extra={"examples": ["John Doe"]}
    )
    email: str = string_field(
        description="Person's email",
        json_schema_extra={"examples": ["john@example.com"]},
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    date: IsoDateTime = date_field(
        description="Timestamp (ISO 8601)",
        json_schema_extra={"examples": ["2024-02-29T12:00:00Z"]}
    ) 