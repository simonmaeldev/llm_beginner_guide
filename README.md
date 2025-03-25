# Code Review Assistant

A command-line tool that uses DeepSeek's LLM to analyze git diffs and suggest code improvements.

## Key Features:
- Compares local changes against remote branch (origin/HEAD)
- Shows complete file context from remote branch
- Applies suggestions interactively
- Streams LLM responses in real-time
- Manages changes through git integration

## Requirements:
- Python 3.12+
- Git installed
- DEEPSEEK_API_KEY environment variable set (recommended: use dotenv or your shell's secure environment storage)

## Dependencies:
Managed using [uv](https://github.com/astral-sh/uv) (version 1.0.0+ recommended):
- aider-chat>=0.78.0  
- openai>=1.66.3
- pyyaml>=6.0.2  
- rich>=13.9.4

Install dependencies with:
```bash
uv pip install -e .
```

## Usage:
1. Make code changes locally
2. Run `python main.py`
3. Review the LLM's code improvement suggestions
4. Selectively apply suggestions through the interactive interface

The tool will:
- Fetch latest changes from remote
- Show the git diff
- Get remote file contents for context
- Send analysis to DeepSeek's API
- Let you apply suggested changes
