import subprocess

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

diff = get_git_diff()
print(diff)
