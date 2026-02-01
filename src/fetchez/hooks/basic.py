import sys
import os
import threading
from . import FetchHook

PRINT_LOCK = threading.Lock()

class PipeOutput(FetchHook):
    name = "pipe"
    desc = "Print absolute file paths to stdout for piping."
    stage = 'post'

    def run(self, entries):
        """Input is: [url, path, type, status]"""

        for entry in entries:
            if entry.get('status') == 0:
                with PRINT_LOCK:
                    print(os.path.abspath(entry.get('dst_fn')), file=sys.stdout, flush=True)
        return entries
