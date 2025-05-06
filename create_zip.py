import os
import zipfile
import fnmatch
import datetime

def should_exclude(file_path, exclude_patterns):
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_path, pattern) or any(fnmatch.fnmatch(part, pattern) for part in file_path.split(os.sep)):
            return True
    return False

def read_gitignore():
    exclude_patterns = []
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Convert .gitignore pattern to fnmatch pattern
                    if line.startswith('/'):
                        line = line[1:]
                    elif not line.startswith('*') and '/' not in line:
                        line = '*' + line if not line.startswith('*') else line
                    exclude_patterns.append(line)
    
    # Always exclude these
    exclude_patterns.extend([
        '*__pycache__*',
        '*.pyc',
        '*node_modules*',
        '*build*',
        '*.env',
        '*.git*',
        '*test.db*',
        '*.cursorrules',
        'create_zip.py'  # Exclude this script itself
    ])
    
    return exclude_patterns

def create_zip():
    # Create a timestamp for the zip filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"culinaryAI_{timestamp}.zip"
    
    exclude_patterns = read_gitignore()
    
    print(f"Creating zip file: {zip_filename}")
    print(f"Excluding patterns: {exclude_patterns}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Skip certain directories using the patterns
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not should_exclude(file_path, exclude_patterns):
                    arcname = file_path[2:]  # Remove './'
                    print(f"Adding: {arcname}")
                    zipf.write(file_path, arcname)
    
    print(f"\nZip file created: {zip_filename}")
    print(f"Size: {os.path.getsize(zip_filename) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    create_zip() 