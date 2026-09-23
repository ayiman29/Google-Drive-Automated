import os
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import pickle
import json
import fnmatch
from authenticate import authenticate
import json

IGNORED_FOLDERS = {"$Temp", "__MACOSX", ".git"}
IGNORED_FILES = {".DS_Store", "Thumbs.db", "README.md", "readme.md", "LICENSE", "license.txt"}
IGNORED_FILES = {
    ".DS_Store", "Thumbs.db", "README.md", "readme.md", "LICENSE", "license.txt",
    ".folderignore", "folderignore"
}


DEFAULT_FOLDERIGNORE_TEMPLATE = """# Folder Ignore List
# Add folder names or patterns to ignore during Google Drive synchronization.
# One entry per line. Blank lines and lines starting with '#' are ignored.

# Exact folder names
node_modules
venv
.venv
__pycache__
build
dist
$Temp
__MACOSX

# Wildcard patterns
temp_*
*.tmp
*cache*
"""


def create_default_folderignore(target_path=".folderignore"):
    """Create a default .folderignore file if one does not exist."""
    sample_path = ".folderignore.sample"
    try:
        if os.path.isfile(sample_path):
            with open(sample_path, "r", encoding="utf-8") as src:
                content = src.read()
        else:
            content = DEFAULT_FOLDERIGNORE_TEMPLATE
        with open(target_path, "w", encoding="utf-8") as dst:
            dst.write(content)
        print(f"Created default folder ignore file: {target_path}")
    except Exception as e:
        print(f"Warning: could not create default {target_path}: {e}")


def load_ignored_folders(local_folder=None, auto_create=True):
    """
    Load ignored folder names and patterns from .folderignore or folderignore files.
    Checks both the current working directory and local_folder (if provided).
    If no ignore file exists and auto_create is True, creates a default .folderignore.
    Returns a set of patterns including default IGNORED_FOLDERS.
    """
    ignored = set(IGNORED_FOLDERS)

    candidate_paths = [".folderignore", "folderignore"]
    if local_folder and os.path.isdir(local_folder):
        candidate_paths.append(os.path.join(local_folder, ".folderignore"))
        candidate_paths.append(os.path.join(local_folder, "folderignore"))

    # If no ignore file exists, create a default one
    has_existing = any(os.path.isfile(p) for p in candidate_paths)
    if not has_existing and auto_create:
        create_default_folderignore(".folderignore")

    seen_files = set()
    for file_path in candidate_paths:
        abs_path = os.path.abspath(file_path)
        if abs_path in seen_files:
            continue
        seen_files.add(abs_path)

        if os.path.isfile(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        line = line.rstrip("/\\")
                        if line:
                            ignored.add(line)
            except Exception as e:
                print(f"Warning: could not read ignore file {abs_path}: {e}")

    return ignored


def is_folder_ignored(folder_name, relative_folder_path="", ignored_patterns=None):
    """Check if a folder name or relative path matches any pattern in ignored_patterns."""
    if ignored_patterns is None:
        ignored_patterns = IGNORED_FOLDERS

    norm_rel = relative_folder_path.replace("\\", "/").strip("/") if relative_folder_path else ""
    parts = norm_rel.split("/") if norm_rel and norm_rel != "." else []

    for pattern in ignored_patterns:
        norm_pattern = pattern.replace("\\", "/").strip("/")

        # Direct name match or glob pattern match
        if folder_name == norm_pattern or fnmatch.fnmatch(folder_name, norm_pattern):
            return True

        # Full relative path match
        if norm_rel and (norm_rel == norm_pattern or fnmatch.fnmatch(norm_rel, norm_pattern)):
            return True

        # Any path component match
        for part in parts:
            if part == norm_pattern or fnmatch.fnmatch(part, norm_pattern):
                return True

    return False

def create_folder(service, folder_name, parent_folder_id, uploaded_folders):
    """Create a folder on Google Drive and return the folder ID."""
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id] if parent_folder_id else []
    }

    folder = service.files().create(body=folder_metadata, fields='id').execute()
    folder_id = folder['id']

    uploaded_folders["folders"][folder_name] = folder_id
    save_uploaded_folders(uploaded_folders)

    print(f"Folder created: {folder_name} - {folder_id}")
    return folder_id


