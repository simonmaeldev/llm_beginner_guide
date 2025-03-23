import subprocess

def get_git_diff():
    try:
        # Get current branch name
        branch_name = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.STDOUT
        ).decode().strip()
        
        # Fetch updates from remote
        subprocess.run(['git', 'fetch', 'origin'], check=True)
        
        # Get diff between local and remote
        diff_output = subprocess.check_output(
            ['git', 'diff', f'HEAD..origin/{branch_name}'],
            stderr=subprocess.STDOUT
        ).decode()
        
        return diff_output
    
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e.output.decode()}"

diff = get_git_diff()
print(diff)
