# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import google.auth
import os.path
import json
import io
import shutil
from absl import logging
from typing import Any, Dict, List, Optional
from googleapiclient.http import MediaIoBaseUpload
from google.adk.tools import ToolContext, FunctionTool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from master.config import (
    PROJECT_ID,
    TOKEN_PATH,
    WRITABLE_PATH,
    CREDENTIALS_FILE_NAME,
    REPOSITORY_FOLDER_ID,
    DEFAULT_FOLDER_ID)



# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive', 
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive.metadata',
          'https://www.googleapis.com/auth/documents',
          'https://www.googleapis.com/auth/presentations']

DEFAULT_TEMPLATE_ID = "PLACEHOLDER"


def authenticate_google_apis_default():
    """
    Authenticates a web service to Google APIs using Application Default Credentials (ADC).
    This method automatically finds credentials in environments like Google Cloud Platform.
    """
    creds = None
    try:

        # google.auth.default() automatically finds credentials based on the environment.
        # On GCP, this will typically be the attached service account.
        # Outside GCP, it might look for the GOOGLE_APPLICATION_CREDENTIALS environment variable
        # or a local credentials file set up by 'gcloud auth application-default login'.
        creds, project = google.auth.default(scopes=SCOPES)
        print("Application Default Credentials authentication successful.")
        return creds
    except Exception as e:
        print(f"Error during Application Default Credentials authentication: {e}")
        return None