def create_folder_recursive(service, folder_path, parent_folder_id, uploaded_folders):
    parts = folder_path.split(os.sep)  
    current_parent = parent_folder_id  

    for i in range(len(parts)):
        subpath = os.sep.join(parts[: i + 1])  

        if subpath in uploaded_folders["folders"]:  
            current_parent = uploaded_folders["folders"][subpath]
        else:
            current_parent = create_folder(service, parts[i], current_parent, uploaded_folders)
            uploaded_folders["folders"][subpath] = current_parent  # Store full path

    return current_parent


def upload_file(service, file_path, parent_folder_id=None, uploaded_folders=None):
    file_name = os.path.basename(file_path)


    if file_name in IGNORED_FILES or file_name.startswith('.'):
        print(f"Skipping hidden/system file: {file_name}")
        return


    if file_name in uploaded_folders["files"].get(parent_folder_id, {}):
        existing_file_id = uploaded_folders["files"][parent_folder_id][file_name]["id"]
        stored_last_modified = uploaded_folders["files"][parent_folder_id][file_name]["last_modified"]
        local_last_modified = os.path.getmtime(file_path)


        if stored_last_modified >= local_last_modified:
            print(f"Skipping {file_name}, no changes detected.")
            return  


        try:
            print(f"Deleting existing file {file_name}...")
            service.files().delete(fileId=existing_file_id).execute()
            print(f"Deleted file {file_name} from Google Drive.")
        except Exception as e:
            print(f"Error deleting file {file_name}: {e}")

    media = MediaFileUpload(file_path, resumable=True)
    file_metadata = {
        'name': file_name,
        'parents': [parent_folder_id] if parent_folder_id else []
    }

    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        print(f"File uploaded: {file['id']} - {file['name']}")

        if parent_folder_id not in uploaded_folders["files"]:
            uploaded_folders["files"][parent_folder_id] = {}

        uploaded_folders["files"][parent_folder_id][file_name] = {
            "id": file["id"],
            "last_modified": os.path.getmtime(file_path)
        }

        save_uploaded_folders(uploaded_folders)

    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")


def load_uploaded_folders():
    try:
        with open("uploaded_folders.json", "r") as f:
            data = json.load(f)
            if "folders" not in data:
                data["folders"] = {}
            if "files" not in data:
                data["files"] = {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"folders": {}, "files": {}}


def save_uploaded_folders(data):
    with open("uploaded_folders.json", "w") as f:
        json.dump(data, f, indent=4)



def check_and_upload_files(local_folder, drive_service, parent_folder_id=None):
    uploaded_folders = load_uploaded_folders()
    ignored_folders = load_ignored_folders(local_folder)

    for root, dirs, files in os.walk(local_folder):
        relative_folder_path = os.path.relpath(root, local_folder)

        if relative_folder_path != '.' and is_folder_ignored(os.path.basename(root), relative_folder_path, ignored_folders):
            print(f"Skipping ignored folder: {root}")
            dirs[:] = []
            continue

        kept_dirs = []
        for d in dirs:
            dir_rel_path = os.path.relpath(os.path.join(root, d), local_folder)
            if is_folder_ignored(d, dir_rel_path, ignored_folders):
                print(f"Skipping ignored folder: {os.path.join(root, d)}")
            else:
                kept_dirs.append(d)
        dirs[:] = kept_dirs

        folder_id = parent_folder_id
        if relative_folder_path != '.':
            folder_id = create_folder_recursive(drive_service, relative_folder_path, parent_folder_id, uploaded_folders)

        for file_name in files:
            file_path = os.path.join(root, file_name)

            if file_name in IGNORED_FILES or file_name.startswith('.'):
                print(f"Skipping hidden/system file: {file_name}")
                continue

            upload_file(drive_service, file_path, folder_id, uploaded_folders)


if __name__ == '__main__':
    drive_service = authenticate()

    with open("config.json", "r") as f:
        config = json.load(f)

    root_folder_id = config["root_folder_id"]
    local_folder = config["local_folder"]

    check_and_upload_files(local_folder, drive_service, parent_folder_id=root_folder_id)
