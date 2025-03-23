import os
import subprocess
from pathlib import Path
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

console = Console()

def send_query(prompt: str) -> str:
    try:
        # Load API key from environment
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            return "Error: DEEPSEEK_API_KEY environment variable not set"
            
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=True
        )
        
        # Stream the response with Rich
        console.print(Panel("LLM Response:", style="bold green"))
        full_response = ""
        with console.status("[bold green]Receiving response...[/bold green]"):
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    console.print(content, end="", style="dim", highlight=False)
                    full_response += content
                    
        console.print("\n")
        return full_response
        
    except Exception as e:
        console.print(f"[red]Error occurred: {str(e)}[/red]")
        return f"Error occurred: {str(e)}"

def get_git_diff():
    try:
        # Get current branch name
        branch_name = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.STDOUT
        ).decode().strip()
        
        # Check if remote exists
        try:
            subprocess.check_output(
                ['git', 'config', '--get', 'remote.origin.url'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError:
            return "Error: No remote 'origin' configured. Please set up a remote repository."
        
        # Fetch updates from remote
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin'],
            capture_output=True,
            text=True
        )
        
        if fetch_result.returncode != 0:
            return f"Error fetching from remote: {fetch_result.stderr}"
        
        # Get diff between local and remote
        diff_output = subprocess.check_output(
            ['git', 'diff', f'HEAD..origin/{branch_name}'],
            stderr=subprocess.STDOUT
        ).decode()
        
        return diff_output if diff_output else "No differences found"
    
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e.stderr if e.stderr else e.stdout}"

if __name__ == "__main__":
    # Get git diff
    console.print(Panel("Getting git diff...", style="bold blue"))
    
    git_diff = get_git_diff()
    
    # Show the diff
    console.print(Panel("Git diff:", style="bold green"))
    console.print(Syntax(git_diff, "diff", theme="monokai", line_numbers=True))
    console.print(Panel.fit("", style="dim"))
    
    # Load prompt template
    try:
        prompt_template = Path("prompt.txt").read_text()
    except Exception as e:
        console.print(f"[red]Error loading prompt template: {e}[/red]")
        exit(1)
    
    # Format prompt with git diff
    if git_diff.startswith("Error"):
        console.print(f"[red]{git_diff}[/red]")
        exit(1)
        
    prompt = prompt_template.format(git_diff=git_diff)
    
    # Send query to LLM
    console.print(Panel("Sending request to LLM...", style="bold yellow"))
    response = send_query(prompt)
