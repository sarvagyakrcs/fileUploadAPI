# api/views.py
import os
import time
from rest_framework import generics
from django.shortcuts import get_object_or_404
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from .models import File
from .serializers import FileSerializer

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_PATH = os.path.join(os.getcwd(), "driveApp", "credentials.json")

def get_credentials(file_path=None):
    creds = None
    token_path = "token.json"
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=3000)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds

def upload_basic(file_path):
    try:
        creds = get_credentials()

        # Create drive API client
        service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": os.path.basename(file_path)}
        media = MediaFileUpload(file_path, mimetype="image/jpeg")

        print("Uploading file...")
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink, webContentLink")
            .execute()
        )

        file_id = file.get("id")

        # Wait for a short duration before retrieving the webViewLink
        time.sleep(1)

        # Retrieve the file details again to get the webContentLink
        file = service.files().get(fileId=file_id, fields="id, webViewLink, webContentLink").execute()
        web_view_link = file.get("webViewLink")
        web_content_link = file.get("webContentLink")

        print(f'File ID: {file_id}')
        print(f'File URL (webViewLink): {web_view_link}')
        print(f'File URL (webContentLink): {web_content_link}')

        # Add permission for "anyone" to view the file
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        service.permissions().create(fileId=file_id, body=permission).execute()
        print("Permissions updated. File is now viewable by everyone.")

        return file_id, web_content_link

    except HttpError as error:
        print(f"An error occurred: {error}")
        return {
            "error": f"An error occurred: {error}",
            "file": None,
        }

class FileListCreateView(generics.ListCreateAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def perform_create(self, serializer):
        # Save the instance to get the object with the file path
        instance = serializer.save()
        print('calling upload_basic...')        
        upload_basic(str(instance.file))

class FileRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    lookup_field = 'name'
