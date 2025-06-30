import json

import firebase_admin
from firebase_admin import auth, credentials, firestore

from app.config import settings

_app = None
_firestore_client = None


def initialize_firebase():
    global _app, _firestore_client

    if _app is None:
        cred = None

        print("FIREBASE DEBUG: Starting Firebase initialization")
        print(f"FIREBASE DEBUG: Project ID from settings: {settings.firebase_project_id}")
        print(f"FIREBASE DEBUG: Service account JSON exists: {bool(settings.firebase_service_account_json)}")
        print(f"FIREBASE DEBUG: Service account path exists: {bool(settings.firebase_service_account_path)}")

        # Priority 1: Use JSON content from environment variable
        if settings.firebase_service_account_json:
            try:
                service_account_info = json.loads(settings.firebase_service_account_json)
                print("FIREBASE DEBUG: Service account JSON exists: " f"{bool(settings.firebase_service_account_json)}")
                print("FIREBASE DEBUG: Service account path exists: " f"{bool(settings.firebase_service_account_path)}")
                cred = credentials.Certificate(service_account_info)
            except json.JSONDecodeError:
                print("FIREBASE ERROR: Failed to parse service account JSON")
                cred = None

        # Priority 2: Use file path if provided
        elif settings.firebase_service_account_path:
            print("FIREBASE DEBUG: Using credentials file: " f"{settings.firebase_service_account_path}")
            cred = credentials.Certificate(settings.firebase_service_account_path)

        # Priority 3: Use default credentials from environment
        else:
            print("FIREBASE WARNING: No service account credentials provided")

        if cred:
            try:
                firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
                print(
                    (
                        "FIREBASE DEBUG: Firebase app initialized successfully for "
                        f"project: {settings.firebase_project_id}"
                    )
                )
            except ValueError as e:
                print(f"FIREBASE ERROR: Firebase already initialized? Error: {e}")
            except Exception as e:
                print(f"FIREBASE ERROR: Failed to initialize Firebase: {e}")

    if _firestore_client is None:
        _firestore_client = firestore.client()
        print("FIREBASE DEBUG: Firestore client initialized")

    return _app


def get_firestore_client():
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client


def get_auth():
    if _app is None:
        initialize_firebase()
    return auth
