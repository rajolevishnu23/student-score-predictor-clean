import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime

firebase_initialized = False

def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        return False

def register_user(email, password, name, college, class_name):
    try:
        if not init_firebase():
            return {"success": False, "error": "Firebase not available"}
        return {"success": True, "user": {"email": email}, "profile": {
            "name": name, "email": email, "college": college, "class_name": class_name,
            "created_at": str(datetime.datetime.now()), "streak": 0
        }}
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(email, password):
    try:
        if not init_firebase():
            return {"success": False, "error": "Firebase not available"}
        return {"success": True, "user": {"email": email}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_prediction(uid, subject, score, confidence):
    try:
        if not init_firebase():
            return False
        return True
    except Exception as e:
        return False

def get_user_predictions(uid):
    try:
        if not init_firebase():
            return []
        return []
    except Exception as e:
        return []

def get_class_leaderboard(class_name, limit=10):
    try:
        if not init_firebase():
            return []
        return []
    except Exception as e:
        return []

def update_streak(uid, new_streak):
    try:
        if not init_firebase():
            return False
        return True
    except Exception as e:
        return False