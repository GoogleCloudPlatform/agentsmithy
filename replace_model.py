import os
import re

directories_to_check = ['agent_bar_v2', '.']

count = 0
for root, dirs, files in os.walk('.'):
    if any(ignore in root for ignore in ['.venv', 'venv', '.git', '__pycache__', 'node_modules']):
        continue
        
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            if 'os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview")' in content or "os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview")" in content:
                # Replace the string literal with the os.getenv call
                new_content = re.sub(r'[\'"]gemini-2.5-flash[\'"]', 'os.getenv("GEMINI_MODEL_VERSION", "gemini-3-flash-preview")', content)
                
                # Check if 'import os' is in the file
                if not re.search(r'^import os$', new_content, re.MULTILINE):
                    new_content = 'import os\n' + new_content
                
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Updated {path}")
                count += 1

print(f"Total files updated: {count}")
