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

    # For production, we MUST have valid credentials.
    # If initialization fails here, the application is misconfigured and should not start.
    elif settings.firebase_service_account_json:
        try:
            print("Attempting to initialize Firebase for production...")
            service_account_info = json.loads(settings.firebase_service_account_json)
            cred = credentials.Certificate(service_account_info)
            _app = firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
            print("Firebase initialized successfully for production.")
        except Exception as e:
            json_snippet = (settings.firebase_service_account_json or "")[:150]
            print("FATAL: Failed to initialize Firebase for production. The server will exit.")
            print(f"Error: {e}")
            print(f"Service account JSON snippet: {json_snippet}...")
            # In a production/staging environment, this is a fatal error.
            raise SystemExit("Fatal: Firebase initialization failed.") from e
    else:
        # If we are in production and have no credentials, it's a fatal error.
        print("FATAL: In a production environment, FIREBASE_SERVICE_ACCOUNT_JSON must be set.")
        raise SystemExit("Fatal: Firebase credentials not configured.")


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
