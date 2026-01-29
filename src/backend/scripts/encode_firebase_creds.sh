#!/bin/bash
# Helper script to encode Firebase service account JSON for Railway deployment
# Usage: ./scripts/encode_firebase_creds.sh /path/to/service-account.json

if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/service-account.json"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: File not found: $1"
    exit 1
fi

echo "=== Base64-encoded Firebase credentials ==="
echo ""
echo "Copy this value and set it as GOOGLE_APPLICATION_CREDENTIALS_BASE64 in Railway:"
echo ""
base64 -i "$1" | tr -d '\n'
echo ""
echo ""
echo "=== Done ==="
