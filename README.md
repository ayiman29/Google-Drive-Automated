# Google Drive File Sync Script

This project provides a Python-based solution for synchronizing local files and folders with Google Drive. It allows you to upload files from a local directory to Google Drive, ensuring that only missing or modified files are uploaded. The folder structure on Google Drive is mirrored from the local directory, creating folders and subfolders as necessary.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Setup Instructions](#setup-instructions)
  - [Google Cloud Console Setup](#google-cloud-console-setup)
  - [Installing Dependencies](#installing-dependencies)
  - [Configuration](#configuration)
- [How to Use](#how-to-use)
- [Code Overview](#code-overview)
- [Security Considerations](#security-considerations)
- [Acknowledgements](#acknowledgements)

## Introduction

This script allows seamless file synchronization between your local machine and Google Drive using Google Drive API. It checks if files already exist in Google Drive and only uploads those that are new or modified. The folder structure from the local directory is preserved in Google Drive. The script also uses OAuth 2.0 authentication for secure access to your Google Drive.

This code was built with the help of ChatGPT, who assisted in guiding through the necessary steps and code structure.

## Features
- Synchronizes a local folder to a Google Drive folder.
- Creates folders recursively on Google Drive to match local structure.
- Uploads only new or modified files, skipping unchanged files.
- Ignores system files and folders (e.g., `.DS_Store`, `.git`).
- OAuth 2.0 authentication for secure access to Google Drive.
- Stores upload state (folders and files) in a JSON file for efficiency.
- Ensures only relevant files are uploaded by comparing modification times.

## Requirements

Before running this script, ensure you have the following:

- Python 3.x
- Google Cloud project with Google Drive API enabled
- OAuth 2.0 credentials (`credentials.json`)

Additionally, the following Python packages are required:

- `google-api-python-client`
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `oauthlib`
- `requests`
- `pandas` (optional, for data manipulation)
- `openpyxl` (optional, for handling Excel files)
- `pillow` (optional, for working with images)
- `pytest` (for unit testing)
- `rich` (for enhanced console output)

## Setup Instructions

### Google Cloud Console Setup

To get started with the Google Drive API, you'll need to create a project in the Google Cloud Console and obtain OAuth 2.0 credentials.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Google Drive API**:
   - Navigate to **APIs & Services > Library**.
   - Search for **Google Drive API** and enable it for your project.
4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services > Credentials**.
   - Click **Create Credentials > OAuth 2.0 Client IDs**.
   - Set **Application Type** to **Desktop App** and give it a name.
   - Download the `credentials.json` file, which contains your client ID and client secret. This file is needed to authenticate the application.

### Installing Dependencies

Install the necessary dependencies using `pip`:

```bash
pip install -r requirements.txt
```

This will install all the required libraries listed in the `requirements.txt` file.

### Configuration

Before running the script, you must configure your local folder and Google Drive folder details.

1. **Create a `config.json` file**: This file stores the local directory and the root folder ID of your Google Drive where files will be uploaded. Example configuration:
   
   ```json
   {
     "local_folder": "path-to-your-local-folder",
     "root_folder_id": "your-google-drive-root-folder-id"
   }
   ```

   You can find your Google Drive root folder ID from the Google Drive API or the folder’s URL.

2. **Add OAuth credentials**: Place the `credentials.json` you downloaded from the Google Cloud Console in the project directory.

3. **Create `uploaded_folders.json`**: This file will be generated automatically to keep track of uploaded folders and files, ensuring that only new or modified files are uploaded.

## How to Use

### Running the Script

1. **Authenticate with Google Drive**:
   The first time you run the script, it will open a web browser asking for Google account authorization to access Google Drive.

   ```bash
   python upload_files.py
   ```

2. **File Upload**:
   Once authenticated, the script will scan your local folder (specified in `config.json`), create corresponding folders on Google Drive, and upload any missing or modified files.

3. **Folder Structure**:
   The folder structure of your local directory will be mirrored on Google Drive, ensuring that the same folder hierarchy is maintained.

### Optional: Testing

To ensure everything is working correctly, you can run unit tests with `pytest`:

```bash
pytest
```

This will test key functions in the script, ensuring that files are uploaded correctly and no errors occur.

## Code Overview

### `authenticate.py`
Handles OAuth 2.0 authentication for accessing Google Drive. It saves user credentials to `token.pickle` for future use, ensuring the user doesn’t have to authenticate every time.

### `upload_files.py`
This is the main script that performs the file synchronization:
- It walks through the local directory, creates folders on Google Drive, and uploads files that are new or modified.
- The script uses the `MediaFileUpload` method from Google API to upload files efficiently.

### `config.json`
Contains configuration settings such as the path to the local folder to be synced and the root folder ID on Google Drive where the files will be uploaded.

### `credentials.json`
This file contains OAuth 2.0 credentials for the application, including client ID and client secret. **Do not share or upload this file to public repositories.**

### `uploaded_folders.json`
This file is used to track uploaded folders and files. It ensures that the script doesn’t upload the same file multiple times, and it helps to check if a file has been modified locally.

## Security Considerations

1. **OAuth Credentials**: Keep your `credentials.json` and `token.pickle` files secure. These contain sensitive authentication data. Ensure that these files are excluded from public repositories using `.gitignore`.
   
2. **Sensitive Data**: While the local folder path and Google Drive folder ID aren’t as critical as OAuth credentials, you should still avoid sharing them publicly or committing them to version control.

3. **Environment Variables**: For production environments, consider storing sensitive information (such as OAuth secrets and tokens) in environment variables, using tools like `dotenv`.

4. **File Permissions**: Be cautious when handling files, especially when downloading or uploading files with sensitive content. Always verify that the uploaded files are being sent to the correct Google Drive folders.

## Acknowledgements

This project was built with the assistance of **ChatGPT**, which helped in the design, structure, and implementation of key parts of the code. ChatGPT provided guidance on setting up OAuth 2.0 authentication, organizing the file structure, and addressing common issues in file syncing with Google Drive.

