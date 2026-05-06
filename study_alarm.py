import streamlit as st
import datetime
import json
import os
from zoneinfo import ZoneInfo

ALARM_FILE = "alarms_data.json"

# ── Timezone options ──────────────────────────────────────────────────────────
TIMEZONE_OPTIONS = {
    "🇮🇳 India": ["Asia/Kolkata"],
    "🇺🇸 United States": ["America/New_York","America/Chicago","America/Denver","America/Los_Angeles"],
    "🇬🇧 United Kingdom": ["Europe/London"],
    "🇪🇺 Europe": ["Europe/Paris","Europe/Berlin","Europe/Rome","Europe/Madrid","Europe/Moscow"],
    "🇦🇺 Australia": ["Australia/Sydney","Australia/Melbourne","Australia/Brisbane","Australia/Perth"],
    "🇯🇵 Japan / Korea": ["Asia/Tokyo","Asia/Seoul"],
    "🇨🇳 China": ["Asia/Shanghai"],
    "🇸🇬 Singapore": ["Asia/Singapore","Asia/Kuala_Lumpur"],
    "🇦🇪 UAE / Gulf": ["Asia/Dubai","Asia/Riyadh"],
    "🇧🇷 Brazil": ["America/Sao_Paulo"],
    "🌏 Other Asia": ["Asia/Bangkok","Asia/Jakarta","Asia/Karachi","Asia/Dhaka","Asia/Colombo","Asia/Kathmandu","Asia/Manila","Asia/Ho_Chi_Minh"],
    "🌎 Latin America": ["America/Mexico_City","America/Bogota","America/Lima","America/Buenos_Aires"],
    "🌍 Africa": ["Africa/Cairo","Africa/Lagos","Africa/Nairobi","Africa/Johannesburg"],
    "🌐 UTC": ["UTC"],
}

def save_alarms(alarms):
    """Save alarms to disk so they survive page reloads."""
    try:
        with open(ALARM_FILE, "w") as f:
            json.dump(alarms, f)
    except:
        pass

