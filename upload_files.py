import os
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import pickle
from authenticate import authenticate
import json

# Function to create a folder on Google Drive
def create_folder(service, folder_name, parent_folder_id=None):
    # Create a folder metadata object
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id] if parent_folder_id else []
    }
    
    # Create the folder
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

# Function to upload a file to Google Drive, in the correct folder
def upload_file(service, file_path, parent_folder_id=None):
    media = MediaFileUpload(file_path, resumable=True)
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [parent_folder_id] if parent_folder_id else []
    }
    
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        print(f"File uploaded: {file['id']} - {file['name']}")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")

# Function to check local files and create corresponding folders on Google Drive
def check_and_upload_files(local_folder, drive_service, parent_folder_id=None):
    for root, dirs, files in os.walk(local_folder):
        # Skip any directories that contain '.git'
        if '.git' in root:
            continue
        
        # Determine the relative path of the folder (so we can recreate the structure)
        relative_folder_path = os.path.relpath(root, local_folder)
        
        # Check if the folder already exists on Google Drive, if not create it
        folder_id = parent_folder_id
        if relative_folder_path != '.':
            folder_id = create_folder(drive_service, relative_folder_path, parent_folder_id)
        
        # Upload files in this folder
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            # Skip unwanted sample files
            if file_name.lower().endswith('.sample'):
                print(f"Skipping file: {file_name} (unwanted sample file)")
                continue
            
            print(f"Uploading file: {file_path}")
            upload_file(drive_service, file_path, folder_id)

if __name__ == '__main__':
    # Authenticate with Google Drive
    drive_service = authenticate()


    # Load config.json
    with open("config.json", "r") as f:
        config = json.load(f)

    # The parent folder ID where all the files will be uploaded
    # If you want to upload everything into a folder like 'BRAC STUDY MATERIALS' in your Drive, you should specify that folder ID
    root_folder_id = config["root_folder_id"]  # Replace with your folder ID

    # Path to the local folder you want to scan and upload from
    local_folder = config["local_folder"]  # Change this to your folder path

    # Check and upload files
    check_and_upload_files(local_folder, drive_service, parent_folder_id=root_folder_id)
