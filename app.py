import streamlit as st
import numpy as np
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import json, os, datetime, warnings, random

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Student Performance Predictor",page_icon="🎓",layout="wide",initial_sidebar_state="expanded")

defaults={"logged_in":False,"user":None,"profile":{},"history":[],"streak":0,
          "chat_messages":[],"exams":[],"study_log":[],"pomodoro_count":0,
          "daily_goal":5.0,"logged_today":0.0,"auth_mode":"login"}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

# ── Restore session from URL query param (survives soft reloads) ─────────────
import urllib.parse as _up, json as _js, base64 as _b64
qp = st.query_params
if not st.session_state.logged_in and "s" in qp:
    try:
        saved = _js.loads(_b64.b64decode(qp["s"]).decode())
        st.session_state.logged_in = True
        st.session_state.profile   = saved.get("profile",{})
        st.session_state.user      = saved.get("user",{})
        st.session_state.streak    = saved.get("streak",0)
    except: pass

try:
    from firebase_config import login_user,register_user,save_prediction,get_user_predictions,get_class_leaderboard,update_streak,init_firebase
    init_firebase()
    FIREBASE_ENABLED=True
except ImportError:
    FIREBASE_ENABLED=False

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.stApp{background:linear-gradient(135deg,#0f0c29 0%,#1a1040 50%,#0f0c29 100%);color:#e8e0ff;}
header[data-testid="stHeader"]{background:transparent;}
.hero-title{font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;background:linear-gradient(90deg,#a78bfa,#60a5fa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1.1;margin-bottom:0.3rem;}
.hero-sub{font-size:1rem;color:#a09cc0;font-weight:300;margin-bottom:1.5rem;}
.card{background:rgba(255,255,255,0.04);border:1px solid rgba(167,139,250,0.18);border-radius:20px;padding:1.5rem 1.8rem;margin-bottom:1.2rem;}
.card-title{font-family:'Syne',sans-serif;font-size:0.72rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#a78bfa;margin-bottom:1rem;}
.result-pass{background:linear-gradient(135deg,rgba(52,211,153,.15),rgba(16,185,129,.08));border:2px solid rgba(52,211,153,.5);border-radius:20px;padding:2rem;text-align:center;}
.result-fail{background:linear-gradient(135deg,rgba(248,113,113,.15),rgba(239,68,68,.08));border:2px solid rgba(248,113,113,.5);border-radius:20px;padding:2rem;text-align:center;}
.result-label{font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:800;}
.result-label-pass{color:#34d399;}.result-label-fail{color:#f87171;}
.result-conf{font-size:.95rem;color:#a09cc0;margin-top:.5rem;}
.stat-box{background:rgba(255,255,255,.04);border:1px solid rgba(167,139,250,.15);border-radius:14px;padding:1rem;text-align:center;}
.stat-val{font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:700;color:#a78bfa;}
.stat-lbl{font-size:.75rem;color:#7c6fa0;margin-top:.2rem;}
[data-testid="stSidebar"]{background:rgba(15,12,41,.97)!important;border-right:1px solid rgba(167,139,250,.12);}
.stButton>button{background:linear-gradient(135deg,#7c3aed,#4f46e5)!important;color:white!important;border:none!important;border-radius:12px!important;padding:.75rem 2rem!important;font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:.95rem!important;width:100%!important;box-shadow:0 4px 20px rgba(124,58,237,.35)!important;}
.tip-box{background:rgba(96,165,250,.08);border-left:3px solid #60a5fa;border-radius:0 10px 10px 0;padding:.8rem 1.1rem;font-size:.87rem;color:#93c5fd;margin-bottom:.8rem;}
.tip-warn{background:rgba(251,191,36,.08);border-left:3px solid #fbbf24;border-radius:0 10px 10px 0;padding:.8rem 1.1rem;font-size:.87rem;color:#fde68a;margin-bottom:.8rem;}
.tip-good{background:rgba(52,211,153,.08);border-left:3px solid #34d399;border-radius:0 10px 10px 0;padding:.8rem 1.1rem;font-size:.87rem;color:#6ee7b7;margin-bottom:.8rem;}
.badge{display:inline-block;border-radius:20px;padding:.3rem .9rem;font-size:.78rem;color:white;margin:.2rem;font-weight:600;}
.subject-card{background:rgba(255,255,255,.04);border:1px solid rgba(167,139,250,.15);border-radius:16px;padding:1.2rem;text-align:center;margin-bottom:.8rem;}
.chat-bubble-bot{background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.25);border-radius:18px 18px 18px 4px;padding:.9rem 1.2rem;margin-bottom:.6rem;font-size:.88rem;color:#e8e0ff;max-width:85%;}
.chat-bubble-user{background:rgba(79,70,229,.25);border:1px solid rgba(79,70,229,.4);border-radius:18px 18px 4px 18px;padding:.9rem 1.2rem;margin-bottom:.6rem;font-size:.88rem;color:#e8e0ff;max-width:85%;margin-left:auto;}
.chat-time{font-size:.7rem;color:#4a4060;margin-top:.3rem;}
.exam-card{background:rgba(255,255,255,.03);border:1px solid rgba(167,139,250,.15);border-radius:14px;padding:1rem 1.2rem;margin-bottom:.6rem;}
.profile-chip{display:inline-block;background:rgba(167,139,250,.15);border:1px solid rgba(167,139,250,.3);border-radius:20px;padding:.3rem .9rem;font-size:.78rem;color:#c4b5fd;margin:.2rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    with open("model.pkl","rb") as f: model=pickle.load(f)
    with open("scaler.pkl","rb") as f: scaler=pickle.load(f)
    return model,scaler

@st.cache_data
def load_data(): return pd.read_csv("dataset.csv")

model,scaler=load_model()
df=load_data()

def predict(study,attend,prev,sleep,assign):
    inp=scaler.transform(np.array([[study,attend,prev,sleep,assign]]))
    pred=model.predict(inp)[0]; prob=model.predict_proba(inp)[0]
    return pred,prob[pred]*100

def risk_score(study,attend,prev,sleep,assign):
    pred,conf=predict(study,attend,prev,sleep,assign)
    return max(0,100-conf) if pred==1 else min(100,conf)

def get_badges(study,attend,prev,sleep,assign):
    b=[]
    if study>=7:  b.append(("📚 Study Beast","#f59e0b"))
    if attend>=90:b.append(("🏫 Star","#f59e0b"))
    if prev>=80:  b.append(("🏆 High Achiever","#f59e0b"))
    if sleep>=7:  b.append(("😴 Well Rested","#059669"))
    if assign>=9: b.append(("✅ Assignment Pro","#059669"))
    if study>=5 and attend>=75 and prev>=60: b.append(("🌟 Balanced","#7c3aed"))
    return b

# ══════════════════════════════════════════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""<div style='text-align:center;padding:2.5rem 0 1rem;'>
        <div style='font-size:3.5rem;'>🎓</div>
        <div class='hero-title' style='font-size:2.5rem;text-align:center;'>Student Performance Predictor</div>
        <div style='font-size:1rem;color:#a09cc0;margin-top:.5rem;'>AI-powered coaching · Class leaderboards · Exam timetable</div>
    </div>""", unsafe_allow_html=True)

    _,col_c,_ = st.columns([1,1.2,1])
    with col_c:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        m1,m2=st.columns(2)
        if m1.button("🔑 Login"):    st.session_state.auth_mode="login";    st.rerun()
        if m2.button("📝 Register"): st.session_state.auth_mode="register"; st.rerun()
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        if st.session_state.auth_mode=="login":
            st.markdown("<div style='font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;text-align:center;background:linear-gradient(90deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>Welcome Back 👋</div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;color:#6b5f8a;font-size:.85rem;margin-bottom:1rem;'>Login to your account</div>", unsafe_allow_html=True)
            email=st.text_input("📧 Email",placeholder="you@example.com",key="li_email")
            password=st.text_input("🔒 Password",placeholder="Your password",key="li_pass",type="password")
            if st.button("⚡ Login to My Account"):
                if not email or not password:
                    st.error("Please fill in all fields!")
                elif not FIREBASE_ENABLED:
                    st.session_state.logged_in=True
                    st.session_state.profile={"name":email.split("@")[0].title(),"email":email,"college":"Demo College","class_name":"Demo-A","streak":0,"total_sessions":0,"best_confidence":0}
                    st.session_state.user={"localId":"demo","idToken":"demo"}
                    st.toast("✅ Demo login! Connect Firebase for full features.",icon="🔥"); st.rerun()
                else:
                    with st.spinner("Logging in..."):
                        r=login_user(email,password)
                    if r["success"]:
                        st.session_state.logged_in=True; st.session_state.user=r["user"]
                        st.session_state.profile=r["profile"]; st.session_state.streak=r["profile"].get("streak",0)
                        import json as _j, base64 as _b
                        _saved = _j.dumps({"profile":r["profile"],"user":r["user"],"streak":r["profile"].get("streak",0)})
                        st.query_params["s"] = _b.b64encode(_saved.encode()).decode()
                        st.toast(f"✅ Welcome back, {r['profile'].get('name','!')}!",icon="🎉"); st.rerun()
                    else: st.error(r["error"])
            st.markdown("<div style='text-align:center;font-size:.82rem;color:#4a4060;margin-top:.8rem;'>No account? Click <strong style='color:#a78bfa;'>Register</strong> above!</div>", unsafe_allow_html=True)

        else:
            st.markdown("<div style='font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;text-align:center;background:linear-gradient(90deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>Create Account 🚀</div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;color:#6b5f8a;font-size:.85rem;margin-bottom:1rem;'>Join your class & compete!</div>", unsafe_allow_html=True)
            rn=st.text_input("👤 Full Name",placeholder="e.g. Vishnu Rajole",key="rg_name")
            re=st.text_input("📧 Email",placeholder="you@example.com",key="rg_email")
            rp=st.text_input("🔒 Password",placeholder="Min 6 characters",key="rg_pass",type="password")
            rp2=st.text_input("🔒 Confirm Password",placeholder="Repeat password",key="rg_pass2",type="password")
            rc=st.text_input("🏫 College Name",placeholder="e.g. VJTI Mumbai",key="rg_college")
            rcl=st.text_input("📚 Class / Section",placeholder="e.g. FY-CS-A",key="rg_class")
            st.markdown("<div style='font-size:.75rem;color:#6b5f8a;margin-bottom:.5rem;'>⚠️ Use the EXACT same college name & class as your classmates for the leaderboard to work!</div>", unsafe_allow_html=True)
            # Timezone selection
            import study_alarm
            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            rtz = study_alarm.render_timezone_selector("reg")
            if st.button("🎓 Create My Account"):
                if not all([rn,re,rp,rp2,rc,rcl]): st.error("Fill in ALL fields!")
                elif rp!=rp2: st.error("Passwords don't match!")
                elif len(rp)<6: st.error("Password needs 6+ characters!")
                elif not FIREBASE_ENABLED:
                    st.session_state.logged_in=True
                    st.session_state.profile={"name":rn,"email":re,"college":rc,"class_name":rcl,"timezone":rtz,"streak":0,"total_sessions":0,"best_confidence":0}
                    st.session_state.user={"localId":"demo","idToken":"demo"}
                    st.toast(f"✅ Welcome {rn}! (Demo Mode)",icon="🎉"); st.rerun()
                else:
                    with st.spinner("Creating account..."):
                        r=register_user(re,rp,rn,rc,rcl)
                    if r["success"]:
                        # Save timezone to profile
                        if "profile" in r: r["profile"]["timezone"] = rtz
                        st.success(f"🎉 Account created! Welcome {rn}!"); st.session_state.auth_mode="login"; st.rerun()
                    else: st.error(r["error"])
            st.markdown("<div style='text-align:center;font-size:.82rem;color:#4a4060;margin-top:.8rem;'>Have account? Click <strong style='color:#a78bfa;'>Login</strong> above!</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    fc1,fc2,fc3,fc4=st.columns(4)
    for col,emoji,title,desc in [(fc1,"🎯","AI Prediction","89% accuracy PASS/FAIL"),(fc2,"🏆","Class Leaderboard","Compete with classmates"),(fc3,"🤖","AI Coach","Chatbot + timetable"),(fc4,"📚","5 Subjects","Predict all at once")]:
        col.markdown(f"""<div class='stat-box' style='padding:1.5rem;'>
            <div style='font-size:2rem;'>{emoji}</div>
            <div style='font-family:Syne,sans-serif;font-size:.9rem;font-weight:700;color:#c4b5fd;margin:.5rem 0 .3rem;'>{title}</div>
            <div style='font-size:.78rem;color:#6b5f8a;'>{desc}</div>
        </div>""", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP (after login)
# ══════════════════════════════════════════════════════════════════════════════
profile=st.session_state.profile
uid=st.session_state.user.get("localId","") if st.session_state.user else ""
token=st.session_state.user.get("idToken","") if st.session_state.user else ""

with st.sidebar:
    st.markdown(f"""<div style='text-align:center;padding:1rem 0 .8rem;'>
        <div style='font-size:2.2rem;'>🎓</div>
        <div style='font-family:Syne,sans-serif;font-size:.95rem;font-weight:700;color:#a78bfa;'>STUDENT PREDICTOR</div>
        <div style='margin-top:.5rem;'>
            <span class='profile-chip'>👤 {profile.get("name","")}</span><br>
            <span class='profile-chip'>🏫 {profile.get("college","")}</span><br>
            <span class='profile-chip'>📚 {profile.get("class_name","")}</span>
        </div>
    </div><hr style='border-color:rgba(167,139,250,.15);margin-bottom:1rem;'>""", unsafe_allow_html=True)
    study_hours=st.slider("📚 Study Hours/Day",0.0,10.0,5.0,0.5)
    attendance=st.slider("🏫 Attendance (%)",30.0,100.0,75.0,1.0)
    prev_score=st.slider("📝 Previous Score",30.0,100.0,65.0,1.0)
    sleep_hours=st.slider("😴 Sleep Hours/Night",3.0,10.0,7.0,0.5)
    assignments=st.slider("✅ Assignments (out of 10)",0,10,7,1)
    subject=st.selectbox("📖 Subject",["Overall","Mathematics","Science","English","Computer Science","History"])
    predict_btn=st.button("⚡  PREDICT NOW")
    save_btn=st.button("💾  SAVE TO HISTORY")
    if st.button("🚪 Logout"):
        for k in defaults: st.session_state[k]=defaults[k]
        st.rerun()
    st.markdown("<hr style='border-color:rgba(167,139,250,.1);'><div style='font-size:.7rem;color:#4a4060;text-align:center;'>89% Accuracy · 500 Records</div>", unsafe_allow_html=True)

pred_result,confidence=predict(study_hours,attendance,prev_score,sleep_hours,assignments)
rs=risk_score(study_hours,attendance,prev_score,sleep_hours,assignments)
badges=get_badges(study_hours,attendance,prev_score,sleep_hours,assignments)

if save_btn:
    entry={"name":profile.get("name",""),"college":profile.get("college",""),"class_name":profile.get("class_name",""),
           "subject":subject,"study":study_hours,"attend":attendance,"prev":prev_score,"sleep":sleep_hours,
           "assign":assignments,"result":"PASS" if pred_result==1 else "FAIL","confidence":round(confidence,1),
           "time":datetime.datetime.now().strftime("%H:%M"),"date":str(datetime.date.today())}
    st.session_state.history.append(entry)
    st.session_state.streak+=1
    if FIREBASE_ENABLED and uid!="demo":
        save_prediction(uid,token,entry)
        update_streak(uid,token,st.session_state.streak)
    st.toast(f"✅ Saved! {'PASS 🎉' if pred_result==1 else 'FAIL ⚠️'}")

st.markdown(f"""<div style='padding:2rem 0 .5rem;'>
    <div class='hero-title'>Student Performance<br>Predictor</div>
    <div class='hero-sub'>Hey <strong style='color:#a78bfa'>{profile.get('name','')}</strong>! · {profile.get('college','')} · {profile.get('class_name','')} · v2.0
    {'<span style="color:#fbbf24;margin-left:.5rem;">⚠️ Demo Mode — Connect Firebase for cloud features</span>' if not FIREBASE_ENABLED else ''}</div>
</div>""", unsafe_allow_html=True)

dark_bg="#0f0c29"; pass_col="#a78bfa"; fail_col="#f472b6"
t1,t2,t3,t4,t5,t6,t7,t8=st.tabs(["🎯 Predictor","📚 Subjects","📈 Progress","🏆 Class Leaderboard","🤖 AI Coach","🔒 Focus Lock","👤 Profile","ℹ️ About"])

# ── TAB 1: PREDICTOR ──────────────────────────────────────────────────────────
with t1:
    L,R=st.columns([1.1,1],gap="large")
    with L:
        st.markdown("<div class='card'><div class='card-title'>📋 Input Summary</div>", unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        c1.markdown(f"<div class='stat-box'><div class='stat-val'>{study_hours}</div><div class='stat-lbl'>Study hrs</div></div>",unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-box'><div class='stat-val'>{attendance:.0f}%</div><div class='stat-lbl'>Attendance</div></div>",unsafe_allow_html=True)
        c3.markdown(f"<div class='stat-box'><div class='stat-val'>{prev_score:.0f}</div><div class='stat-lbl'>Prev Score</div></div>",unsafe_allow_html=True)
        d1,d2=st.columns(2)
        d1.markdown(f"<div class='stat-box' style='margin-top:.8rem'><div class='stat-val'>{sleep_hours}</div><div class='stat-lbl'>Sleep hrs</div></div>",unsafe_allow_html=True)
        d2.markdown(f"<div class='stat-box' style='margin-top:.8rem'><div class='stat-val'>{assignments}/10</div><div class='stat-lbl'>Assignments</div></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        if pred_result==1:
            st.markdown(f"""<div class='result-pass'><div style='font-size:3rem'>🏆</div>
                <div class='result-label result-label-pass'>PASS</div>
                <div class='result-conf'>Confidence: <strong>{confidence:.1f}%</strong> · {subject}</div>
                <div style='margin-top:.8rem;font-size:.88rem;color:#6ee7b7;'>Great job! Keep it up.</div></div>""",unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class='result-fail'><div style='font-size:3rem'>⚠️</div>
                <div class='result-label result-label-fail'>FAIL</div>
                <div class='result-conf'>Confidence: <strong>{confidence:.1f}%</strong> · {subject}</div>
                <div style='margin-top:.8rem;font-size:.88rem;color:#fca5a5;'>Improve attendance & study!</div></div>""",unsafe_allow_html=True)

        rc="#34d399" if rs<30 else "#fbbf24" if rs<60 else "#f87171"
        rl="Low Risk 🟢" if rs<30 else "Medium Risk 🟡" if rs<60 else "High Risk 🔴"
        st.markdown(f"""<div style='margin-top:1rem;'><div class='card-title'>🎯 Risk Meter</div>
        <div style='display:flex;justify-content:space-between;font-size:.8rem;color:#a09cc0;margin-bottom:.3rem;'><span>Safe</span><span>{rl}</span><span>Danger</span></div>
        <div style='background:rgba(255,255,255,.07);border-radius:999px;height:12px;overflow:hidden;'>
        <div style='width:{rs}%;background:linear-gradient(90deg,#34d399,{rc});border-radius:999px;height:100%;'></div></div>
        <div style='text-align:center;font-family:Syne,sans-serif;font-size:1.5rem;font-weight:700;color:{rc};margin-top:.4rem;'>{rs:.0f}% Risk</div></div>""",unsafe_allow_html=True)

        if badges:
            st.markdown("<div style='height:.6rem'></div><div class='card-title'>🏅 Badges</div>", unsafe_allow_html=True)
            st.markdown("".join([f"<span class='badge' style='background:{c};'>{n}</span>" for n,c in badges]),unsafe_allow_html=True)

        st.markdown("<div style='height:.8rem'></div><div class='card-title'>💡 Smart Tips</div>",unsafe_allow_html=True)
        for cond,cls,msg in [
            (study_hours<3,"tip-warn",f"📚 Critical: {study_hours}h/day. Need 4h minimum!"),
            (3<=study_hours<5,"tip-box","📚 Increase to 5–6 hrs/day for better results."),
            (study_hours>=5,"tip-good",f"📚 Great study time at {study_hours}h/day!"),
            (attendance<65,"tip-warn",f"🏫 Critical: {attendance:.0f}%. Risk of exam ban!"),
            (65<=attendance<80,"tip-box",f"🏫 {attendance:.0f}% attendance. Aim for 85%+."),
            (attendance>=80,"tip-good",f"🏫 Excellent attendance at {attendance:.0f}%!"),
            (assignments<6,"tip-warn",f"✅ Only {assignments}/10. Submit at least 8!"),
            (6<=assignments<8,"tip-box",f"✅ {assignments}/10 done. Target 9–10!"),
            (assignments>=8,"tip-good",f"✅ Outstanding! {assignments}/10 done."),
            (sleep_hours<6,"tip-warn",f"😴 Only {sleep_hours}h sleep. Hurts memory!"),
            (sleep_hours>=6,"tip-good",f"😴 Good sleep at {sleep_hours}h/night!"),
        ]:
            if cond: st.markdown(f"<div class='{cls}'>{msg}</div>",unsafe_allow_html=True)

        # 7-day plan
        st.markdown("<div style='height:.8rem'></div><div class='card-title'>🤖 7-Day Study Plan</div>",unsafe_allow_html=True)
        weak=[x for x,c in [("study",study_hours<5),("attendance",attendance<80),("assignments",assignments<8),("sleep",sleep_hours<7)] if c]
        plan=[("Mon","Identify weak topics + make checklist"),("Tue",f"Deep study: {'fix '+weak[0] if weak else 'core revision'} (3–4h)"),
              ("Wed","Submit all assignments"),("Thu","Practice tests + review mistakes"),
              ("Fri",f"{'Work on '+weak[1] if len(weak)>1 else 'Concept mapping'}"),
              ("Sat","Full mock exam (2h) + analyze"),("Sun","Light review + set goals 🎯")]
        pc=["#a78bfa","#60a5fa","#34d399","#fbbf24","#f472b6","#a78bfa","#60a5fa"]
        h="<div style='background:rgba(255,255,255,.03);border-radius:14px;padding:1rem;border:1px solid rgba(167,139,250,.1);'>"
        for i,(day,task) in enumerate(plan):
            c=pc[i]
            h+=f"""<div style='display:flex;align-items:flex-start;gap:.8rem;margin-bottom:.6rem;'>
                <div style='min-width:2.5rem;height:2rem;background:{c}22;border:1px solid {c}44;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700;color:{c};'>{day}</div>
                <div style='font-size:.83rem;color:#c4b5fd;padding-top:.3rem;'>{task}</div></div>"""
        h+="</div>"
        st.markdown(h,unsafe_allow_html=True)

    with R:
        st.markdown("<div class='card-title'>📊 Data Insights</div>",unsafe_allow_html=True)
        ch1,ch2,ch3=st.tabs(["Study Hours","Attendance","Feature Impact"])
        def mk_hist(dp,df_,uv,xl,title):
            fig,ax=plt.subplots(figsize=(6,3.5),facecolor=dark_bg); ax.set_facecolor(dark_bg)
            ax.hist(dp,bins=15,alpha=.75,color=pass_col,label="Pass",edgecolor="none")
            ax.hist(df_,bins=15,alpha=.75,color=fail_col,label="Fail",edgecolor="none")
            ax.axvline(uv,color="#fbbf24",linewidth=2,linestyle="--",label=f"You ({uv})")
            ax.set_xlabel(xl,color="#a09cc0",fontsize=9); ax.set_ylabel("Students",color="#a09cc0",fontsize=9)
            ax.tick_params(colors="#6b5f8a",labelsize=8)
            for s in ax.spines.values(): s.set_edgecolor("#1a1040")
            ax.legend(facecolor="#1a1040",edgecolor="none",labelcolor="#c4b5fd",fontsize=8)
            ax.set_title(title,color="#c4b5fd",fontsize=10,pad=8); plt.tight_layout(); st.pyplot(fig); plt.close()
        with ch1: mk_hist(df[df["result"]==1]["study_hours"],df[df["result"]==0]["study_hours"],study_hours,"Study hrs/day","Study Hours")
        with ch2: mk_hist(df[df["result"]==1]["attendance_pct"],df[df["result"]==0]["attendance_pct"],attendance,"Attendance (%)","Attendance")
        with ch3:
            fig,ax=plt.subplots(figsize=(6,3.5),facecolor=dark_bg); ax.set_facecolor(dark_bg)
            feats=["Study Hrs","Attendance","Prev Score","Sleep","Assignments"]
            coefs=np.abs(model.coef_[0]); cn=coefs/coefs.sum()*100
            bars=ax.barh(feats,cn,color=["#a78bfa","#60a5fa","#34d399","#fbbf24","#f472b6"],edgecolor="none",height=.55)
            for bar,val in zip(bars,cn): ax.text(val+.5,bar.get_y()+bar.get_height()/2,f"{val:.1f}%",va="center",color="#c4b5fd",fontsize=8)
            ax.set_xlabel("Importance (%)",color="#a09cc0",fontsize=9); ax.tick_params(colors="#a09cc0",labelsize=8)
            for s in ax.spines.values(): s.set_edgecolor("#1a1040")
            ax.set_title("Feature Importance",color="#c4b5fd",fontsize=10,pad=8); ax.set_xlim(0,max(cn)*1.2)
            plt.tight_layout(); st.pyplot(fig); plt.close()

        st.markdown("<div style='height:.5rem'></div><div class='card-title'>🔍 Why This Prediction?</div>",unsafe_allow_html=True)
        uvs=[study_hours,attendance,prev_score,sleep_hours,assignments]
        avs=[df["study_hours"].mean(),df["attendance_pct"].mean(),df["previous_score"].mean(),df["sleep_hours"].mean(),df["assignments_done"].mean()]
        impacts=[(uvs[i]-avs[i])*model.coef_[0][i] for i in range(5)]
        expl="<div style='background:rgba(255,255,255,.03);border-radius:14px;padding:1rem;border:1px solid rgba(167,139,250,.1);'>"
        for feat,imp in zip(["Study Hrs","Attendance","Prev Score","Sleep","Assignments"],impacts):
            ic="#34d399" if imp>0 else "#f87171"; il=f"+{imp:.2f} ✅" if imp>0 else f"{imp:.2f} ❌"
            bw=min(abs(imp)*8,100)
            expl+=f"""<div style='margin-bottom:.7rem;'>
                <div style='display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:.2rem;'>
                    <span style='color:#c4b5fd;'>{feat}</span><span style='color:{ic};font-weight:600;'>{il}</span></div>
                <div style='background:rgba(255,255,255,.06);border-radius:999px;height:6px;'>
                    <div style='width:{bw}%;background:{ic};border-radius:999px;height:100%;'></div></div></div>"""
        expl+="</div>"
        st.markdown(expl,unsafe_allow_html=True)
        mc1,mc2,mc3=st.columns(3)
        mc1.markdown("<div class='stat-box'><div class='stat-val'>89%</div><div class='stat-lbl'>Accuracy</div></div>",unsafe_allow_html=True)
        mc2.markdown("<div class='stat-box'><div class='stat-val'>500</div><div class='stat-lbl'>Records</div></div>",unsafe_allow_html=True)
        mc3.markdown("<div class='stat-box'><div class='stat-val'>5</div><div class='stat-lbl'>Features</div></div>",unsafe_allow_html=True)

# ── TAB 2: SUBJECTS ───────────────────────────────────────────────────────────
with t2:
    st.markdown("<div class='card-title'>📚 Multi-Subject Prediction</div>",unsafe_allow_html=True)
    sw={"Mathematics":[1.4,1.0,1.3,.8,1.2],"Science":[1.2,1.1,1.2,1.0,1.1],
        "English":[.9,1.2,1.0,1.1,1.0],"Computer Science":[1.3,1.0,1.1,.9,1.3],"History":[1.0,1.1,1.0,1.0,1.0]}
    ui=np.array([study_hours,attendance,prev_score,sleep_hours,assignments])
    cols5=st.columns(5); sn,sp=[],[]
    for i,(subj,w) in enumerate(sw.items()):
        mod=np.clip(ui*np.array(w),[0,30,30,3,0],[10,100,100,10,10])
        p,c=predict(*mod); pp=model.predict_proba(scaler.transform(mod.reshape(1,-1)))[0][1]*100
        sn.append(subj); sp.append(pp); color="#34d399" if p==1 else "#f87171"
        with cols5[i]:
            st.markdown(f"""<div class='subject-card'>
                <div style='font-size:1.5rem;'>{"✅" if p==1 else "❌"}</div>
                <div style='font-family:Syne,sans-serif;font-size:.82rem;font-weight:700;color:#c4b5fd;margin:.4rem 0;'>{subj}</div>
                <div style='font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;color:{color};'>{"PASS" if p==1 else "FAIL"}</div>
                <div style='font-size:.75rem;color:#7c6fa0;'>{c:.0f}% conf</div></div>""",unsafe_allow_html=True)
    fig,ax=plt.subplots(figsize=(10,3.5),facecolor=dark_bg); ax.set_facecolor(dark_bg)
    bars=ax.bar(sn,sp,color=["#34d399" if p>=50 else "#f87171" for p in sp],edgecolor="none",width=.5)
    ax.axhline(50,color="#fbbf24",linewidth=1.5,linestyle="--",alpha=.7,label="Pass (50%)")
    for bar,val in zip(bars,sp): ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1.5,f"{val:.0f}%",ha="center",color="#c4b5fd",fontsize=9)
    ax.set_ylabel("Pass Probability (%)",color="#a09cc0",fontsize=9); ax.set_ylim(0,115); ax.tick_params(colors="#a09cc0",labelsize=9)
    for s in ax.spines.values(): s.set_edgecolor("#1a1040")
    ax.legend(facecolor="#1a1040",edgecolor="none",labelcolor="#c4b5fd",fontsize=8)
    ax.set_title("Pass Probability by Subject",color="#c4b5fd",fontsize=11,pad=10)
    plt.tight_layout(); st.pyplot(fig); plt.close()

# ── TAB 3: PROGRESS ───────────────────────────────────────────────────────────
with t3:
    st.markdown("<div class='card-title'>📈 Progress Tracker</div>",unsafe_allow_html=True)
    if not st.session_state.history:
        st.markdown("<div style='text-align:center;padding:3rem;'><div style='font-size:3rem;'>📭</div><div style='color:#6b5f8a;margin-top:.5rem;'>No history yet! Adjust sliders → click 💾 Save</div></div>",unsafe_allow_html=True)
    else:
        total=len(st.session_state.history); passes=sum(1 for h in st.session_state.history if h["result"]=="PASS")
        avg_c=sum(h["confidence"] for h in st.session_state.history)/total
        sc1,sc2,sc3,sc4=st.columns(4)
        sc1.markdown(f"<div class='stat-box'><div class='stat-val'>{total}</div><div class='stat-lbl'>Sessions</div></div>",unsafe_allow_html=True)
        sc2.markdown(f"<div class='stat-box'><div class='stat-val'>{passes}</div><div class='stat-lbl'>PASSes</div></div>",unsafe_allow_html=True)
        sc3.markdown(f"<div class='stat-box'><div class='stat-val'>{total-passes}</div><div class='stat-lbl'>FAILs</div></div>",unsafe_allow_html=True)
        sc4.markdown(f"<div class='stat-box'><div class='stat-val'>{avg_c:.0f}%</div><div class='stat-lbl'>Avg Conf</div></div>",unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
        for h in reversed(st.session_state.history):
            rc2="#34d399" if h["result"]=="PASS" else "#f87171"
            st.markdown(f"""<div style='background:rgba(255,255,255,.03);border:1px solid rgba(167,139,250,.1);border-radius:12px;
                padding:.8rem 1.2rem;margin-bottom:.6rem;display:flex;justify-content:space-between;align-items:center;'>
                <div><span style='font-weight:600;color:#c4b5fd;'>{h.get("name","")}</span>
                <span style='font-size:.78rem;color:#6b5f8a;'> · {h['subject']} · {h['time']}</span></div>
                <div style='display:flex;gap:1rem;align-items:center;'>
                    <span style='color:#a09cc0;font-size:.82rem;'>📚{h['study']}h 🏫{h['attend']:.0f}% 📝{h['prev']:.0f}</span>
                    <span style='font-family:Syne,sans-serif;font-weight:700;color:{rc2};'>{h['result']} ({h['confidence']}%)</span>
                </div></div>""",unsafe_allow_html=True)
        if st.button("🗑️ Clear History"): st.session_state.history=[]; st.rerun()

# ── TAB 4: CLASS LEADERBOARD ─────────────────────────────────────────────────
with t4:
    uc=profile.get("college",""); ucl=profile.get("class_name",""); un=profile.get("name","")
    st.markdown(f"""<div class='card-title'>🏆 Class Leaderboard</div>
    <div style='margin-bottom:1rem;'><span class='profile-chip'>🏫 {uc}</span><span class='profile-chip'>📚 {ucl}</span></div>""",unsafe_allow_html=True)

    if FIREBASE_ENABLED and uid!="demo":
        with st.spinner("Loading classmates..."): lb_data=get_class_leaderboard(uc,ucl)
    else:
        lb_data=[
            {"name":"Alex",  "best_confidence":92.0,"total_sessions":15,"streak":7},
            {"name":"Priya", "best_confidence":88.0,"total_sessions":12,"streak":5},
            {"name":"Rahul", "best_confidence":81.0,"total_sessions":10,"streak":4},
            {"name":"Emma",  "best_confidence":74.0,"total_sessions":8, "streak":3},
            {"name":un,      "best_confidence":round(confidence,1),"total_sessions":len(st.session_state.history),"streak":st.session_state.streak},
        ]
        lb_data.sort(key=lambda x:x["best_confidence"],reverse=True)

    if not lb_data:
        st.markdown("<div style='text-align:center;padding:2rem;color:#4a4060;'><div style='font-size:2rem;'>👥</div><div style='margin-top:.5rem;'>No classmates yet! Share the app with your class!</div></div>",unsafe_allow_html=True)
    else:
        lb1,lb2,lb3=st.columns(3)
        lb1.markdown(f"<div class='stat-box'><div class='stat-val'>{len(lb_data)}</div><div class='stat-lbl'>Classmates</div></div>",unsafe_allow_html=True)
        lb2.markdown(f"<div class='stat-box'><div class='stat-val'>{max(r['best_confidence'] for r in lb_data):.0f}%</div><div class='stat-lbl'>Top Score</div></div>",unsafe_allow_html=True)
        lb3.markdown(f"<div class='stat-box'><div class='stat-val'>{sum(1 for r in lb_data if r['best_confidence']>=50)}/{len(lb_data)}</div><div class='stat-lbl'>Predicted PASS</div></div>",unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
        medals=["🥇","🥈","🥉"]+["⭐"]*50
        for rank,row in enumerate(lb_data):
            is_you=row["name"]==un
            bg="rgba(167,139,250,.12)" if is_you else "rgba(255,255,255,.03)"
            bd="rgba(167,139,250,.5)" if is_you else "rgba(167,139,250,.1)"
            cc="#34d399" if row["best_confidence"]>=70 else "#fbbf24" if row["best_confidence"]>=50 else "#f87171"
            st.markdown(f"""<div style='background:{bg};border:1px solid {bd};border-radius:14px;padding:1rem 1.4rem;margin-bottom:.6rem;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div style='display:flex;align-items:center;gap:1rem;'>
                        <div style='font-size:1.5rem;'>{medals[rank]}</div>
                        <div>
                            <div style='font-family:Syne,sans-serif;font-weight:700;color:{"#a78bfa" if is_you else "#c4b5fd"};'>{row["name"]} {"← You" if is_you else ""}</div>
                            <div style='font-size:.75rem;color:#6b5f8a;'>🎯 {row["total_sessions"]} sessions · 🔥 {row["streak"]} streak</div>
                        </div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='font-family:Syne,sans-serif;font-weight:800;color:{cc};font-size:1.2rem;'>{row["best_confidence"]:.0f}%</div>
                        <div style='font-size:.75rem;color:{cc};'>{"PASS" if row["best_confidence"]>=50 else "FAIL"}</div>
                    </div>
                </div>
                <div style='margin-top:.6rem;background:rgba(255,255,255,.06);border-radius:999px;height:6px;'>
                    <div style='width:{row["best_confidence"]}%;background:linear-gradient(90deg,#7c3aed,{cc});border-radius:999px;height:100%;'></div>
                </div></div>""",unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;font-size:.8rem;color:#4a4060;margin-top:.5rem;'>💡 Ranked by best confidence score · Invite classmates to join!</div>",unsafe_allow_html=True)

# ── TAB 5: AI COACH (Claude AI Powered) ──────────────────────────────────────
with t5:
    from ai_coach import render_ai_chatbot
    render_ai_chatbot(profile, study_hours, attendance, prev_score, sleep_hours, assignments, confidence, pred_result)

# ── TAB 6: FOCUS LOCK ────────────────────────────────────────────────────────
with t6:
    import study_alarm
    study_alarm.render_study_alarm_manager(profile, st.session_state.exams)

# ── TAB 7: PROFILE ────────────────────────────────────────────────────────────
with t7:
    pr1,pr2=st.columns([1,1.5])
    with pr1:
        st.markdown(f"""<div style='text-align:center;background:rgba(255,255,255,.04);border:1px solid rgba(167,139,250,.2);border-radius:20px;padding:2rem;'>
            <div style='font-size:4rem;'>👤</div>
            <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#a78bfa;margin-top:.5rem;'>{profile.get('name','')}</div>
            <div style='font-size:.85rem;color:#6b5f8a;'>{profile.get('email','')}</div>
            <div style='margin-top:1rem;'>
                <span class='profile-chip'>🏫 {profile.get('college','')}</span><br>
                <span class='profile-chip' style='margin-top:.5rem;display:inline-block;'>📚 {profile.get('class_name','')}</span>
            </div>
            <div style='margin-top:1rem;font-size:.78rem;color:#4a4060;'>{'🔥 Firebase Connected' if FIREBASE_ENABLED else '⚠️ Demo Mode'}</div>
        </div>""",unsafe_allow_html=True)
    with pr2:
        st.markdown("<div class='card-title'>📊 My Stats</div>",unsafe_allow_html=True)
        ps1,ps2=st.columns(2)
        ps1.markdown(f"<div class='stat-box'><div class='stat-val'>{len(st.session_state.history)}</div><div class='stat-lbl'>Sessions</div></div>",unsafe_allow_html=True)
        ps2.markdown(f"<div class='stat-box'><div class='stat-val'>{st.session_state.streak}🔥</div><div class='stat-lbl'>Streak</div></div>",unsafe_allow_html=True)
        ps3,ps4=st.columns(2)
        best=max([h["confidence"] for h in st.session_state.history],default=0)
        ps3.markdown(f"<div class='stat-box' style='margin-top:.8rem'><div class='stat-val'>{best:.0f}%</div><div class='stat-lbl'>Best Score</div></div>",unsafe_allow_html=True)
        ps4.markdown(f"<div class='stat-box' style='margin-top:.8rem'><div class='stat-val'>{st.session_state.pomodoro_count}</div><div class='stat-lbl'>Pomodoros</div></div>",unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div><div class='card-title'>🏅 Earned Badges</div>",unsafe_allow_html=True)
        if badges:
            st.markdown("".join([f"<span class='badge' style='background:{c};'>{n}</span>" for n,c in badges]),unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#4a4060;font-size:.85rem;'>Adjust sliders to earn badges!</div>",unsafe_allow_html=True)

# ── TAB 8: ABOUT ──────────────────────────────────────────────────────────────
with t8:
    a1,a2=st.columns(2)
    with a1:
        st.markdown("<div class='card-title'>🚀 About</div>",unsafe_allow_html=True)
        st.markdown("""<div style='color:#c4b5fd;font-size:.9rem;line-height:1.8;'>
        <strong style='color:#a78bfa;'>Student Performance Predictor v2.0</strong><br>
        Full-stack ML web app with auth, cloud DB, and AI coaching.<br><br>
        ✅ Login/Register · Firebase Auth + Firestore<br>
        ✅ College + Class Leaderboard<br>
        ✅ Multi-subject prediction<br>
        ✅ AI chatbot coach<br>
        ✅ Exam timetable + Pomodoro<br>
        ✅ Progress tracking + Badges</div>""",unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div><div class='card-title'>🛠️ Tech Stack</div>",unsafe_allow_html=True)
        for tn,td in [("🐍 Python","Core"),("📊 scikit-learn","ML model"),("🌊 Streamlit","UI framework"),("🔥 Firebase","Auth + Database"),("🐼 Pandas","Data processing"),("📈 Matplotlib","Charts")]:
            st.markdown(f"<div class='tip-good'><strong>{tn}</strong> — {td}</div>",unsafe_allow_html=True)
    with a2:
        st.markdown("<div class='card-title'>🔮 Future Roadmap</div>",unsafe_allow_html=True)
        for f in ["🤖 Claude AI powered coaching","📱 Mobile app","📊 XGBoost (95%+ accuracy)","📧 Email/Push notifications","🌐 Multi-language","👨‍🏫 Teacher dashboard"]:
            st.markdown(f"<div style='color:#c4b5fd;font-size:.85rem;padding:.3rem 0;'>{f}</div>",unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div><div class='card-title'>⚠️ Limitations</div>",unsafe_allow_html=True)
        st.markdown("<div style='color:#a09cc0;font-size:.83rem;line-height:1.8;'>• Synthetic training data<br>• Binary prediction only<br>• Firebase setup required for cloud features<br>• No real push notifications yet</div>",unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div><div class='card-title'>🔥 Streamlit Cloud Setup</div>",unsafe_allow_html=True)
        st.markdown("""<div style='color:#c4b5fd;font-size:.82rem;line-height:1.9;'>
        1. Add secrets to Streamlit Cloud settings<br>
        2. Create <strong>firebase</strong> secret with service account JSON<br>
        3. Upload to <strong>streamlit/secrets.toml</strong><br>
        4. App will auto-initialize Firebase from secrets</div>""",unsafe_allow_html=True)

st.markdown("<div style='text-align:center;padding:2rem 0 1rem;color:#3d3560;font-size:.78rem;'>Student Performance Predictor v2.0 🎓 · Streamlit · Firebase · scikit-learn</div>",unsafe_allow_html=True)
