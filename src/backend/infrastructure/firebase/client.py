import json

import firebase_admin
from firebase_admin import auth, credentials

from app.config import settings

_app = None
_firestore_client = None


def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using credentials from environment variables.
    """
    global _app
    if _app:
        return

    cred = None

    if settings.firebase_service_account_json:
        try:
            service_account_info = json.loads(settings.firebase_service_account_json)
            cred = credentials.Certificate(service_account_info)
        except json.JSONDecodeError:
            print("FIREBASE ERROR: Failed to parse service account JSON")
            cred = None
    else:
        print("FIREBASE WARNING: No service account credentials provided")

    if cred:
        try:
            _app = firebase_admin.initialize_app(
                cred, {"projectId": settings.firebase_project_id}
            )
        except Exception as e:
            print(f"FIREBASE ERROR: Failed to initialize Firebase: {e}")


def get_firestore_client():
    """Get a Firestore client, initializing Firebase if needed."""
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client


def get_auth():
    if _app is None:
        initialize_firebase()
    return auth