def authenticate_google_apis():
    """Shows basic usage of the Drive and Docs APIs.
    Prints the names and IDs of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH) and not os.path.exists(WRITABLE_PATH):
        shutil.copy(TOKEN_PATH, WRITABLE_PATH)
        creds = Credentials.from_authorized_user_file(WRITABLE_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE_NAME, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

# ... (after authenticate_google_apis) ...

def _get_folder_id(drive_service, parent_id, folder_name):
    """Searches for a folder by name within a specific parent ID."""
    # Note: Using supportsAllDrives and includeItemsFromAllDrives flags
    # handles both regular and Shared Drive searches.
    
    query = (
        f"name='{folder_name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'{parent_id}' in parents and "
        "trashed=false"
    )

    try:
        results = drive_service.files().list(
            q=query,
            fields='files(id)', 
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora='allDrives' # Important for searching across Shared Drives
        ).execute()
        
        items = results.get('files', [])
        
        return items[0]['id'] if items else None
    
    except HttpError as error:
        print(f"Error resolving folder ID for '{folder_name}' in parent '{parent_id}': {error}")
        return None


def _resolve_folder_path_to_id(drive_service, full_path: str, default_folder_id: str):
    """
    Resolves a full folder path (e.g., 'SharedDriveID/Folder A/Subfolder B')
    to the final destination folder ID.
    """
    path_parts = [p.strip() for p in full_path.split('/') if p.strip()]
    
    if not path_parts:
        return default_folder_id

    # The first component must be the Shared Drive ID (or a known root ID)
    current_parent_id = path_parts[0]
    
    # If the path is just a single ID, return it immediately
    if len(path_parts) == 1:
        # A simple check to see if the first part is likely a Drive ID (not exhaustive)
        if len(current_parent_id) > 10 and not current_parent_id.endswith('.txt'): # Basic check to avoid treating a folder name as an ID
            return current_parent_id
        # If it's a single folder name, we need a known root to search from
        # In a Shared Drive context, you often need the Shared Drive ID first.
        # This function assumes the user passes the Shared Drive ID as the first part.
        pass # Continue traversal

    # Traverse the path components starting from the second part
    # Assuming path_parts[0] is the Shared Drive ID, we start searching from path_parts[1:]
    
    # If the user provides a full path starting with a name, we must determine the root ID.
    # For simplicity, we assume the user provides the Shared Drive ID as the root.
    
    # If path_parts[0] is the Shared Drive ID, the folder names start at index 1
    # If the path starts with a folder name, you need a different starting ID (e.g., 'root')
    
    # Let's adjust: Assume the input is a mix of Shared Drive ID and folder path:
    # E.g., full_path = "0A_xxxxxxxxxx_DRIVEID/Folder A/Subfolder B"
    
    for folder_name in path_parts[1:]:
        if not current_parent_id:
            print(f"Traversal failed. Could not find parent for: {folder_name}")
            return None

        # Search for the next folder inside the current parent ID
        current_parent_id = _get_folder_id(drive_service, current_parent_id, folder_name)
        
    return current_parent_id
  
def list_drive_documents(
    tool_context: ToolContext,
    folder_id: str = DEFAULT_FOLDER_ID,
    include_deleted: bool = False):
    """
    Lists all files (documents) in a given folder, handling pagination for large results.
    
    Args:
        folder_id: The ID of the folder (or Shared Drive) to list.
        include_deleted: Whether to include deleted documents.
    """
    creds = authenticate_google_apis_default()
    
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Build the query to filter for files within the folder/drive
        # The 'driveId' parameter is sufficient for top-level Shared Drive listing,
        # but a 'q' parameter with the 'in parents' clause is more general for subfolders.
        # Since the input 'folder_id' could be a Shared Drive ID or a regular folder ID, 
        # using the 'in parents' query is more robust.
        
        # Default query: files that have the folder_id as a parent, not trashed.
        query = f"'{folder_id}' in parents and trashed = false"

        # If you specifically want to list ALL files in the Shared Drive (not just the top level),
        # you would omit the 'in parents' and just rely on the driveId parameter.
        # Given your use of 'driveId' in the original code, let's keep the query simple 
        # for folder contents, and rely on the Shared Drive parameters below.

        # --- PAGINATION LOGIC ---
        all_documents = []
        page_token = None
        
        while True:
            # The pageSize is now maxed out at 1000 for efficiency
            response = drive_service.files().list(
                pageSize=1000, # Increased for better performance
                q=query,       # Only show items directly in the folder
                pageToken=page_token, # Send the token for the next page
                
                # Shared Drive parameters:
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                corpora='allDrives', # Search across all Shared Drives/My Drive
                
                # Fields to return
                fields='nextPageToken, files(id, name, mimeType)'
            ).execute()
            
            # Append the files from the current page to the list
            all_documents.extend(response.get('files', []))
            
            # Get the token for the next page
            page_token = response.get('nextPageToken', None)
            
            # If no token is returned, we have reached the end of the results
            if page_token is None:
                break
        
        # --- END PAGINATION LOGIC ---
        
        return {
            "status": "success",
            "folder_id": folder_id,
            "message": f"Successfully listed {len(all_documents)} documents in folder '{folder_id}'",
            "documents": all_documents
        }
    except HttpError as error:
        # ... (error handling remains the same) ...
        return {
            "status": "error",
            "folder_id": folder_id,
            "error_message": str(error),
            "message": f"Failed to list documents in folder: {str(error)}"
        }
    except Exception as e:
        # ... (error handling remains the same) ...
        return {
            "status": "error",
            "folder_id": folder_id,
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def copy_and_replace_document(
    tool_context: ToolContext,
    original_document_id: str, 
    new_document_name: str,
    replacements: dict[str, str],
    destination_folder_path: str = None): # <-- NEW Parameter
    """
    Copies an existing Google Doc and replaces specified text while retaining formatting,
    optionally moving it to a new folder/path.

    Args:
        original_document_id: The ID of the Google Doc to copy.
        new_document_name: The name for the new copied document.
        replacements: A dictionary where keys are the text to find and values are the text to replace with.
        destination_folder_path: Optional. The path or ID of the folder to save the copy to. 
                                 e.g., 'SharedDriveID/Folder A/Subfolder B'.
    """
    creds = authenticate_google_apis_default()

    try:
        drive_service = build('drive', 'v3', credentials=creds)

        # 1. Resolve Destination Folder ID (if a path is provided)
        target_folder_id = None
        if destination_folder_path:
            target_folder_id = _resolve_folder_path_to_id(
                drive_service, 
                destination_folder_path, 
                DEFAULT_FOLDER_ID # Use default only if path resolution fails or is root
            )

        # ... (rest of existing code to determine mimeType and service) ...
        
        # 1. Copy the document
        copied_file_metadata = {
            'name': new_document_name,
            'mimeType': new_mime_type
        }
        
        # Add parents to metadata if a target folder was resolved
        if target_folder_id:
            copied_file_metadata['parents'] = [target_folder_id]
            
        copied_document = drive_service.files().copy(
            fileId=original_document_id,
            body=copied_file_metadata,
            supportsAllDrives=True # <-- REQUIRED FOR SHARED DRIVE COPY
        ).execute()

        new_document_id = copied_document.get('id')
        print(f"Document copied. New document ID: {new_document_id}")
        # 2. Prepare batch update requests for text replacement
        requests = []
        for old_text, new_text in replacements.items():
            requests.append({
                'replaceAllText': {
                    'replaceText': new_text,
                    'containsText': {
                        'text': old_text,
                        'matchCase': True # Set to False for case-insensitive replacement
                    }
                }
            })

        # Execute the batch update to replace text
        if requests:
            if mime_type == 'application/vnd.google-apps.document':
                service.documents().batchUpdate(
                    documentId=new_document_id,
                    body={'requests': requests}
                ).execute()
            elif mime_type == 'application/vnd.google-apps.presentation':
                service.presentations().batchUpdate(
                    presentationId=new_document_id,
                    body={'requests': requests}
                ).execute()
            print("Text replacement complete.")
        else:
            print("No replacements specified.")

        return {
            "status": "success",
            "message": f"Document '{new_document_name}' created and updated successfully.",
            "document_id": new_document_id
        }

    except HttpError as error:
        return {"status": "error", "message": f"An error occurred: {error}"}
    except Exception as e:
        return {"status": "error", "message": f"Error copying and replacing document: {str(e)}"}

def _delete_existing_slides(
    credentials: Any,
    presentation_id: str
) -> None:
  """This function deletes the existing slides in created presentation.

  Args:
    credentials: The credentials of the user.
    presentation_id: The presentation ID.

  Returns:
    None
  """
  try:

    # Build Service
    service = build("slides", "v1", credentials=credentials)

    response = (
        service.presentations().get(presentationId=presentation_id).execute()
    )

    if "slides" not in response:
      logging.info(
          "[_delete_existing_slides] - No slides found in the presentation"
      )
      return

    request_list = []
    for slide in response["slides"]:
      object_id = slide["objectId"]
      request_list.append({"deleteObject": {"objectId": object_id}})

    body = {"requests": request_list}

    _ = (
        service.presentations()
        .batchUpdate(presentationId=presentation_id, body=body)
        .execute()
    )
    logging.info("[_delete_existing_slides] - Deleted existing slide")
  except errors.HttpError as e:
    logging.exception(
        "[_delete_existing_slides] - Failed to delete existing slide: %s",
        presentation_id
    )
    raise e


def copy_theme_presentation(
    tool_context: ToolContext,
    title: str
) -> Dict[str, Any]:
  """This function copies the theme presentation to the user presentation.

  Args:
    tool_context: The tool context.
    title: The title of the presentation.

  Returns:
    Dictionary containing the status, message and result of
    the copied presentation.
  """
  credentials = authenticate_google_apis_default()

  try:
    body = {"name": title}

    drive_service = build("drive", "v3", credentials=credentials)

    if os.environ.get("DEFAULT_TEMPLATE_ID", None) is not None:
      theme_presentation_id = os.environ.get("DEFAULT_TEMPLATE_ID")
    else:
      theme_presentation_id = DEFAULT_TEMPLATE_ID

    logging.info(
        "[copy_theme_presentation] - Copying presentation: %s",
        theme_presentation_id
    )

    response = (
        drive_service.files()
        .copy(fileId=theme_presentation_id, body=body)
        .execute()
    )

    # Delete the existing slides of the copied presentation.
    _delete_existing_slides(credentials, response["id"])

    logging.info(
        "[copy_theme_presentation] - Copied presentation: %s", response
    )
    presentation_id = response["id"]

    return {
        "status": "success",
        "message": (
            "[copy_theme_presentation] - Copied presentation: "
            f"{presentation_id}"
        ),
        "result": {"presentation_id": presentation_id},
    }
  except errors.HttpError as e:
    logging.exception(
        "[copy_theme_presentation] - Failed to copy presentation: %s", e
    )
    return {
        "status": "error",
        "message": (
            f"[copy_theme_presentation] - Failed to copy presentation: {e}"
        ),
        "result": {"presentation_id": None},
    }


def detect_layouts_details(
    tool_context: ToolContext, presentation_id: str
) -> Dict[str, Any]:
  """Displays the presentation master and layout details.

  Args:
    tool_context: The tool context.
    presentation_id: The presentation ID.

  Returns:
    Dictionary of layout details.
  """
  credentials = authenticate_google_apis_default()

  try:
    # Build Service
    service = build("slides", "v1", credentials=credentials)

    # pylint: disable=g-too-many-blank-lines
    # This function is to display the presentation master and layout details.
    # This is for debugging purpose.
    response = (
        service.presentations().get(presentationId=presentation_id).execute()
    )

    # To reduce the size of the response, we are only keeping the required
    # fields.
    cleaned_response = {}
    cleaned_response["presentationId"] = response["presentationId"]
    cleaned_response["title"] = response["title"]

    # Parsing of layouts
    out_layouts = []
    for layouts in response["layouts"]:
      out_layout_dict = {}
      out_layout_dict["objectId"] = layouts["objectId"]
      out_layout_dict["layoutProperties"] = layouts["layoutProperties"]

      # Parsing of layouts.pageElements
      out_page_elements = []
      for page_element in layouts["pageElements"]:
        if "shape" in page_element:
          if "shapeType" in page_element["shape"]:
            if page_element["shape"]["shapeType"] == "TEXT_BOX":
              out_page_element_dict = {}
              out_page_element_dict["objectId"] = page_element["objectId"]
              out_page_element_dict["shape"] = page_element["shape"]
              out_page_element_dict["shape"].pop("text")
              out_page_element_dict["shape"].pop("shapeProperties")
              out_page_element_dict["size"] = page_element["size"]
              out_page_element_dict["transform"] = page_element["transform"]
              out_page_elements.append(out_page_element_dict)

      # Adding the pageElements to the layouts.
      if out_page_elements:
        out_layout_dict["pageElements"] = out_page_elements

      out_layouts.append(out_layout_dict)

    # Adding the layouts to the cleaned response.
    cleaned_response["layouts"] = out_layouts

    # json.dump(cleaned_response, open("/tmp/detect_layouts_details.json", "w"))

    logging.info(
        "[detect_layouts_details] - Detected layouts"
    )
    return cleaned_response
  except errors.HttpError as e:
    logging.exception(
        "[detect_layouts_details] - Failed to detect layouts: %s", e
    )
    raise e


def create_presentation(
    tool_context: ToolContext,
    presentation_id: str,
    request_json: List[Dict[str, Any]]
) -> Dict[str, Any]:
  """Creates a new presentation.

  Args:
    tool_context: The tool context.
    presentation_id: The presentation ID.
    request_json: The request json containing the list of operations to be
      performed for creating the presentation.

  Returns:
    Dictionary containing the status, message and result of
    the created presentation.
  """
  credentials = authenticate_google_apis_default()

  try:
    # Build Service
    service = build("slides", "v1", credentials=credentials)

    body = {"requests": request_json}

    # logging.info(
    #     "[create_presentation] - Creating presentation with response: %s",
    #     json.dumps(body)
    # )

    _ = (
        service.presentations()
        .batchUpdate(presentationId=presentation_id, body=body)
        .execute()
    )

    logging.info(
        "[create_presentation] - "
        "Created presentation: http://docs.google.com/presentation/d/%s/edit",
        presentation_id,
    )

    return {
        "status": "success",
        "message": "[create_presentation] - Created presentation Successfully",
        "result": {
            "presentation_url": (
                f"http://docs.google.com/presentation/d/{presentation_id}/edit"
            )
        },
    }

  except errors.HttpError as e:
    logging.exception(
        "[create_presentation] - Failed to create presentation: %s", e
    )
    return {
        "status": "error",
        "message": (
            f"[create_presentation] - Failed to create presentation: {e}"
        ),
        "result": {"presentation_url": None},
    }

# Change the parameter name from parent_folder_id to full_folder_path
def save_document(
    tool_context: ToolContext,
    file_name: str,
    content_key: str,
    full_folder_path: str = REPOSITORY_FOLDER_ID): # <-- Parameter name change
    """
    Saves a plaintext document to Google Drive in the specified folder/path.

    The content being saved will be read from tool context. This will be a large raw text string of HTML code.

    Args:
        file_name: The desired name for the file (e.g., 'notes.txt').
        full_folder_path: The full path or ID of the folder where the file should be saved.
                          e.g., 'SharedDriveID/Folder A/Subfolder B'.
    """
    creds = authenticate_google_apis_default()
    
    try:
        drive_service = build('drive', 'v3', credentials=creds)



        # NEW: Resolve the path to the final folder ID
        # parent_folder_id = _resolve_folder_path_to_id(
        #     drive_service, 
        #     full_folder_path, 
        #     DEFAULT_FOLDER_ID
        # )
        parent_folder_id = REPOSITORY_FOLDER_ID

        if not parent_folder_id:
            return {
                "status": "error",
                "file_name": file_name,
                "error_message": "Could not resolve the provided folder path to a valid ID.",
                "message": f"Failed to resolve path: {full_folder_path}"
            }
        
        # 1. File metadata
        file_metadata = {
            'name': file_name,
            'parents': [parent_folder_id],
            'mimeType': 'text/html'
        }
        
        # 2. Convert content string to a stream for uploading
        content = tool_context.state.get(content_key)
        media_content = io.BytesIO(content.encode('utf-8'))
        
        # 3. Create a MediaIoBaseUpload object
        media = MediaIoBaseUpload(media_content, 
                                  resumable=True)
        
        # 4. Upload the file
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink',
            supportsAllDrives=True # <-- REQUIRED FOR SHARED DRIVE
        ).execute()
        tool_context.state['document_link'] = file.get('webViewLink')
        return {
            "status": "success",
            "file_id": file.get('id'),
            "file_name": file.get('name'),
            "message": f"Successfully created document '{file.get('name')}' in folder '{parent_folder_id}' ({full_folder_path})",
            "link": file.get('webViewLink')
        }        
    except HttpError as error:
        return {
            "status": "error",
            "file_name": file_name,
            "error_message": str(error),
            "message": f"Failed to save document: {str(error)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "file_name": file_name,
            "error_message": str(e),
            "message": f"An unexpected error occurred while saving the document: {str(e)}"
        }

copy_and_replace_document_tool = FunctionTool(copy_and_replace_document)
list_drive_documents_tool = FunctionTool(list_drive_documents)
save_document_tool = FunctionTool(save_document)
