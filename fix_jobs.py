import os
import re

def fix_jobs():
    for root, _, files in os.walk('apps'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                
                if 'Job(' in content and 'type=' in content:
                    # Just print for now to inspect
                    print(f"File: {path}")
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'job = Job(' in line or 'Job(' in line:
                            print(f"{i}: {line}")

if __name__ == "__main__":
    fix_jobs()
