import json
import glob
import re

# 1. Parse python openapi.json
with open('apps/api/openapi.json', 'r') as f:
    openapi = json.load(f)

python_endpoints = set()
for path, methods in openapi['paths'].items():
    # Convert path params {param} to generic {}
    norm_path = re.sub(r'\{[^}]+\}', '{}', path)
    if not norm_path.startswith('/api/v1'):
        continue
    for method in methods.keys():
        python_endpoints.add(f"{method.upper()} {norm_path}")

# 2. Parse Java controllers
java_endpoints = set()
controllers = glob.glob('apps/api-java/src/main/java/com/mesalaw/controller/*.java')

for controller in controllers:
    with open(controller, 'r') as f:
        content = f.read()
    
    # Base mapping
    base_path_match = re.search(r'@RequestMapping\("([^"]+)"\)', content)
    base_path = base_path_match.group(1) if base_path_match else ""
    
    # Method mappings
    methods = re.findall(r'@(Get|Post|Put|Delete|Patch)Mapping\((?:value\s*=\s*)?((?:\{[^}]+\})|(?:"[^"]+"))?[^)]*\)', content)
    for m in methods:
        method = m[0].upper()
        # Parse path
        path_part = ""
        if m[1]:
            if m[1].startswith('{'):
                paths = [p.strip().strip('"') for p in m[1][1:-1].split(',')]
                path_part = paths[0]
            else:
                path_part = m[1].strip('"')
        
        full_path = (base_path + path_part).replace('//', '/')
        # Convert {param} to {}
        norm_path = re.sub(r'\{[^}]+\}', '{}', full_path)
        java_endpoints.add(f"{method} {norm_path}")
        
    # Also find simple @(Get|Post...)Mapping without args
    methods_simple = re.findall(r'@(Get|Post|Put|Delete|Patch)Mapping(\s*\n|\s*\()', content)
    # the previous regex is a bit complex, let's do something simpler:
    
