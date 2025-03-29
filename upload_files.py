import os
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import pickle
from authenticate import authenticate
import json

IGNORED_FOLDERS = {"$Temp", "__MACOSX", ".git"}
IGNORED_FILES = {".DS_Store", "Thumbs.db"}

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

    for root, dirs, files in os.walk(local_folder):
        if any(ignored in root for ignored in IGNORED_FOLDERS):
            print(f"Skipping ignored folder: {root}")
            continue

        relative_folder_path = os.path.relpath(root, local_folder)

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
