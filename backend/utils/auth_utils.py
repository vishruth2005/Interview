from firebase_admin import auth, firestore
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
import streamlit as st
import time
import os

def is_token_valid():
    """Check if the current session token is valid."""
    if 'id_token' not in st.session_state:
        return False
        
    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            st.session_state.id_token,
            requests.Request(),
            st.secrets["GOOGLE_CLIENT_ID"],
            clock_skew_in_seconds=900
        )
        
        # Check if token is not expired
        current_time = int(time.time())
        if current_time >= id_info['exp']:
            return False
            
        # Verify email domain
        if not id_info['email'].endswith('@nitk.edu.in'):
            return False
            
        return True
    except Exception:
        return False

def check_auth():
    """Check authentication status and redirect if needed."""
    # Check if we have all required session data
    required_keys = ['id_token', 'user_info', 'logged_in']
    if not all(key in st.session_state for key in required_keys):
        return False
        
    # Verify token validity
    if not is_token_valid():
        clear_session()
        return False
        
    return True
def auto_login():
    """Attempt to automatically log in using stored tokens."""
    if all(key in st.session_state for key in ['id_token', 'logged_in', 'user_info']):
        if is_token_valid(st.session_state.id_token):
            return True
    return False

def verify_google_token(token):
    try:
        # Increased clock skew tolerance and added specific error handling
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            st.secrets["GOOGLE_CLIENT_ID"],
            clock_skew_in_seconds=600  # 10 minutes tolerance
        )

        # Additional validation
        current_time = int(time.time())
        
        # Check if token is not expired
        if current_time >= idinfo['exp']:
            raise ValueError('Token has expired')
            
        # Check if token is valid for use
        if current_time < idinfo['iat'] - 600:  # Allow 10 minutes skew
            st.warning("Warning: Your system clock might be out of sync")
            # Continue anyway since we have high tolerance

        email = idinfo['email']
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        
        return {
            'email': email,
            'name': name,
            'picture': picture,
            'auth_time': current_time
        }
    except ValueError as ve:
        st.error(f"Authentication error: {str(ve)}")
        # Add debug information
        st.info("Please check if your system clock is synchronized")
        return None
    except Exception as e:
        st.error("Authentication failed. Please try again.")
        print(f"Debug - Auth Error: {str(e)}")  # For debugging
        return None
    
def save_user_to_firebase(user_info):
    db = firestore.client()
    user_ref = db.collection('users').document(user_info['email'])
    user_ref.set({
        'name': user_info['name'],
        'email': user_info['email'],
        'picture': user_info['picture'],
        'last_login': datetime.datetime.now()
    })

def check_session_validity():
    """Check if the current session is valid (less than 2 hours old)."""
    if 'login_time' not in st.session_state:
        return False
    
    # Check if 2 hours have passed since login
    current_time = time.time()
    login_time = st.session_state.login_time
    
    # Convert datetime to timestamp if needed
    if isinstance(login_time, datetime.datetime):
        login_time = login_time.timestamp()
    
    try:
        time_diff = current_time - float(login_time)
        # 2 hours = 7200 seconds
        return time_diff < 7200
    except (TypeError, ValueError):
        # If conversion fails, session is invalid
        return False

def init_session(user_info):
    st.session_state.logged_in = True
    st.session_state.login_time = time.time()
    st.session_state.user_info = user_info

def clear_session():
    st.session_state.logged_in = False
    if 'login_time' in st.session_state:
        del st.session_state.login_time
    if 'user_info' in st.session_state:
        del st.session_state.user_info
