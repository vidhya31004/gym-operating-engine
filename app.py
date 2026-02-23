import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import re


# =====================================================
# PAGE
# =====================================================
st.set_page_config(layout="wide")
st.title("🏋️ Gym Operating System")


# =====================================================
# PATHS
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

ENGINE_FILE = os.path.join(
    DATA_PATH,
    "studio_decision_engine_v1.xlsx"
)

CLIENT_FILE = os.path.join(
    DATA_PATH,
    "client_database.xlsx"
)


# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load():

    time_engine = pd.read_excel(
        ENGINE_FILE,
        sheet_name="TIME_ENGINE",
        header=None,
        engine="openpyxl"
    ).fillna("")

    dashboard = pd.read_excel(
        ENGINE_FILE,
        sheet_name="DASHBOARD",
        header=None,
        engine="openpyxl"
    ).fillna("")

    session = pd.read_excel(
        CLIENT_FILE,
        sheet_name="SESSION_LOG",
        engine="openpyxl"
    )

    return time_engine, dashboard, session


time_engine, dashboard, session_log = load()


# =====================================================
# HELPERS
# =====================================================
def clean(x):
    return re.sub(r"[^a-z0-9 ]", "", str(x).lower())


def to_number(v):

    if isinstance(v, (int, float)):
        return v

    v = str(v).replace("₹", "").replace(",", "").replace("%", "")

    try:
        return float(v)
    except:
        return None


# =====================================================
# METRIC SCANNER
# =====================================================
def scan_sheet(sheet, words):

    rows, cols = sheet.shape

    for r in range(rows):
        for c in range(cols):

            cell = clean(sheet.iloc[r, c])

            if all(w in cell for w in words):

                # RIGHT
                for i in range(1,6):
                    if c+i < cols:
                        num = to_number(sheet.iloc[r, c+i])
                        if num is not None:
                            return num

                # DOWN
                for i in range(1,6):
                    if r+i < rows:
                        num = to_number(sheet.iloc[r+i, c])
                        if num is not None:
                            return num

                # TEXT VALUE
                for i in range(1,4):
                    if c+i < cols:
                        val = sheet.iloc[r, c+i]
                        if isinstance(val,str) and val.strip():
                            return val

    return None


def find_metric(label):

    words = clean(label).split()

    val = scan_sheet(time_engine, words)
    if val is not None:
        return val

    val = scan_sheet(dashboard, words)
    if val is not None:
        return val

    return 0


# =====================================================
# CLEAN SESSION DATA
# =====================================================
session_log.columns = (
    session_log.columns
    .astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

client_col = [c for c in session_log.columns if "client" in c][0]
trainer_col = [c for c in session_log.columns if "trainer" in c][0]
date_col = [c for c in session_log.columns if "date" in c][0]
weight_col = [c for c in session_log.columns if "weight" in c][0]
perf_col = [c for c in session_log.columns if "performance" in c][0]

session_log[date_col] = pd.to_datetime(
    session_log[date_col],
    errors="coerce"
)


# =====================================================
# SIDEBAR
# =====================================================
page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard","Client Analytics","Log Session"]
)


# =====================================================
# DASHBOARD
# =====================================================
if page == "Dashboard":

    st.header("📊 Studio Command Center")

    r1 = st.columns(7)

    r1[0].metric("Active Clients",
        int(find_metric("active clients")))

    r1[1].metric("Monthly Revenue",
        f"₹{find_metric('monthly revenue'):,.0f}")

    r1[2].metric("Revenue / Hour",
        f"₹{find_metric('revenue per hour'):,.0f}")

    r1[3].metric("Average Utilization",
        f"{find_metric('average utilization')*100:.1f}%")

    r1[4].metric("Overload Events",
        int(find_metric("overload")))

    r1[5].metric("Capacity Utilization",
        f"{find_metric('capacity utilization')*100:.1f}%")

    r1[6].metric("Revenue Realization",
        f"{find_metric('revenue realization')*100:.0f}%")

    st.divider()

    r2 = st.columns(6)

    r2[0].metric("Monthly Profit",
        f"₹{find_metric('monthly profit'):,.0f}")

    r2[1].metric("Profit / Hour",
        f"₹{find_metric('profit per hour'):,.0f}")

    r2[2].metric("Break Even Clients",
        int(find_metric("break even")))

    r2[3].metric("Profit Margin",
        f"{find_metric('profit margin')*100:.0f}%")

    r2[4].metric("Capacity Pressure",
        f"{find_metric('capacity pressure')*100:.0f}%")

    r2[5].metric("Operational Status",
        find_metric("operational status"))


# =====================================================
# CLIENT ANALYTICS
# =====================================================
elif page == "Client Analytics":

    clients = session_log[client_col].dropna().unique()

    selected = st.selectbox("Client", clients)

    data = session_log[
        session_log[client_col] == selected
    ]

    c1, c2 = st.columns(2)

    c1.plotly_chart(
        px.line(data, x=date_col, y=weight_col,
        markers=True, title="Weight Progress"),
        use_container_width=True)

    c2.plotly_chart(
        px.line(data, x=date_col, y=perf_col,
        markers=True, title="Performance"),
        use_container_width=True)


# =====================================================
# LOG SESSION
# =====================================================
elif page == "Log Session":

    st.header("📝 Log Training Session")

    clients = session_log[client_col].dropna().unique()
    trainers = session_log[trainer_col].dropna().unique()

    client = st.selectbox("Client", clients)
    trainer = st.selectbox("Trainer", trainers)

    weight = float(st.text_input("Weight", "0"))

    sessions_done = st.selectbox(
        "Sessions Done",
        list(range(1,31))
    )

    progress_type = st.selectbox(
        "Progress Type",
        ["Strength Gain",
         "Weight Loss",
         "Mobility",
         "Endurance",
         "General"]
    )

    performance = st.slider(
        "Performance Score",1,10)

    notes = st.text_area("Notes")

    if st.button("Save Session"):

        new_row = {
            date_col: date.today(),
            client_col: client,
            trainer_col: trainer,
            weight_col: weight,
            "session_done": sessions_done,
            "progress_type": progress_type,
            perf_col: performance,
            "notes": notes
        }

        session_log.loc[len(session_log)] = new_row

        with pd.ExcelWriter(
            CLIENT_FILE,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace"
        ) as writer:

            session_log.to_excel(
                writer,
                sheet_name="SESSION_LOG",
                index=False
            )

        st.cache_data.clear()
        st.success("✅ Session Saved")

        st.rerun()
