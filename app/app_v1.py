import streamlit as st
import numpy as np
import pandas as pd
from collections import deque
import joblib
import serial
import serial.tools.list_ports
import time
import os
from datetime import datetime

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MachineIQ Monitor",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject Custom CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Exo+2:wght@300;400;600;800&display=swap');

html, body, .stApp{ font-family: 'Exo 2', sans-serif; }

.stApp { background: #0a0c10; color: #c8d6e5; }

[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1e2d3d;
}
[data-testid="stSidebar"] * { color: #8b9ab0 !important; }
[data-testid="stSidebar"] .stRadio label {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    letter-spacing: 1px;
    font-size: 0.9rem;
    text-transform: uppercase;
}

[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0f1923 0%, #131e2c 100%);
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00d4ff, #0077ff);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    color: #4a9eda !important;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.8rem;
    color: #e8f4fd !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
}

.stButton > button {
    background: linear-gradient(135deg, #0d2137, #0a3255);
    color: #00d4ff;
    border: 1px solid #0077ff;
    border-radius: 4px;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 0.8rem;
    padding: 8px 20px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0a3255, #0d4a7a);
    border-color: #00d4ff;
    color: #ffffff;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

[data-testid="stDataFrame"] { border: 1px solid #1e3a5f; border-radius: 6px; }

h1, h2, h3 {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}
h1 { color: #e8f4fd; font-size: 1.6rem; }
h2 { color: #4a9eda; font-size: 1.1rem; }
h3 { color: #8bc4e8; font-size: 0.95rem; }

.alert-yellow {
    background: linear-gradient(135deg, #2d1f00, #3d2900);
    border: 2px solid #ff9900;
    border-left: 6px solid #ff9900;
    border-radius: 6px;
    padding: 20px 24px;
    margin-bottom: 16px;
    font-family: 'Rajdhani', sans-serif;
    animation: pulse-yellow 2s ease-in-out infinite;
}
.alert-red {
    background: linear-gradient(135deg, #2d0000, #400000);
    border: 2px solid #ff2222;
    border-left: 6px solid #ff2222;
    border-radius: 6px;
    padding: 20px 24px;
    margin-bottom: 16px;
    font-family: 'Rajdhani', sans-serif;
    animation: pulse-red 1s ease-in-out infinite;
}
.alert-title {
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.alert-yellow .alert-title { color: #ff9900; }
.alert-red .alert-title    { color: #ff4444; }
.alert-body { color: #c8d6e5; font-size: 1rem; font-weight: 500; }

@keyframes pulse-yellow {
    0%, 100% { box-shadow: 0 0 8px rgba(255,153,0,0.2); }
    50%       { box-shadow: 0 0 24px rgba(255,153,0,0.5); }
}
@keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 12px rgba(255,34,34,0.3); }
    50%       { box-shadow: 0 0 36px rgba(255,34,34,0.7); }
}

.state-badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 3px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 1rem;
    letter-spacing: 3px;
    font-weight: bold;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.state-green  { background: #001a00; border: 1px solid #00ff44; color: #00ff44; }
.state-yellow { background: #1a0f00; border: 1px solid #ff9900; color: #ff9900; }
.state-red    { background: #1a0000; border: 1px solid #ff2222; color: #ff2222; }

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #1e3a5f, transparent);
    margin: 20px 0;
}

[data-testid="stLineChart"] {
    background: #0d1117;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
}

[data-testid="stRadio"] > label {
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600;
    letter-spacing: 1px;
}

.stAlert { font-family: 'Rajdhani', sans-serif; }

.sidebar-logo {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.3rem;
    font-weight: 800;
    letter-spacing: 4px;
    color: #00d4ff;
    text-transform: uppercase;
    padding: 10px 0;
    border-bottom: 1px solid #1e3a5f;
    margin-bottom: 20px;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0a0c10; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ─── Constants ──────────────────────────────────────────────────────────────────
WINDOW           = 50
INIT_SAMPLES     = 100
REFRESH_INTERVAL = 0.4
MODEL_PATH       = "model/I_Tree.pkl"
SCALER_PATH      = "model/scaler.pkl"

# ─── Load Pre-trained Model & Scaler ────────────────────────────────────────────
@st.cache_resource
def load_models():
    errors = []
    model, scaler = None, None
    try:
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
    except Exception as e:
        errors.append(f"Failed to load artifacts: {e}")
    return model, scaler, errors

MODEL, SCALER, LOAD_ERRORS = load_models()

# ─── Session State Init ─────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "t":             0,
        "temp_buf":      deque(maxlen=WINDOW),
        "vib_buf":       deque(maxlen=WINDOW),
        "snd_buf":       deque(maxlen=WINDOW),
        "score_history": [],
        "logs":          [],
        "thresholds":    None,
        "system_status": "RUNNING" if MODEL is not None else "STOPPED",
        "last_state":    "GREEN",
        "red_logged":    False,
        "init_features": [],
        # Input mode & Arduino serial state
        "input_mode":   "Simulated",
        "serial_port":  None,
        "serial_baud":  9600,
        "serial_conn":  None,
        "serial_error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── Simulation ─────────────────────────────────────────────────────────────────
def simulate_sensors(t):
    """Three-phase simulation: normal → degradation → failure."""
    if t < 300:
        temp = 70  + np.random.normal(0, 1.5)
        vib  = 0.5 + np.random.normal(0, 0.05)
        snd  = 45  + np.random.normal(0, 2)
    elif t < 600:
        drift = (t - 300) / 300
        temp = 70  + drift * 18  + np.random.normal(0, 3)
        vib  = 0.5 + drift * 1.2 + np.random.normal(0, 0.15)
        snd  = 45  + drift * 25  + np.random.normal(0, 5)
    else:
        temp = 95  + np.random.normal(0, 8)   + np.random.choice([0, 15],  p=[0.7, 0.3])
        vib  = 2.5 + np.random.normal(0, 0.6) + np.random.choice([0, 1.5], p=[0.6, 0.4])
        snd  = 85  + np.random.normal(0, 12)  + np.random.choice([0, 20],  p=[0.6, 0.4])
    return temp, vib, snd

# ─── Arduino Serial Helpers ──────────────────────────────────────────────────────
def list_serial_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

def open_serial(port, baud=9600):
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=1)
        return ser, None
    except Exception as e:
        return None, str(e)

def read_arduino(ser):
    """
    Read one CSV line from Arduino and parse into (temp, vib, snd).
    Expected Arduino format:  Serial.println("72.3,0.52,48.1")
    Returns (float, float, float) or None on failure.
    """
    try:
        raw   = ser.readline().decode("utf-8").strip()
        parts = raw.split(",")
        if len(parts) == 3:
            return float(parts[0]), float(parts[1]), float(parts[2])
    except Exception:
        pass
    return None

# ─── Feature Extraction ─────────────────────────────────────────────────────────
def extract_features(temp, vib, snd, t_buf, v_buf, s_buf):
    t_buf.append(temp); v_buf.append(vib); s_buf.append(snd)
    ta, va, sa = np.array(t_buf), np.array(v_buf), np.array(s_buf)
    return [
        temp, vib, snd,
        np.mean(ta), np.mean(va), np.mean(sa),
        np.std(ta) if len(ta) > 1 else 0,
        np.std(va) if len(va) > 1 else 0,
        np.std(sa) if len(sa) > 1 else 0,
    ]

# ─── State Classification ───────────────────────────────────────────────────────
def classify(score, thresholds):
    if thresholds is None:
        return "GREEN"
    if score <= thresholds["red"]:
        return "RED"
    elif score <= thresholds["yellow"]:
        return "YELLOW"
    return "GREEN"

# ─── Contributing Sensors ───────────────────────────────────────────────────────
def contributing_sensors(temp, vib, snd):
    suspects = []
    if temp > 80:  suspects.append("Temperature")
    if vib  > 1.2: suspects.append("Vibration")
    if snd  > 65:  suspects.append("Sound")
    return ", ".join(suspects) if suspects else "Multiple"

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚙ MachineIQ</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", ["Live Monitor", "Logs"], label_visibility="collapsed")
    st.markdown("---")

    # Model load status
    if MODEL is not None:
        st.markdown("""
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                        color:#00ff44;letter-spacing:1px;padding:4px 0;">
                ✔ I_Tree.pkl loaded<br>✔ scaler.pkl loaded
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                        color:#ff4444;letter-spacing:1px;padding:4px 0;">
                ✖ Model files missing
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Input Source ──────────────────────────────────────────────────────────
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                    color:#4a9eda;letter-spacing:2px;padding:4px 0;">
            INPUT SOURCE
        </div>
    """, unsafe_allow_html=True)

    input_mode = st.radio(
        "Input Mode",
        ["Simulated", "Arduino"],
        index=0 if st.session_state.input_mode == "Simulated" else 1,
        label_visibility="collapsed",
    )
    st.session_state.input_mode = input_mode

    if input_mode == "Arduino":
        available_ports = list_serial_ports()

        if not available_ports:
            st.markdown("""
                <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                            color:#ff4444;padding:4px 0;">
                    ✖ No serial ports found.<br>Check USB connection.
                </div>
            """, unsafe_allow_html=True)
        else:
            current_port = st.session_state.serial_port
            port_index   = available_ports.index(current_port) if current_port in available_ports else 0

            selected_port = st.selectbox("Port", available_ports, index=port_index)
            selected_baud = st.selectbox("Baud Rate", [9600, 19200, 38400, 57600, 115200], index=0)
            st.session_state.serial_port = selected_port
            st.session_state.serial_baud = selected_baud

            col_con, col_dis = st.columns(2)
            with col_con:
                if st.button("Connect", use_container_width=True):
                    if st.session_state.serial_conn:
                        try: st.session_state.serial_conn.close()
                        except Exception: pass
                    ser, err = open_serial(selected_port, selected_baud)
                    st.session_state.serial_conn  = ser
                    st.session_state.serial_error = err
            with col_dis:
                if st.button("Disconnect", use_container_width=True):
                    if st.session_state.serial_conn:
                        try: st.session_state.serial_conn.close()
                        except Exception: pass
                    st.session_state.serial_conn  = None
                    st.session_state.serial_error = None

            # Connection status
            conn = st.session_state.serial_conn
            if conn and conn.is_open:
                st.markdown(f"""
                    <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                                color:#00ff44;padding:4px 0;">
                        ● CONNECTED — {selected_port} @ {selected_baud}
                    </div>
                """, unsafe_allow_html=True)
            elif st.session_state.serial_error:
                st.markdown(f"""
                    <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                                color:#ff4444;padding:4px 0;">
                        ✖ {st.session_state.serial_error}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                                color:#8b9ab0;padding:4px 0;">
                        ○ Not connected
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # System status
    status = st.session_state.system_status
    color  = "#00ff44" if status == "RUNNING" else "#ff2222"
    st.markdown(f"""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                    color:{color};letter-spacing:2px;padding:8px 0;">
            ● SYSTEM: {status}
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
                    color:#4a9eda;letter-spacing:1px;padding:4px 0;">
            SAMPLES: {st.session_state.t}
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.thresholds:
        thr = st.session_state.thresholds
        st.markdown(f"""
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                        color:#8b9ab0;padding:6px 0;line-height:1.8;">
                THRESH YELLOW: {thr['yellow']:.4f}<br>
                THRESH RED: {thr['red']:.4f}
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("↺  Reset System", use_container_width=True, key = 'reset_btn'):
        # Safely close serial port before clearing state
        if st.session_state.get("serial_conn"):
            try: st.session_state.serial_conn.close()
            except Exception: pass
        keys_to_clear = [
            "t", "temp_buf", "vib_buf", "snd_buf", "score_history", "logs",
            "thresholds", "system_status", "last_state", "red_logged", "init_features",
            "serial_conn", "serial_error",
        ]
        for k in keys_to_clear:
            st.session_state.pop(k, None)
            
        init_state()
        st.rerun()
        st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE MONITOR
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Live Monitor":
    col_title, col_phase = st.columns([3, 1])
    with col_title:
        st.markdown("## ⚙ LIVE MACHINE HEALTH MONITOR")
    with col_phase:
        t = st.session_state.t
        if st.session_state.input_mode == "Simulated":
            phase        = "NORMAL" if t < 300 else ("DEGRADATION" if t < 600 else "FAILURE")
            phase_colors = {"NORMAL": "#00ff44", "DEGRADATION": "#ff9900", "FAILURE": "#ff2222"}
            st.markdown(f"""
                <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
                            color:{phase_colors[phase]};text-align:right;padding-top:12px;letter-spacing:2px;">
                    SIM PHASE: {phase}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
                            color:#4a9eda;text-align:right;padding-top:12px;letter-spacing:2px;">
                    SOURCE: ARDUINO
                </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Model load error — halt page
    if LOAD_ERRORS:
        for err in LOAD_ERRORS:
            st.error(f"⚠ {err}")
        st.warning("Place `I_Tree.pkl` and `scaler.pkl` in the `model/` directory, then restart the app.")
        st.stop()

    alert_placeholder = st.empty()

    m1, m2, m3, m4 = st.columns(4)
    metric_temp  = m1.empty()
    metric_vib   = m2.empty()
    metric_snd   = m3.empty()
    metric_score = m4.empty()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    s1, s2 = st.columns([1, 2])
    with s1:
        st.markdown("### SYSTEM STATE")
        state_placeholder = st.empty()
    with s2:
        st.markdown("### ANOMALY SCORE TREND")
        chart_placeholder = st.empty()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    init_placeholder = st.empty()

    # ── Main Loop ─────────────────────────────────────────────────────────────
    t = st.session_state.t
    temp_buf = st.session_state.temp_buf
    vib_buf  = st.session_state.vib_buf
    snd_buf  = st.session_state.snd_buf
    while st.session_state.system_status == "RUNNING":
        # ── Sensor Read ────────────────────────────────────────────────────
        if st.session_state.input_mode == "Arduino":
            ser = st.session_state.serial_conn
            if ser is None or not ser.is_open:
                with alert_placeholder.container():
                    st.markdown("""
                        <div class="alert-yellow">
                            <div class="alert-title">⚠ ARDUINO NOT CONNECTED</div>
                            <div class="alert-body">
                                Select a port and click <strong>Connect</strong> in the sidebar.
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                break
            reading = read_arduino(ser)
            if reading is None:
                
                time.sleep(0.1)
                st.rerun()
            temp, vib, snd = reading
        else:
            temp, vib, snd = simulate_sensors(t)

        features = extract_features(temp, vib, snd, temp_buf, vib_buf, snd_buf)

        # ── Threshold Calibration Phase ─────────────────────────────────────
        if t < INIT_SAMPLES:
            st.session_state.init_features.append(features)
            with init_placeholder.container():
                st.markdown(f"""
                    <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
                                color:#4a9eda;padding:20px;background:#0d1117;
                                border:1px solid #1e3a5f;border-radius:6px;text-align:center;">
                        ◌ CALIBRATING THRESHOLDS — COLLECTING BASELINE DATA<br>
                        <span style="color:#00d4ff;font-size:1.2rem;">{t}/{INIT_SAMPLES} samples</span>
                    </div>
                """, unsafe_allow_html=True)
                st.progress(t / INIT_SAMPLES)
            score = 0.0
            current_state = "GREEN"
        else:
            init_placeholder.empty()

            # Freeze thresholds once after calibration
            if st.session_state.thresholds is None:
                X_init        = np.array(st.session_state.init_features)
                X_scaled_init = SCALER.transform(X_init)
                init_scores   = MODEL.decision_function(X_scaled_init)
                st.session_state.thresholds = {
                    "yellow": np.percentile(init_scores, 25),
                    "red": np.percentile(init_scores, 5),
                }

            X = np.array(features).reshape(1, -1)
            X_scaled = SCALER.transform(X)
            score = float(MODEL.decision_function(X_scaled)[0])
            current_state = classify(score, st.session_state.thresholds)

        # Update score history
        st.session_state.score_history.append(score)
        if len(st.session_state.score_history) > 200:
            st.session_state.score_history = st.session_state.score_history[-200:]

        # ── Metrics ─────────────────────────────────────────────────────────
        # with metric_temp:
        #     delta_t = f"{temp - np.mean(temp_buf):.1f}" if len(temp_buf) > 1 else None
        #     st.metric("TEMPERATURE (°C)", f"{temp:.1f}", delta=delta_t)
        # with metric_vib:
        #     delta_v = f"{vib - np.mean(vib_buf):.3f}" if len(vib_buf) > 1 else None
        #     st.metric("VIBRATION (mm/s)", f"{vib:.3f}", delta=delta_v)
        # with metric_snd:
        #     delta_s = f"{snd - np.mean(snd_buf):.1f}" if len(snd_buf) > 1 else None
        #     st.metric("SOUND (dB)", f"{snd:.1f}", delta=delta_s)
        # with metric_score:
        #     st.metric("ANOMALY SCORE", f"{score:.4f}")
        metric_temp.metric("TEMPERATURE (°C)", f"{temp:.1f}")
        metric_vib.metric("VIBRATION (mm/s)", f"{vib:.3f}")
        metric_snd.metric("SOUND (dB)", f"{snd:.1f}")
        metric_score.metric("ANOMALY SCORE", f"{score:.4f}")
        # ── State Badge ─────────────────────────────────────────────────────
        state_map = {
            "GREEN":  ("state-green",  "▲ NOMINAL"),
            "YELLOW": ("state-yellow", "⚠ DEGRADING"),
            "RED":    ("state-red",    "✖ CRITICAL"),
        }
        badge_class, badge_text = state_map[current_state]
        with state_placeholder:
            st.markdown(f"""
                <div class="state-badge {badge_class}">{badge_text}</div>
                <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
                            color:#4a9eda;margin-top:8px;">
                    SCORE: {score:.4f}
                </div>
            """, unsafe_allow_html=True)

        # ── Chart ───────────────────────────────────────────────────────────
        if len(st.session_state.score_history) > 1:
            with chart_placeholder:
                st.line_chart(
                    pd.DataFrame({"Anomaly Score": st.session_state.score_history}),
                    height=160, use_container_width=True,
                )

        # ── Alert + State Machine ───────────────────────────────────────────
        if current_state == "GREEN":
            alert_placeholder.empty()

        elif current_state == "YELLOW":
            sensors = contributing_sensors(temp, vib, snd)
            with alert_placeholder.container():
                st.markdown(f"""
                    <div class="alert-yellow">
                        <div class="alert-title">⚠ EARLY DEGRADATION DETECTED</div>
                        <div class="alert-body">
                            System showing signs of wear. Sensor anomalies detected.<br>
                            <strong>Contributing:</strong> {sensors} &nbsp;|&nbsp;
                            <strong>Score:</strong> {score:.4f} &nbsp;|&nbsp;
                            <strong>Sample:</strong> {t}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.session_state.logs.append({
                "Timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Temperature":  round(temp, 2),
                "Vibration":    round(vib, 4),
                "Sound":        round(snd, 2),
                "State":        "YELLOW",
                "Contributing": sensors,
            })

        elif current_state == "RED":
            sensors = contributing_sensors(temp, vib, snd)
            with alert_placeholder.container():
                st.markdown(f"""
                    <div class="alert-red">
                        <div class="alert-title">✖ CRITICAL FAILURE — SYSTEM HALTED</div>
                        <div class="alert-body">
                            Machine health has reached critical threshold. Monitoring suspended.<br>
                            <strong>Contributing:</strong> {sensors} &nbsp;|&nbsp;
                            <strong>Score:</strong> {score:.4f} &nbsp;|&nbsp;
                            <strong>Sample:</strong> {t}<br><br>
                            <strong>→ Use "Reset System" in the sidebar to restart.</strong>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            if not st.session_state.red_logged:
                st.session_state.logs.append({
                    "Timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Temperature":  round(temp, 2),
                    "Vibration":    round(vib, 4),
                    "Sound":        round(snd, 2),
                    "State":        "RED",
                    "Contributing": sensors,
                })
                st.session_state.red_logged = True
            st.session_state.system_status = "STOPPED"

        # ── Advance ─────────────────────────────────────────────────────────
        st.session_state.t          = t + 1
        st.session_state.last_state = current_state

        if st.session_state.system_status == "RUNNING":
            time.sleep(REFRESH_INTERVAL)
            st.rerun()

    else:
        # ── STOPPED state ───────────────────────────────────────────────────
        last_score = st.session_state.score_history[-1] if st.session_state.score_history else 0
        last_temp  = list(st.session_state.temp_buf)[-1] if st.session_state.temp_buf else 0
        last_vib   = list(st.session_state.vib_buf)[-1]  if st.session_state.vib_buf  else 0
        last_snd   = list(st.session_state.snd_buf)[-1]  if st.session_state.snd_buf  else 0

        with alert_placeholder.container():
            st.markdown(f"""
                <div class="alert-red">
                    <div class="alert-title">✖ CRITICAL FAILURE — SYSTEM HALTED</div>
                    <div class="alert-body">
                        Critical threshold was exceeded. Machine monitoring has been suspended.<br>
                        Last recorded anomaly score: <strong>{last_score:.4f}</strong><br><br>
                        <strong>→ Use "Reset System" in the sidebar to restart.</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with metric_temp:  st.metric("TEMPERATURE (°C)", f"{last_temp:.1f}")
        with metric_vib:   st.metric("VIBRATION (mm/s)", f"{last_vib:.3f}")
        with metric_snd:   st.metric("SOUND (dB)",        f"{last_snd:.1f}")
        with metric_score: st.metric("ANOMALY SCORE",     f"{last_score:.4f}")

        with state_placeholder:
            st.markdown('<div class="state-badge state-red">✖ HALTED</div>', unsafe_allow_html=True)

        if len(st.session_state.score_history) > 1:
            with chart_placeholder:
                st.line_chart(
                    pd.DataFrame({"Anomaly Score": st.session_state.score_history}),
                    height=160, use_container_width=True,
                )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LOGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Logs":
    st.markdown("## ◉ EVENT LOG ARCHIVE")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    logs         = st.session_state.logs
    yellow_count = sum(1 for l in logs if l.get("State") == "YELLOW")
    red_count    = sum(1 for l in logs if l.get("State") == "RED")

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL EVENTS",    len(logs))
    c2.metric("⚠ YELLOW EVENTS", yellow_count)
    c3.metric("✖ RED EVENTS",    red_count)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if not logs:
        st.markdown("""
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.85rem;
                        color:#2a4a6a;text-align:center;padding:60px;
                        border:1px dashed #1e3a5f;border-radius:6px;">
                NO ANOMALY EVENTS RECORDED YET<br>
                <span style="font-size:0.7rem;color:#1e3a5f;">
                    System will log YELLOW and RED state transitions.
                </span>
            </div>
        """, unsafe_allow_html=True)
    else:
        df = pd.DataFrame(logs[::-1])

        def style_state(val):
            if val == "RED":
                return "background-color: #2d0000; color: #ff4444; font-weight: bold;"
            elif val == "YELLOW":
                return "background-color: #2d1f00; color: #ff9900; font-weight: bold;"
            return ""

        st.dataframe(
            df.style.map(style_state, subset=["State"]),
        )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.download_button(
            label="↓  Export Log as CSV",
            data=df.to_csv(index=False),
            file_name=f"machine_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
