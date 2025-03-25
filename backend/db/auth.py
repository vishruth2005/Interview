import os
import firebase_admin
from firebase_admin import credentials, auth

# Load environment variables (make sure these are set in your environment)
firebase_config = {
    "type": os.getenv("FIREBASE_TYPE", "service_account"),
    "project_id": os.getenv("VITE_FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("VITE_FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("VITE_FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("VITE_FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("VITE_FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("VITE_FIREBASE_CLIENT_CERT_URL")
}

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)

# Now you can use Firebase auth features, for example:
user = auth.get_user_by_email('example@example.com')
print('Successfully fetched user data:', user.uid)
