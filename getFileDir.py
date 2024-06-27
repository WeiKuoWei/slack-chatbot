import os
import json
import fire
from queue import Queue

def findFileBFS(
        root: str = "./data/articles", 
        file_type: str = ".json"
    ):
    
    print(f"Searching for {file_type} files in {root}")

    files = {}
    q = Queue()
    q.put(root)

    while not q.empty():
        current_dir = q.get()

        # scan the files in the current directory with os.scandir
        with os.scandir(current_dir) as entries:
            if entries is None:
                continue
            for entry in entries:
                if entry.is_file() and entry.name.endswith(file_type):
                    files[entry.name] = entry.path
                    # print(entry.path)
                
                elif entry.is_dir():
                    q.put(entry.path)
    
    with open('files.json', 'w') as f:
        json.dump(files, f, indent=4)

    return files

if __name__ == "__main__":
    fire.Fire(findFileBFS)

    