def load_alarms():
    """Load alarms from disk."""
    try:
        if os.path.exists(ALARM_FILE):
            with open(ALARM_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return []

def get_user_now(tz_str):
    try:
        return datetime.datetime.now(ZoneInfo(tz_str))
    except:
        return datetime.datetime.now(ZoneInfo("UTC"))

def render_timezone_selector(key_prefix="reg"):
    st.markdown("<div style='font-size:.75rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:.3rem;'>🌍 YOUR TIMEZONE</div>", unsafe_allow_html=True)
    region_options = list(TIMEZONE_OPTIONS.keys())
    sel_region = st.selectbox("🌏 Region / Country", region_options, index=0, key=f"{key_prefix}_region")
    tz_list = TIMEZONE_OPTIONS[sel_region]
    tz_labels = []
    for tz in tz_list:
        try:
            now = datetime.datetime.now(ZoneInfo(tz))
            offset = now.strftime("%z")
            label = f"{tz.split('/')[-1].replace('_',' ')} — UTC{offset[:3]}:{offset[3:]}"
            tz_labels.append((label, tz))
        except:
            tz_labels.append((tz, tz))
    sel_label = st.selectbox("⏰ Timezone", [l for l,_ in tz_labels], key=f"{key_prefix}_tz")
    sel_tz = next((tz for l,tz in tz_labels if l == sel_label), "UTC")
    now_local = get_user_now(sel_tz)
    st.markdown(f"<div style='font-size:.8rem;color:#34d399;margin-top:.3rem;'>🕐 Current time: <strong>{now_local.strftime('%d %b %Y, %I:%M:%S %p')}</strong></div>", unsafe_allow_html=True)
    return sel_tz

DAYS_OF_WEEK = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# ── Sound definitions (JS, no external files needed) ─────────────────────────
SOUNDS = {
    "🔔 Gentle Bell":      "gentle_bell",
    "🚨 Urgent Alarm":     "urgent_alarm",
    "🧘 Meditation Bowl":  "meditation_bowl",
    "🌊 Ocean Wave":       "ocean_wave",
    "☯️ OM Chant":         "om_chant",
    "🎵 Focus Tone":       "focus_tone",
    "⚡ Energy Boost":     "energy_boost",
    "🌸 Soft Chime":       "soft_chime",
    "🔕 Silent":           "silent",
}

def render_study_alarm_manager(profile, exams):
    if "focus_mode"      not in st.session_state: st.session_state.focus_mode     = False
    if "focus_subject"   not in st.session_state: st.session_state.focus_subject  = ""
    if "focus_duration"  not in st.session_state: st.session_state.focus_duration = 25
    if "focus_start"     not in st.session_state: st.session_state.focus_start    = None
    if "focus_sound_key" not in st.session_state: st.session_state.focus_sound_key= "gentle_bell"

    # Always load alarms from disk — survives reloads
    alarms = load_alarms()

    name   = profile.get("name", "Student")
    tz_str = profile.get("timezone", "Asia/Kolkata")
    now_local = get_user_now(tz_str)

    # ── FOCUS LOCK MODE ───────────────────────────────────────────────────────
    if st.session_state.focus_mode:
        subject    = st.session_state.focus_subject
        duration   = st.session_state.focus_duration
        start      = st.session_state.focus_start
        total_secs = duration * 60
        start_ms   = int(start.timestamp() * 1000) if start else 0

        quotes = [
            "Every minute you study now is one less minute of stress later.",
            f"Your future self is watching you right now {name}. Make them proud.",
            "Champions are made in moments like this when no one is watching.",
            "The phone can wait. Your dreams cannot.",
            "Discipline is choosing what you want most over what you want now.",
            "Success is the sum of small efforts repeated day after day.",
            "Push yourself. No one else is going to do it for you.",
            "The pain of discipline is less than the pain of regret.",
        ]
        quotes_json = json.dumps(quotes)

        particles = "".join([
            f'<div style="position:absolute;width:{8+i*4}px;height:{8+i*4}px;left:{3+i*10}%;'
            f'background:rgba(167,139,250,0.1);border-radius:50%;'
            f'animation:floatUp {10+i*3}s linear {i*0.8}s infinite;"></div>'
            for i in range(8)
        ])

        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{background:transparent;overflow:hidden;}}
  @keyframes floatUp{{0%{{transform:translateY(110vh) scale(0);opacity:0;}}10%{{opacity:0.35;}}90%{{opacity:0.15;}}100%{{transform:translateY(-10vh) scale(1);opacity:0;}}}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.45}}}}
  @keyframes celebPop{{0%{{transform:scale(0.5);opacity:0;}}70%{{transform:scale(1.1);}}100%{{transform:scale(1);opacity:1;}}}}
  #fo{{width:100%;height:580px;background:linear-gradient(135deg,#0a0820 0%,#0f0c29 40%,#150d35 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Syne',sans-serif;position:relative;overflow:hidden;border-radius:16px;}}
  #label{{font-size:.78rem;font-weight:600;color:#6b5f8a;letter-spacing:.2em;text-transform:uppercase;margin-bottom:.5rem;z-index:1;}}
  #uname{{font-size:.9rem;color:#a78bfa;font-weight:600;margin-bottom:.2rem;z-index:1;}}
  #clock{{font-size:.75rem;color:#4a4060;margin-bottom:.3rem;z-index:1;}}
  #subj{{font-size:2.5rem;font-weight:800;background:linear-gradient(90deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;text-align:center;z-index:1;padding:0 20px;margin-bottom:.4rem;}}
  #timer{{font-size:5.5rem;font-weight:800;color:#e8e0ff;letter-spacing:.06em;line-height:1;margin:.7rem 0;font-variant-numeric:tabular-nums;z-index:1;transition:color .3s;}}
  .timer-urgent{{color:#f87171!important;animation:pulse 1s infinite;}}
  #progbg{{width:340px;height:8px;background:rgba(255,255,255,.08);border-radius:999px;margin:.4rem 0;overflow:hidden;z-index:1;}}
  #progfill{{height:100%;width:0%;background:linear-gradient(90deg,#7c3aed,#a78bfa);border-radius:999px;}}
  #stats{{color:#a09cc0;font-size:.8rem;margin:.3rem 0;z-index:1;}}
  #quote{{font-size:.85rem;color:#6b5f8a;text-align:center;max-width:400px;line-height:1.6;margin:.8rem 20px;font-style:italic;font-family:'DM Sans',sans-serif;z-index:1;min-height:2.8rem;}}
  #urgent-msg{{color:#f87171;font-size:.95rem;font-weight:700;animation:pulse 1s infinite;margin-top:.3rem;z-index:1;display:none;}}
  #complete{{display:none;flex-direction:column;align-items:center;justify-content:center;width:100%;height:100%;z-index:2;}}
  #complete-icon{{font-size:4rem;animation:celebPop .6s ease both;}}
  #complete-title{{font-size:2.3rem;font-weight:800;background:linear-gradient(90deg,#34d399,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;text-align:center;margin:.4rem 0;}}
  #complete-sub{{color:#6ee7b7;font-size:.95rem;text-align:center;}}
  #complete-name{{color:#a78bfa;font-weight:700;font-size:.9rem;margin-top:.4rem;}}
</style></head><body>
<div id="fo">
  {particles}
  <div id="active-view" style="display:flex;flex-direction:column;align-items:center;z-index:1;width:100%;">
    <div id="label">🎯 FOCUS MODE ACTIVE</div>
    <div id="uname">👤 {name}</div>
    <div id="clock">🕐 Loading...</div>
    <div id="subj">{subject}</div>
    <div id="timer">--:--</div>
    <div id="progbg"><div id="progfill"></div></div>
    <div id="stats">Starting...</div>
    <div id="quote"></div>
    <div id="urgent-msg">⚠️ Last minute — push through!</div>
  </div>
  <div id="complete">
    <div id="complete-icon">🏆</div>
    <div id="complete-title">Session Complete!</div>
    <div id="complete-sub">You studied {duration} minutes of {subject} 🎉</div>
    <div id="complete-name">Amazing work, {name}! Take a 5-min break ☕</div>
  </div>
</div>
<script>
const START_MS={start_ms},TOTAL_SECS={total_secs},TZ="{tz_str}",QUOTES={quotes_json};
let alarmPlayed=false,completeDone=false;
function playUrgent(){{try{{var c=new(AudioContext||webkitAudioContext);[880,990,880,990].forEach(function(f,i){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0.25,c.currentTime+i*0.35);g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+i*0.35+0.28);o.start(c.currentTime+i*0.35);o.stop(c.currentTime+i*0.35+0.3);}})}}catch(e){{}}}}
function playComplete(){{try{{var c=new(AudioContext||webkitAudioContext);[523,659,784,1047,1319].forEach(function(f,i){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0.2,c.currentTime+i*0.12);g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+i*0.12+0.5);o.start(c.currentTime+i*0.12);o.stop(c.currentTime+i*0.12+0.5);}})}}catch(e){{}}}}
function getLocalTime(){{try{{return new Date().toLocaleString("en-IN",{{timeZone:TZ,weekday:"short",day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit",second:"2-digit"}})}}catch(e){{return new Date().toLocaleString()}}}}
function tick(){{
  var now=Date.now(),elapsed=Math.floor((now-START_MS)/1000),remaining=Math.max(0,TOTAL_SECS-elapsed);
  var mins=Math.floor(remaining/60),secs=remaining%60,pct=Math.min(100,(elapsed/TOTAL_SECS)*100);
  var qIdx=Math.min(Math.floor(elapsed/300),QUOTES.length-1);
  document.getElementById('timer').textContent=String(mins).padStart(2,'0')+':'+String(secs).padStart(2,'0');
  document.getElementById('progfill').style.width=pct.toFixed(2)+'%';
  document.getElementById('stats').textContent=Math.floor(elapsed/60)+' min studied · '+mins+' min remaining';
  document.getElementById('quote').textContent='"'+QUOTES[qIdx]+'"';
  document.getElementById('clock').textContent='🕐 '+getLocalTime();
  if(remaining<=60&&remaining>0){{document.getElementById('timer').classList.add('timer-urgent');document.getElementById('urgent-msg').style.display='block';if(!alarmPlayed){{alarmPlayed=true;playUrgent();}}}}
  if(remaining===0&&!completeDone){{completeDone=true;playComplete();document.getElementById('active-view').style.display='none';document.getElementById('complete').style.display='flex';}}
}}
tick();setInterval(tick,1000);
</script></body></html>"""

        st.components.v1.html(html, height=595, scrolling=False)
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"<div style='color:#34d399;font-size:.8rem;padding:.5rem;'>🟢 Timer ticking · {tz_str}</div>", unsafe_allow_html=True)
        with col2:
            if st.button("🚪 Exit Focus", use_container_width=True):
                st.session_state.focus_mode  = False
                st.session_state.focus_start = None
                st.rerun()
        return

    # ── NORMAL MODE ───────────────────────────────────────────────────────────
    st.markdown("<div class='card-title'>🔒 Study Alarm & Focus Lock</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#a09cc0;font-size:.82rem;margin-bottom:.8rem;'>🕐 Your time: <strong style='color:#34d399;'>{now_local.strftime('%d %b %Y, %I:%M %p')}</strong> &nbsp;·&nbsp; 🌍 {tz_str.split('/')[-1].replace('_',' ')}</div>", unsafe_allow_html=True)

    # ── Instant Focus Mode ─────────────────────────────────────────────────
    st.markdown("<div class='card-title'>⚡ Start Focus Mode Instantly</div>", unsafe_allow_html=True)
    fc1, fc2 = st.columns([3,1])
    with fc1:
        focus_subj = st.text_input("📚 What are you studying?", placeholder="e.g. Binomial Theorem, DBMS", key="focus_subj_input")
    with fc2:
        focus_dur  = st.selectbox("⏱️ Duration", [5,10,15,20,25,30,45,60,90,120], index=4, key="focus_dur_sel", format_func=lambda x: f"{x} min")
    fc3, fc4 = st.columns([3,1])
    with fc3:
        focus_sound_label = st.selectbox("🔔 Sound", list(SOUNDS.keys()), index=0, key="focus_sound_sel")
    with fc4:
        st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        if st.button("🔒 Enter Focus Mode", use_container_width=True):
            if focus_subj:
                st.session_state.focus_mode      = True
                st.session_state.focus_subject   = focus_subj
                st.session_state.focus_duration  = focus_dur
                st.session_state.focus_start     = datetime.datetime.now()
                st.session_state.focus_sound_key = SOUNDS[focus_sound_label]
                st.rerun()
            else:
                st.error("Enter what you're studying!")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Schedule Alarms ────────────────────────────────────────────────────
    st.markdown("<div class='card-title'>📅 Schedule Study Alarms</div>", unsafe_allow_html=True)
    with st.expander("➕ Add New Alarm", expanded=len(alarms)==0):
        a1,a2 = st.columns([2,1])
        with a1: alarm_subj = st.text_input("📚 Subject", placeholder="e.g. Mathematics", key="al_subj")
        with a2: alarm_sound_label = st.selectbox("🔔 Sound", list(SOUNDS.keys()), index=2, key="al_sound")
        a3,a4,a5 = st.columns([1,1,1])
        with a3: alarm_date = st.date_input("📅 Date", value=now_local.date(), min_value=now_local.date(), key="al_date")
        with a4: alarm_hour = st.selectbox("⏰ Hour", list(range(24)), index=now_local.hour, format_func=lambda h: f"{h:02d}:00", key="al_hour")
        with a5: alarm_min  = st.selectbox("🕐 Minute", list(range(60)), index=0, format_func=lambda m: f":{m:02d}", key="al_min")
        alarm_dur = st.select_slider("⏱️ Duration (minutes)", options=list(range(5,125,5)), value=25, key="al_dur")
        st.markdown("<div style='font-size:.8rem;color:#a78bfa;margin:.4rem 0 .2rem;font-weight:600;'>🔁 Repeat</div>", unsafe_allow_html=True)
        repeat_type = st.radio("", ["Once","Daily","Select days"], horizontal=True, key="al_repeat", label_visibility="collapsed")
        selected_days = []
        if repeat_type == "Select days":
            day_cols = st.columns(7)
            for idx, day in enumerate(DAYS_OF_WEEK):
                with day_cols[idx]:
                    if st.checkbox(day[:3], key=f"day_{idx}"): selected_days.append(day)

        if st.button("✅ Set Alarm", use_container_width=True):
            if alarm_subj:
                repeat_str = repeat_type if repeat_type != "Select days" else (", ".join(selected_days) if selected_days else "Once")
                new_alarm = {
                    "subject":     alarm_subj,
                    "date":        str(alarm_date),
                    "hour":        alarm_hour,
                    "minute":      alarm_min,
                    "duration":    alarm_dur,
                    "repeat":      repeat_str,
                    "sound_key":   SOUNDS[alarm_sound_label],
                    "sound_label": alarm_sound_label,
                    "timezone":    tz_str,
                    "id":          len(alarms)
                }
                alarms.append(new_alarm)
                save_alarms(alarms)   # ← Save to disk immediately
                st.toast(f"✅ Alarm set for {alarm_date.strftime('%d %b')} at {alarm_hour:02d}:{alarm_min:02d} — {alarm_subj}!", icon="🔔")
                st.rerun()
            else:
                st.error("Enter a subject name!")

    # ── Display alarms — everything in ONE iframe ────────────────────────────
    if alarms:
        import json as _j

        alarms_json = _j.dumps(alarms)
        n_alarms    = len(alarms)
        iframe_h    = n_alarms * 150 + 200

        st.components.v1.html(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{background:transparent;font-family:'DM Sans',sans-serif;padding:0;}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
  @keyframes slideIn{{from{{opacity:0;transform:translateY(-16px)}}to{{opacity:1;transform:translateY(0)}}}}
  @keyframes glow{{0%,100%{{box-shadow:0 0 18px rgba(248,113,113,.4)}}50%{{box-shadow:0 0 44px rgba(248,113,113,.9)}}}}
  .clock{{font-size:11px;color:#4a4060;padding:2px 0 8px;font-family:monospace;}}
  .card{{border-radius:0 14px 14px 0;padding:14px 18px;margin-bottom:10px;border:1px solid rgba(167,139,250,.12);transition:all .3s;}}
  .card.normal{{background:rgba(255,255,255,.03);border-left:4px solid #a78bfa;}}
  .card.soon{{background:rgba(255,255,255,.03);border-left:4px solid #fbbf24;}}
  .card.firing{{background:rgba(248,113,113,.07);border-left:5px solid #f87171;animation:glow 1.2s infinite;}}
  .card.past{{background:rgba(255,255,255,.01);border-left:4px solid #3a3050;opacity:.6;}}
  .card-row{{display:flex;justify-content:space-between;align-items:center;}}
  .subject{{font-family:'Syne',sans-serif;font-weight:700;font-size:15px;}}
  .meta{{font-size:11.5px;color:#6b5f8a;margin-top:4px;line-height:1.6;}}
  .badge{{font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;white-space:nowrap;}}
  .badge.normal{{color:#a78bfa;background:rgba(167,139,250,.12);}}
  .badge.soon{{color:#fbbf24;background:rgba(251,191,36,.12);}}
  .badge.firing{{color:#f87171;background:rgba(248,113,113,.15);animation:pulse 1s infinite;}}
  .badge.past{{color:#4a4060;background:rgba(100,100,100,.08);}}
  .alarm-banner{{display:none;background:linear-gradient(135deg,#2d0a0a,#4a0f0f);
    border:3px solid #f87171;border-radius:14px;padding:18px 22px;margin-bottom:12px;
    animation:slideIn .4s ease, glow 1.2s infinite .4s;}}
  .banner-title{{font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:#f87171;}}
  .banner-sub{{font-size:13px;color:#fca5a5;margin-top:5px;}}
  .banner-subj{{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:#a78bfa;margin-top:7px;}}
  .close-btn{{float:right;background:rgba(255,255,255,.12);border:none;color:white;
    border-radius:50%;width:28px;height:28px;cursor:pointer;font-size:14px;}}
</style>
</head><body>

<div class="clock" id="clk">🕐 Loading...</div>
<div id="banner" class="alarm-banner">
  <button class="close-btn" onclick="document.getElementById('banner').style.display='none'">✕</button>
  <div class="banner-title">🚨 STUDY TIME, {name.upper()}!</div>
  <div class="banner-sub">Your alarm fired — put everything down!</div>
  <div class="banner-subj" id="banner-subj"></div>
</div>
<div id="cards"></div>

<script>
var ALARMS = {alarms_json};
var TZ     = "{tz_str}";
var fired  = {{}};

var SOUNDS = {{
  gentle_bell:    function(){{var c=new(AudioContext||webkitAudioContext);[523,659,784].forEach(function(f,i){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(.25,c.currentTime+i*.5);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+i*.5+1.5);o.start(c.currentTime+i*.5);o.stop(c.currentTime+i*.5+1.5);}});}},
  urgent_alarm:   function(){{var c=new(AudioContext||webkitAudioContext);for(var i=0;i<8;i++){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='square';o.frequency.value=i%2==0?880:660;g.gain.setValueAtTime(.2,c.currentTime+i*.15);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+i*.15+.13);o.start(c.currentTime+i*.15);o.stop(c.currentTime+i*.15+.13);}}}},
  meditation_bowl:function(){{var c=new(AudioContext||webkitAudioContext);[220,440,880,1320].forEach(function(f,i){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0,c.currentTime+i*.1);g.gain.linearRampToValueAtTime(.15,c.currentTime+i*.1+.05);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+i*.1+3.5);o.start(c.currentTime+i*.1);o.stop(c.currentTime+i*.1+3.5);}});}},
  ocean_wave:     function(){{var c=new(AudioContext||webkitAudioContext),b=c.createBuffer(1,c.sampleRate*3,c.sampleRate),d=b.getChannelData(0);for(var i=0;i<d.length;i++)d[i]=(Math.random()*2-1)*.4;var s=c.createBufferSource(),g=c.createGain(),f=c.createBiquadFilter();f.type='lowpass';f.frequency.value=400;s.buffer=b;s.connect(f);f.connect(g);g.connect(c.destination);g.gain.setValueAtTime(.3,c.currentTime);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+3);s.start();s.stop(c.currentTime+3);}},
  om_chant:       function(){{var c=new(AudioContext||webkitAudioContext);[136,272,408].forEach(function(f){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0,c.currentTime);g.gain.linearRampToValueAtTime(.12,c.currentTime+.5);g.gain.setValueAtTime(.12,c.currentTime+3);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+4.5);o.start();o.stop(c.currentTime+4.5);}});}},
  focus_tone:     function(){{var c=new(AudioContext||webkitAudioContext),o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='sine';o.frequency.value=40;g.gain.setValueAtTime(0,c.currentTime);g.gain.linearRampToValueAtTime(.2,c.currentTime+.3);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+3);o.start();o.stop(c.currentTime+3);}},
  energy_boost:   function(){{var c=new(AudioContext||webkitAudioContext);[261,329,392,523,659,784,1047].forEach(function(f,i){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='triangle';o.frequency.value=f;g.gain.setValueAtTime(.15,c.currentTime+i*.08);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+i*.08+.2);o.start(c.currentTime+i*.08);o.stop(c.currentTime+i*.08+.2);}});}},
  soft_chime:     function(){{var c=new(AudioContext||webkitAudioContext);[784,988,1175,1568].forEach(function(f,i){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0,c.currentTime+i*.3);g.gain.linearRampToValueAtTime(.12,c.currentTime+i*.3+.02);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+i*.3+1.8);o.start(c.currentTime+i*.3);o.stop(c.currentTime+i*.3+1.8);}});}},
  silent:         function(){{}}
}};

function play(key){{
  try{{(SOUNDS[key]||SOUNDS.gentle_bell)();}}catch(e){{}}
}}

function getNow(){{
  return new Date(new Date().toLocaleString("en-US",{{timeZone:TZ}}));
}}

function getToday(n){{
  return n.getFullYear()+"-"+String(n.getMonth()+1).padStart(2,"0")+"-"+String(n.getDate()).padStart(2,"0");
}}

function render(){{
  var now   = getNow();
  var h     = now.getHours(), m = now.getMinutes();
  var today = getToday(now);
  var nowM  = h*60+m;

  // Update clock
  document.getElementById("clk").textContent =
    "🕐 "+String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+
    String(now.getSeconds()).padStart(2,"0")+" ("+TZ.split("/").pop().replace(/_/g," ")+")";

  // Rebuild cards
  var html = "";
  ALARMS.forEach(function(a,i){{
    var alarmM = a.hour*60+a.minute;
    var diff   = alarmM - nowM;
    var isToday= a.date===today;
    var state, badge, subjectColor, icon;

    if(isToday && diff===0){{
      state="firing"; badge="🔴 ALARM FIRING!"; subjectColor="#f87171"; icon="🚨";
      // Fire sound + show banner (once only)
      var fkey=a.date+"_"+a.hour+"_"+a.minute;
      if(!fired[fkey]){{
        fired[fkey]=true;
        play(a.sound_key);
        setTimeout(function(){{play(a.sound_key);}},2500);
        setTimeout(function(){{play(a.sound_key);}},5000);
        var banner=document.getElementById("banner");
        document.getElementById("banner-subj").textContent="📚 "+a.subject;
        banner.style.display="block";
        setTimeout(function(){{banner.style.display="none";}},30000);
      }}
    }} else if(isToday && diff>0 && diff<=60){{
      state="soon"; badge="🟡 In "+diff+" min"; subjectColor="#fbbf24"; icon="⏰";
    }} else if(isToday && diff<0){{
      state="past"; badge="⏸️ Past"; subjectColor="#4a4060"; icon="⏰";
    }} else{{
      var dispDate=a.date===today?"Today":a.date;
      state="normal"; badge="🟢 "+dispDate+" "+String(a.hour).padStart(2,"0")+":"+String(a.minute).padStart(2,"0");
      subjectColor="#c4b5fd"; icon="⏰";
    }}

    html+=
      "<div class='card "+state+"'>"+
        "<div class='card-row'>"+
          "<div>"+
            "<div class='subject' style='color:"+subjectColor+";'>"+icon+" "+a.subject+"</div>"+
            "<div class='meta'>"+
              "📅 "+a.date+" &nbsp;·&nbsp; ⏰ "+String(a.hour).padStart(2,"0")+":"+String(a.minute).padStart(2,"0")+
              " &nbsp;·&nbsp; ⏱️ "+a.duration+" min &nbsp;·&nbsp; 🔁 "+a.repeat+
            "</div>"+
            "<div class='meta'>"+a.sound_label+" &nbsp;·&nbsp; 🌍 "+a.timezone.split("/").pop().replace(/_/g," ")+"</div>"+
          "</div>"+
          "<span class='badge "+state+"'>"+badge+"</span>"+
        "</div>"+
      "</div>";
  }});
  document.getElementById("cards").innerHTML=html;
}}

render();
setInterval(render,1000);
</script>
</body></html>""", height=iframe_h, scrolling=False)

        if st.button("🗑️ Clear All Alarms", key="clear_all"):
            save_alarms([])
            st.rerun()

    else:
        st.markdown("""<div style='text-align:center;padding:2rem;color:#4a4060;'>
            <div style='font-size:2.5rem;'>⏰</div>
            <div style='margin-top:.5rem;font-size:.9rem;'>No alarms scheduled yet.</div>
            <div style='font-size:.8rem;margin-top:.3rem;'>Add one above to get notified!</div>
        </div>""", unsafe_allow_html=True)

        # How it works
    st.markdown("<div style='height:1rem'></div><div class='card-title'>ℹ️ How It Works</div>", unsafe_allow_html=True)
    for step, desc, color in [
        ("1️⃣ Add alarm","Pick subject, exact date, hour, minute","#a78bfa"),
        ("2️⃣ Alarms saved to disk","Survive page reloads — never lost","#34d399"),
        ("3️⃣ Countdown updates live","Badge ticks every second in browser","#60a5fa"),
        ("4️⃣ Alarm fires at exact time","Sound plays + popup appears automatically","#fbbf24"),
        ("5️⃣ Enter Focus Mode","Full-screen timer locks you in","#f472b6"),
    ]:
        st.markdown(f"""<div style='background:rgba(255,255,255,.03);border-left:3px solid {color};
            border-radius:0 10px 10px 0;padding:.7rem 1rem;margin-bottom:.5rem;'>
            <span style='font-weight:700;color:{color};'>{step}</span>
            <span style='color:#a09cc0;font-size:.85rem;margin-left:.5rem;'>{desc}</span>
        </div>""", unsafe_allow_html=True)
