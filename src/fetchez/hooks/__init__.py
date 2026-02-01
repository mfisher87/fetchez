class FetchHook:
    """Base class for all Fetchez Hooks."""
    
    # Unique identifier for CLI (e.g., --hook unzip)
    name = "base_hook"
    
    # Description for --list-hooks
    desc = "Does nothing."

    # Defaults to 'per_file', but could be 'pre_fetch' or 'post_fetch'
    # Stages:
    #   1. 'pre':  Runs once before any downloads start.
    #   2. 'file': Runs in the worker thread immediately after a file download.
    #   3. 'post': Runs once after all downloads are finished.
    stage = 'file' 

    def __init__(self, **kwargs):
        self.opts = kwargs

    def run(self, entry):
        """Execute the hook.
        
        Args:
            entry: For 'file' stage: [url, path, type, status]
                   For 'pre'/'post': The full list of results (so far) or context.
        
        Returns:
            Modified entry (for 'file' stage pipeline) or None.
        """
        
        return entry
