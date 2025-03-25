# Code Review Assistant

A command-line tool that uses DeepSeek's LLM to analyze git diffs and suggest code improvements.

## Key Features:
- Compares local changes against remote branch (origin/HEAD)
- Shows complete file context from remote
- Interactive suggestion application
- Streaming LLM responses
- Git integration for change management

## Requirements:
- Python 3.12+
- Git installed
- DEEPSEEK_API_KEY environment variable set

## Dependencies:
Managed using [uv](https://github.com/astral-sh/uv):
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
3. Review the LLM's suggestions
4. Choose whether to apply them

The tool will:
- Fetch latest changes from remote
- Show the git diff
- Get remote file contents for context
- Send analysis to DeepSeek's API
- Let you apply suggested changes
