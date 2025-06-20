import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config import settings


_app = None
_firestore_client = None


def initialize_firebase():
    global _app, _firestore_client
    
    if _app is None:
        if settings.firebase_service_account_path:
            cred = credentials.Certificate(settings.firebase_service_account_path)
        else:
            # Use default credentials from environment
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