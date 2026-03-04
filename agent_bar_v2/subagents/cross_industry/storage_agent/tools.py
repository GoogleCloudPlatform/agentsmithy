"""
Google Cloud Storage (GCS) Bucket Management Tools for ADK

This module provides tools for creating and listing GCS buckets
to be used with the Agent Development Kit (ADK).
"""

from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError, NotFound
from google.adk.tools import ToolContext, FunctionTool
from typing import Dict, Any, Optional
import logging


PROJECT_ID='ai-agent-bar-2026-dev'
GCS_LIST_BUCKETS_MAX_RESULTS = 100
GCS_LIST_BLOBS_MAX_RESULTS = 100
GCS_DEFAULT_STORAGE_CLASS='STANDARD'
GCS_DEFAULT_LOCATION='us-central1'
GCS_DEFAULT_CONTENT_TYPE = 'text/plain'
LOG_LEVEL='INFO'
LOG_FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)

# Initialize the GCS client
client = storage.Client(project=PROJECT_ID)

def create_gcs_bucket(
    tool_context: ToolContext,
    bucket_name: str,
    storage_class: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new Google Cloud Storage bucket.
    
    Args:
        tool_context: The tool context for ADK
        bucket_name: The name of the bucket to create
        storage_class: Storage class for the bucket (default: STANDARD)
        location: Location for the bucket (default: US for multi-regional)
        
    Returns:
        A dictionary containing the result of the bucket creation
    """
    if storage_class is None:
        storage_class = GCS_DEFAULT_STORAGE_CLASS
    if location is None:
        location = GCS_DEFAULT_LOCATION
    try:
        # Initialize the client
        client = storage.Client(project=PROJECT_ID)
        
        # Check if the bucket already exists
        try:
            if client.lookup_bucket(bucket_name):
                return {
                    "status": "error", 
                    "message": f"Bucket {bucket_name} already exists"
                }
        except Exception:
            # Bucket doesn't exist, continue with creation
            pass
            
        # Create the bucket
        bucket = client.bucket(bucket_name)
        bucket.storage_class = storage_class
        bucket = client.create_bucket(bucket, location=location)
        
        # Save the bucket name in state for easy reference later
        if hasattr(tool_context, "state"):
            tool_context.state["last_bucket_name"] = bucket_name
        
        # Return success message with details
        result = {
            "status": "success",
            "bucket_name": bucket_name,
            "self_link": f"https://storage.googleapis.com/{bucket_name}",
            "storage_class": bucket.storage_class,
            "location": bucket.location,
            "message": f"Successfully created bucket '{bucket_name}' in location '{location}'"
        }
        
        return result
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to create bucket: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def list_gcs_buckets(
    prefix: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    Lists Google Cloud Storage buckets in the configured project.
    
    Args:
        prefix: Optional prefix to filter buckets by name
        max_results: Maximum number of results to return (default: 50)
        
    Returns:
        A dictionary containing the list of buckets
    """
    if max_results is None:
        max_results = GCS_LIST_BUCKETS_MAX_RESULTS
    try:
        # Initialize the client
        client = storage.Client(project=PROJECT_ID)
        
        # List the buckets with optional filtering
        bucket_iterator = client.list_buckets(prefix=prefix, max_results=max_results)
        
        bucket_list = []
        for bucket in bucket_iterator:
            bucket_list.append({
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "created": bucket.time_created.isoformat() if bucket.time_created else None,
                "updated": bucket.updated.isoformat() if hasattr(bucket, "updated") and bucket.updated else None
            })
        
        return {
            "status": "success",
            "buckets": bucket_list,
            "count": len(bucket_list),
            "message": f"Found {len(bucket_list)} bucket(s)" + (f" with prefix '{prefix}'" if prefix else "")
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to list buckets: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def get_bucket_details(
    bucket_name: str
) -> Dict[str, Any]:
    """
    Gets detailed information about a specific GCS bucket, including a list of all files (blobs).
    
    Args:
        bucket_name: The name of the bucket to get details for
        
    Returns:
        A dictionary containing the bucket details and a list of files
    """
    try:
        # Initialize the client
        client = storage.Client(project=PROJECT_ID)
        
        # Get the bucket
        bucket = client.get_bucket(bucket_name)
        
        # List all blobs in the bucket
        blobs = client.list_blobs(bucket_name)
        blob_list = []
        for blob in blobs:
            blob_list.append({
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "gcs_uri": f"gs://{bucket_name}/{blob.name}",
                "public_url": f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
            })
        
        # Return detailed information
        return {
            "status": "success",
            "bucket": {
                "name": bucket.name,
                "id": bucket.id,
                "project_number": bucket.project_number,
                "location": bucket.location,
                "location_type": bucket.location_type,
                "storage_class": bucket.storage_class,
                "created": bucket.time_created.isoformat() if bucket.time_created else None,
                "updated": bucket.updated.isoformat() if hasattr(bucket, "updated") and bucket.updated else None,
                "versioning_enabled": bucket.versioning_enabled,
                "labels": bucket.labels,
                "requester_pays": bucket.requester_pays,
                "self_link": f"https://storage.googleapis.com/{bucket_name}",
                "etag": bucket.etag,
                "files": blob_list,
                "file_count": len(blob_list)
            },
            "message": f"Successfully retrieved details and {len(blob_list)} file(s) for bucket '{bucket_name}'"
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to get bucket details: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def list_blobs_in_bucket(
    bucket_name: str,
    prefix: Optional[str] = None,
    delimiter: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    Lists blobs (files) in a Google Cloud Storage bucket.
    
    Args:
        bucket_name: The name of the bucket to list blobs from
        prefix: Optional prefix to filter blobs by name
        delimiter: Optional delimiter for hierarchy simulation (e.g., '/' for folders)
        max_results: Maximum number of results to return (default: 100)
        
    Returns:
        A dictionary containing the list of blobs and prefixes (if delimiter is used)
    """
    if max_results is None:
        max_results = GCS_LIST_BLOBS_MAX_RESULTS
    try:
        # Initialize the client
        client = storage.Client(project=PROJECT_ID)
        
        # Get the bucket
        bucket = client.bucket(bucket_name)
        
        # List blobs with optional filtering
        blobs = client.list_blobs(
            bucket_name, 
            prefix=prefix, 
            delimiter=delimiter,
            max_results=max_results
        )
        
        # Process the results
        blob_list = []
        prefix_list = []
        
        # Save actual blobs
        for blob in blobs:
            blob_list.append({
                "name": blob.name,
                "size": blob.size,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "content_type": blob.content_type,
                "public_url": f"https://storage.googleapis.com/{bucket_name}/{blob.name}",
                "gcs_uri": f"gs://{bucket_name}/{blob.name}"
            })
        
        # If using delimiter, also save prefixes (folders)
        if delimiter:
            prefix_list = list(blobs.prefixes)
        
        return {
            "status": "success",
            "bucket_name": bucket_name,
            "blobs": blob_list,
            "prefixes": prefix_list,
            "count": len(blob_list),
            "prefix_count": len(prefix_list),
            "message": f"Found {len(blob_list)} file(s) and {len(prefix_list)} folder(s) in bucket '{bucket_name}'"
                      + (f" with prefix '{prefix}'" if prefix else "")
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to list files in bucket: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def upload_file_to_gcs(
    tool_context: ToolContext,
    bucket_name: str,
    file_artifact_name: str,
    destination_blob_name: Optional[str] = None,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uploads a file from ADK artifacts to a Google Cloud Storage bucket.
    
    Args:
        tool_context: The tool context for ADK
        bucket_name: The name of the GCS bucket to upload to
        file_artifact_name: The name of the artifact file in the ADK session
        destination_blob_name: The name to give the file in GCS (defaults to artifact name)
        content_type: The content type of the file (defaults to PDF)
        
    Returns:
        A dictionary containing the upload status and details
    """
    if content_type is None:
        content_type = GCS_DEFAULT_CONTENT_TYPE
    try:
        # Check if user_content contains a PDF attachment
        if (hasattr(tool_context, "user_content") and 
            tool_context.user_content and 
            tool_context.user_content.parts):
            
            # Look for any file in parts
            file_data = None
            for part in tool_context.user_content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    if part.inline_data.mime_type.startswith("application/"):
                        file_data = part.inline_data.data
                        break
            
            if file_data:
                # We found file data in the user message
                if not destination_blob_name:
                    destination_blob_name = file_artifact_name
                    if content_type == "application/pdf" and not destination_blob_name.lower().endswith(".pdf"):
                        destination_blob_name += ".pdf"
                
                # Upload to GCS
                client = storage.Client(project=PROJECT_ID)
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(destination_blob_name)
                
                blob.upload_from_string(
                    data=file_data,
                    content_type=content_type
                )
                
                # Generate a URL
                try:
                    url = blob.public_url
                except:
                    url = f"gs://{bucket_name}/{destination_blob_name}"
                
                return {
                    "status": "success",
                    "bucket": bucket_name,
                    "filename": destination_blob_name,
                    "gcs_uri": f"gs://{bucket_name}/{destination_blob_name}",
                    "size_bytes": len(file_data),
                    "content_type": content_type,
                    "url": url,
                    "message": f"Successfully uploaded file to gs://{bucket_name}/{destination_blob_name}"
                }
        
        # If no file found in user content, return error
        return {
            "status": "error",
            "message": "No file found in the current message. Please upload a file and try again.",
            "details": "Files must be attached directly to the current message."
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to upload file: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }
        
def get_file_contents(tool_context: ToolContext, bucket_name: str, blob_name: str, key_name: str | None = None):
    """Reads a blob from GCS into memory.

    Args:
        bucket_name: The name of the GCS bucket.
        blob_name: The name/path of the blob within the bucket.

    Returns:
        The content of the blob as bytes if successful, otherwise None.
    """
    try:
        # Initialize a client
        storage_client = storage.Client(project=PROJECT_ID)

        # Get the bucket
        bucket = storage_client.bucket(bucket_name)

        # Get the blob
        blob = bucket.blob(blob_name)

        # Download the contents of the blob as bytes
        blob_contents_bytes = blob.download_as_bytes()

        print(f"Blob '{blob_name}' from bucket '{bucket_name}' downloaded into memory.")
        if key_name is not None:
            # 1. Convert bytes to a string
            raw_string = blob_contents_bytes.decode('utf-8')
            # 2. Remove newline characters (if you want it all on one line)
            tool_context.state[key_name] = raw_string
            tool_context.save_artifact[key_name] = raw_string
        else:
            tool_context.state[blob_name] = str(blob_contents_bytes)
            tool_context.save_artifact[key_name] = str(blob_contents_bytes)
        return {
            "status": "success",
            "bucket": bucket_name,
            "filename": blob_name,
            "gcs_uri": f"gs://{bucket_name}/{blob_name}",
            # "size_bytes": len(blob_contents_bytes),
            # "contents": blob_contents_bytes,
            "message": "template saved to tool context state!"
                }

    except NotFound as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"file was not found: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

# Create FunctionTools from the functions
create_bucket_tool = FunctionTool(create_gcs_bucket)
list_buckets_tool = FunctionTool(list_gcs_buckets)
get_bucket_details_tool = FunctionTool(get_bucket_details)
list_blobs_tool = FunctionTool(list_blobs_in_bucket)
upload_file_gcs_tool = FunctionTool(upload_file_to_gcs) 
get_file_contents_tool = FunctionTool(get_file_contents)
