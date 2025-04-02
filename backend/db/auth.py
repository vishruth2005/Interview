import os
from authlib.integrations.flask_client import OAuth
from functools import wraps
from flask import redirect, session, url_for
import firebase_admin
from firebase_admin import credentials, auth, firestore

oauth = OAuth()
auth0 = oauth.register(
    'auth0',
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    api_base_url=f'https://{os.getenv("AUTH0_DOMAIN")}',
    access_token_url=f'https://{os.getenv("AUTH0_DOMAIN")}/oauth/token',
    authorize_url=f'https://{os.getenv("AUTH0_DOMAIN")}/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },  
)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session or 'token' not in session:
            return redirect('/login')
        return f(*args, token=session['token'], **kwargs)
    return decorated




# Load environment variables (make sure these are set in your environment)
firebase_config = {
    "apiKey": os.getenv("VITE_FIREBASE_API_KEY"),
    "authDomain": os.getenv("VITE_FIREBASE_AUTH_DOMAIN"),
    "databse_url": os.getenv("VITE_FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("VITE_FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("VITE_FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("VITE_FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("VITE_FIREBASE_APP_ID"),
    "measurementId": os.getenv("VITE_FIREBASE_MEASUREMENT_ID")
}

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("./serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


#addded lines for testing manually

# data = {
#   "user_id": "abc123xyz"
# }

# doc_ref = db.collection("AI_Interview").document("Interview").collection("USER").add(data)
# print("Document written to AI_Interview/USER with ID:", doc_ref[1].id)


firebase_auth = auth

