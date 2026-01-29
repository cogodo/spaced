import base64
import json
import os

import firebase_admin
from firebase_admin import auth, credentials, firestore

from app.config import settings

_app = None
_firestore_client = None


def initialize_firebase():
    """
    Initializes the Firebase Admin SDK.
    It uses the following priority for credentials:
    1. Firebase Emulators if FIREBASE_AUTH_EMULATOR_HOST is set.
    2. Base64-encoded credentials from GOOGLE_APPLICATION_CREDENTIALS_BASE64 (Railway/Heroku)
    3. JSON string credentials from FIREBASE_SERVICE_ACCOUNT_JSON
    4. A service account file specified by the GOOGLE_APPLICATION_CREDENTIALS env var.
    """
    global _app
    if _app:
        return

    options = {"projectId": settings.firebase_project_id}

    # When running with emulators, FIREBASE_AUTH_EMULATOR_HOST and/or
    # FIRESTORE_EMULATOR_HOST may be set. In this case, we don't need to use
    # service account credentials and should initialize without a credential.
    if os.getenv("FIREBASE_AUTH_EMULATOR_HOST") or os.getenv("FIRESTORE_EMULATOR_HOST"):
        print("Using Firebase emulators; skipping service account credentials.")
        _app = firebase_admin.initialize_app(options=options)
        return

    cred = None

    # Option 1: Base64-encoded credentials (Railway/Heroku standard)
    base64_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
    if base64_creds:
        try:
            print("Initializing Firebase with base64-encoded credentials...")
            creds_json = base64.b64decode(base64_creds).decode("utf-8")
            creds_dict = json.loads(creds_json)
            cred = credentials.Certificate(creds_dict)
        except Exception as e:
            print(f"Failed to decode base64 credentials: {e}")

    # Option 2: JSON string credentials
    if not cred:
        json_creds = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        if json_creds:
            try:
                print("Initializing Firebase with JSON string credentials...")
                creds_dict = json.loads(json_creds)
                cred = credentials.Certificate(creds_dict)
            except Exception as e:
                print(f"Failed to parse JSON credentials: {e}")

    # Option 3: File path (local development)
    if not cred:
        credential_path = settings.google_application_credentials
        if credential_path and os.path.exists(credential_path):
            try:
                print(f"Initializing Firebase with credentials from: {credential_path}")
                cred = credentials.Certificate(credential_path)
            except Exception as e:
                print(f"Failed to load credentials from file: {e}")

    if not cred:
        print("FATAL: No valid Firebase credentials found.")
        print(
            "  Set one of: GOOGLE_APPLICATION_CREDENTIALS_BASE64, FIREBASE_SERVICE_ACCOUNT_JSON, or GOOGLE_APPLICATION_CREDENTIALS"
        )
        raise SystemExit("Fatal: Firebase credentials not found.")

    try:
        _app = firebase_admin.initialize_app(cred, options)
        print("Firebase initialized successfully.")
    except Exception as e:
        print("FATAL: Failed to initialize Firebase. The server will exit.")
        print(f"  Error: {e}")
        raise SystemExit("Fatal: Firebase initialization failed.") from e


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
