# firebase_config.py
import pyrebase, datetime

FIREBASE_CONFIG = {
    "apiKey":            "AIzaSyDL3jN1w0hoMrbgYfH-vG6UmfGWwSPYuok",
    "authDomain":        "student-performance-app-9b5e4.firebaseapp.com",
    "databaseURL":       "https://student-performance-app-9b5e4-default-rtdb.firebaseio.com",
    "projectId":         "student-performance-app-9b5e4",
    "storageBucket":     "student-performance-app-9b5e4.firebasestorage.app",
    "messagingSenderId": "1085997407558",
    "appId":             "1:1085997407558:web:862860057a543ed1dcd947"
}

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
auth = firebase.auth()
db   = firebase.database()

def register_user(email, password, name, college, class_name):
    try:
        user  = auth.create_user_with_email_and_password(email, password)
        uid   = user["localId"]; token = user["idToken"]
        profile = {"name":name,"email":email,"college":college,"class_name":class_name,
                   "created_at":str(datetime.datetime.now()),"streak":0,"total_sessions":0,"best_confidence":0}
        db.child("users").child(uid).set(profile, token)
        return {"success":True,"user":user,"profile":profile}
    except Exception as e:
        msg=str(e)
        if "EMAIL_EXISTS"    in msg: return {"success":False,"error":"Email already registered!"}
        if "WEAK_PASSWORD"   in msg: return {"success":False,"error":"Password must be 6+ characters!"}
        if "INVALID_EMAIL"   in msg: return {"success":False,"error":"Invalid email address!"}
        return {"success":False,"error":"Registration failed. Try again."}

def login_user(email, password):
    try:
        user  = auth.sign_in_with_email_and_password(email, password)
        uid   = user["localId"]; token = user["idToken"]
        profile = db.child("users").child(uid).get(token).val()
        return {"success":True,"user":user,"profile":profile or {}}
    except Exception as e:
        msg=str(e)
        if "INVALID_PASSWORD"          in msg: return {"success":False,"error":"Wrong password!"}
        if "INVALID_LOGIN_CREDENTIALS" in msg: return {"success":False,"error":"Wrong email or password!"}
        if "EMAIL_NOT_FOUND"           in msg: return {"success":False,"error":"Email not found. Register first!"}
        if "TOO_MANY_ATTEMPTS"         in msg: return {"success":False,"error":"Too many attempts. Try later."}
        return {"success":False,"error":"Login failed. Check credentials."}

def save_prediction(uid, token, data):
    try:
        db.child("users").child(uid).child("predictions").push(data, token)
        profile=db.child("users").child(uid).get(token).val() or {}
        db.child("users").child(uid).update({
            "total_sessions":profile.get("total_sessions",0)+1,
            "best_confidence":max(profile.get("best_confidence",0),data.get("confidence",0)),
            "last_active":str(datetime.datetime.now())}, token)
        return True
    except: return False

def get_user_predictions(uid, token):
    try:
        data=db.child("users").child(uid).child("predictions").get(token).val()
        return list(data.values()) if data else []
    except: return []

def get_class_leaderboard(college, class_name):
    try:
        all_users=db.child("users").get().val()
        if not all_users: return []
        lb=[]
        for uid,p in all_users.items():
            if (p.get("college","").strip().lower()==college.strip().lower() and
                p.get("class_name","").strip().lower()==class_name.strip().lower()):
                lb.append({"name":p.get("name","Anonymous"),"college":p.get("college",""),
                           "class_name":p.get("class_name",""),"total_sessions":p.get("total_sessions",0),
                           "best_confidence":p.get("best_confidence",0),"streak":p.get("streak",0)})
        lb.sort(key=lambda x:(x["best_confidence"],x["total_sessions"]),reverse=True)
        return lb
    except: return []

def update_streak(uid, token, streak):
    try: db.child("users").child(uid).update({"streak":streak},token); return True
    except: return False