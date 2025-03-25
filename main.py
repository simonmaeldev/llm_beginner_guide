import os
import subprocess
import yaml
from pathlib import Path

from aider.coders import Coder
from aider.models import Model
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def send_query(prompt: str) -> str:
    try:
        # Load API key from environment
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "Error: DEEPSEEK_API_KEY environment variable not set"

        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com"),
        )

        console.print(Panel("LLM Response:", style="bold green"))
        full_response = ""

        # Make the streaming request
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )

        # Process the stream
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                # Print to console
                console.print(content, end="", style="dim", highlight=False)
                # Append to full response
                full_response += content

        console.print("\n")
        return full_response

    except Exception as e:
        console.print(f"[red]Error occurred: {e!s}[/red]")
        return f"Error occurred: {e!s}"




def get_remote_files_content(diff_output: str) -> dict[str, str | None]:
    """Get the content of all files in the diff from remote"""
    file_contents = {}

    # Extract changed files from diff
    changed_files = set()
    for line in diff_output.splitlines():
        if line.startswith("diff --git"):
            # Extract filename after b/
            file_path = line.split(" b/")[1]
            changed_files.add(file_path)

    # Get content of each file from remote
    for file_path in changed_files:
        try:
            content = subprocess.check_output(
                ["git", "show", f"origin/HEAD:{file_path}"], stderr=subprocess.STDOUT,
            ).decode()
            file_contents[file_path] = content
        except subprocess.CalledProcessError:
            # File might be new, so no remote content
            file_contents[file_path] = None

    return file_contents


def get_git_diff():
    try:
        # Get current branch name
        branch_name = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.STDOUT,
            )
            .decode()
            .strip()
        )

        # Check if remote exists
        try:
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError:
            return "Error: No remote 'origin' configured. Please set up a remote repository."

        # Fetch updates from remote
        fetch_result = subprocess.run(
            ["git", "fetch", "origin"], capture_output=True, text=True, check=False,
        )

        if fetch_result.returncode != 0:
            return f"Error fetching from remote: {fetch_result.stderr}"

        # Get diff between local and remote
        diff_output = subprocess.check_output(
            ["git", "diff", f"origin/{branch_name}..HEAD"], stderr=subprocess.STDOUT,
        ).decode()

        return diff_output if diff_output else "No differences found"

    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed: {e.cmd}\n"
        error_msg += f"Return code: {e.returncode}\n"
        error_msg += f"Error output: {e.stderr if e.stderr else e.stdout}"
        return error_msg


def apply_suggestions(suggestions: str, files_to_edit: list):
    try:
        model = Model("deepseek/deepseek-chat")
        coder = Coder.create(main_model=model, fnames=files_to_edit, auto_commits=False)

        # Validate and apply suggestions
        console.print(Panel("LLM Suggestions:", style="bold yellow"))
        console.print(Syntax(suggestions, "python", theme="monokai"))
        if input("Apply these suggestions? (y/n): ").lower() == "n":
            result = "Suggestions not applied - user declined"
        else:
            result = coder.run(get_prompt_value("system.message") + suggestions)

        # Show status instead of committing
        console.print(
            Panel("Changes applied. Here's the git status:", style="bold green"),
        )
        status = subprocess.check_output(
            ["git", "status"], stderr=subprocess.STDOUT,
        ).decode()
        console.print(Syntax(status, "bash", theme="monokai"))

        return result

    except subprocess.CalledProcessError as e:
        return f"Git error occurred: {e!s}"
    except Exception as e:
        return f"Error applying suggestions: {e!s}"


def get_changes() -> tuple[str, dict[str, str | None]]:
    """Get git diff and remote files content"""
    console.print(Panel("Getting git diff...", style="bold blue"))
    git_diff = get_git_diff()

    if git_diff.startswith("Error"):
        return git_diff, {}

    console.print(Panel("Getting remote files content...", style="bold blue"))
    files_before = get_remote_files_content(git_diff)
    return git_diff, files_before


def prepare_prompt(git_diff: str, files_before: dict[str, str | None]) -> str:
    """Prepare the LLM prompt with diff and file contents"""
    files_before_str = "\n\n".join(
        f"File: {path}\n{content if content else 'New file'}"
        for path, content in files_before.items()
    )

    console.print(Panel("Git diff:", style="bold green"))
    console.print(Syntax(git_diff, "diff", theme="monokai", line_numbers=True))
    console.print(Panel.fit("", style="dim"))

    try:
        prompts = load_yaml_config()
        prompt_template = prompts["prompts"]["templates"]["code_review"]
    except FileNotFoundError:
        console.print("[red]Error: prompt.yaml file not found[/red]")
        exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing YAML: {e}[/red]")
        exit(1)
    except KeyError:
        console.print("[red]Error: 'prompt_template' key not found in prompt.yaml[/red]")
        exit(1)

    return prompt_template.format(git_diff=git_diff, files_before=files_before_str)


def apply_changes(response: str, git_diff: str) -> None:
    """Apply the LLM suggestions to files"""
    files_to_edit = list(get_remote_files_content(git_diff).keys())
    branch_name = (
        subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.STDOUT,
        )
        .decode()
        .strip()
    )

    apply_result = apply_suggestions(response, files_to_edit)
    console.print(Panel("Application result:", style="bold green"))
    console.print(apply_result)


def main():
    """Main execution flow"""
    git_diff, files_before = get_changes()
    if git_diff.startswith("Error"):
        console.print(f"[red]{git_diff}[/red]")
        exit(1)

    prompt = prepare_prompt(git_diff, files_before)
    console.print(Panel("Sending request to LLM...", style="bold yellow"))
    response = send_query(prompt)
    apply_changes(response, git_diff)


def load_yaml_config() -> dict:
    """Shared YAML loading function with consistent error handling."""
    try:
        import yaml
        with open("prompt.yaml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        console.print("[red]Error: prompt.yaml file not found[/red]")
        exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing YAML: {e}[/red]")
        exit(1)

def get_prompt_value(key: str) -> str:
    """Helper to get values from prompt.yaml with proper error handling."""
    try:
        prompts = load_yaml_config()
        # Access nested structure: prompts -> prompts -> category -> key
        return prompts["prompts"][key.split('.')[0]][key.split('.')[1] if '.' in key else "message"]
    except KeyError:
        console.print(f"[red]Error: '{key}' key not found in prompt.yaml[/red]")
        exit(1)


if __name__ == "__main__":
    main()
