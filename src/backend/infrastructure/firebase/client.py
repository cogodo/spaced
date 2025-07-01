import json
import os

import firebase_admin
from firebase_admin import auth, credentials, firestore

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

    # When running locally, the FIREBASE_AUTH_EMULATOR_HOST env var will be set.
    # In this case, we don't need to use service account credentials.
    if os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
        print("Using Firebase emulator; skipping service account credentials.")
        _app = firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
        return

    # For local development without emulators, try to load the service account file directly.
    if settings.is_development:
        try:
            service_account_path = os.path.join(os.path.dirname(__file__), "..", "..", "firebase_service_account.json")
            if os.path.exists(service_account_path):
                print(f"Loading service account from: {service_account_path}")
                cred = credentials.Certificate(service_account_path)
                _app = firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
                return
        except Exception as e:
            print(f"FIREBASE WARNING: Could not load local service account file: {e}")

    # For production, load credentials from the service account JSON.
    if settings.firebase_service_account_json:
        try:
            service_account_info = json.loads(settings.firebase_service_account_json)
            cred = credentials.Certificate(service_account_info)
            _app = firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
        except json.JSONDecodeError:
            json_snippet = (settings.firebase_service_account_json or "")[:100]
            print(f"FIREBASE ERROR: Failed to parse service account JSON. Snippet: {json_snippet}...")
        except Exception as e:
            print(f"FIREBASE ERROR: Failed to initialize Firebase: {e}")
    else:
        print("FIREBASE WARNING: No service account credentials provided for production.")


def get_firestore_client():
    """Get a Firestore client, initializing Firebase if needed."""
    global _firestore_client
    if _app is None:
        initialize_firebase()

    if _firestore_client is None and _app:
        _firestore_client = firestore.client(app=_app)

    return _firestore_client


def get_auth():
    if _app is None:
        initialize_firebase()
    return auth
