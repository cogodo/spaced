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
    2. A service account file specified by the GOOGLE_APPLICATION_CREDENTIALS
       environment variable.
    """
    global _app
    if _app:
        return

    options = {"projectId": settings.firebase_project_id}

    # When running with emulators, FIREBASE_AUTH_EMULATOR_HOST will be set.
    # In this case, we don't need to use service account credentials.
    if os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
        print("Using Firebase emulator; skipping service account credentials.")
        _app = firebase_admin.initialize_app(options=options)
        return

    # For production or local development against live services,
    # we must have a valid credential file.
    credential_path = settings.google_application_credentials
    if not credential_path or not os.path.exists(credential_path):
        print("FATAL: GOOGLE_APPLICATION_CREDENTIALS path is not valid or file does not exist.")
        print(f"  Path: {credential_path}")
        raise SystemExit("Fatal: Firebase credentials not found.")

    try:
        print(f"Initializing Firebase with credentials from: {credential_path}")
        cred = credentials.Certificate(credential_path)
        _app = firebase_admin.initialize_app(cred, options)
        print("Firebase initialized successfully.")

    except Exception as e:
        print("FATAL: Failed to initialize Firebase from credentials file. The server will exit.")
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
