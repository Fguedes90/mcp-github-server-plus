# MPC GitHub Python

A Python implementation of GitHub operations using the Model Protocol Context (MPC).

## Features

- Full GitHub API support through PyGithub
- MPC-compliant implementation
- Modern async Python implementation
- Type-safe with strict mypy checking
- Comprehensive test coverage

## Installation

We recommend using [uv](https://github.com/astral-sh/uv) for installation:

```bash
uv venv
uv pip install -e ".[dev]"
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mpc-github-python.git
cd mpc-github-python
```

2. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
uv pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Project Structure

The project follows the implementation order outlined in `implementation-order.md`:

1. Core Infrastructure
   - `repository.py`: Basic repository operations
   - `files.py`: File management operations

2. Basic Operations
   - `branches.py`: Branch management
   - `commits.py`: Commit operations

3. Advanced Features
   - `issues.py`: Issue management
   - `pulls.py`: Pull request operations
   - `actions.py`: GitHub Actions integration
   - `search.py`: Search functionality

## Testing

Run tests with pytest:

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details
