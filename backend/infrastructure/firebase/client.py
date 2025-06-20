import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config import settings
import json
import tempfile
import os


_app = None
_firestore_client = None


def initialize_firebase():
    global _app, _firestore_client
    
    if _app is None:
        cred = None
        
        # Priority 1: Use JSON content from environment variable
        if settings.firebase_service_account_json:
            try:
                # Parse the JSON string and create credentials from dict
                service_account_info = json.loads(settings.firebase_service_account_json)
                cred = credentials.Certificate(service_account_info)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
        
        # Priority 2: Use file path if provided
        elif settings.firebase_service_account_path:
            cred = credentials.Certificate(settings.firebase_service_account_path)
        
        # Priority 3: Use default credentials from environment
        else:
            cred = credentials.ApplicationDefault()
            
        _app = firebase_admin.initialize_app(cred, {
            'projectId': settings.firebase_project_id,
        })
        
    if _firestore_client is None:
        _firestore_client = firestore.client()
        
    return _app


def get_firestore_client():
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client


def get_auth():
    if _app is None:
        initialize_firebase()
    return auth 