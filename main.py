import streamlit as st

# ✅ Must be the FIRST Streamlit command
st.set_page_config(page_title="📊 Gibud User Dashboard", layout="wide")

import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import time

# -----------------------------
# 🔐 Firebase Initialization
# -----------------------------
def initialize_firebase():
    try:
        cred = credentials.Certificate({
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"]
        })

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"❌ Firebase initialization failed: {e}")
        st.stop()

# Initialize Firestore
db = initialize_firebase()
st.success("✅ Firebase initialized successfully!")

# -----------------------------
# 🧠 Risk Interpretation Logic
# -----------------------------
def interpret_score(score):
    if score is None:
        return "Unknown"
    if score <= 20:
        return "Low Risk"
    elif score <= 35:
        return "Moderate Risk"
    elif score <= 39:
        return "High Risk"
    else:
        return "Very High Risk"

# -----------------------------
# 📊 Fetch User Data
# -----------------------------
@st.cache_data(ttl=60)
def fetch_user_data():
    """Fetch user data from Firestore and return a DataFrame."""
    try:
        users_ref = db.collection("Users")
        survey_ref = db.collection("Surveys")
        docs = users_ref.stream()
        user_data = []

        for doc in docs:
            data = doc.to_dict()
            if data:
                user_id = data.get("id")  # 👈 used to match with Surveys
                raw_timestamp = data.get("createdAt")

                # ✅ Normalize Firestore/CSV timestamps safely
                if raw_timestamp:
                    try:
                        raw_timestamp = pd.to_datetime(raw_timestamp, errors="coerce")
                    except Exception:
                        raw_timestamp = pd.NaT
                else:
                    raw_timestamp = pd.NaT

                # Fetch related survey (assume most recent one)
                survey_docs = survey_ref.where("id", "==", user_id).stream()
                question_score = None
                for survey in survey_docs:
                    survey_data = survey.to_dict()
                    question_score = survey_data.get("questionScore")
                    break  # Only fetch the first one found

                risk_level = interpret_score(question_score)

                user_data.append({
                    "Name": data.get("name"),
                    "Email": data.get("email"),
                    "Phone": data.get("phone"),
                    "Age": data.get("age"),
                    "Gender": data.get("gender"),
                    "Height": data.get("height"),
                    "Weight": data.get("weight"),
                    "Payment Status": data.get("gutTestPaymentStatus"),
                    "Question Score": question_score,
                    "Risk Level": risk_level,
                    "Raw Timestamp": raw_timestamp,
                    "Timestamp": raw_timestamp.strftime('%d-%m-%Y %H:%M:%S') if pd.notnull(raw_timestamp) else "N/A"
                })

        df = pd.DataFrame(user_data)
        return df
    except Exception as e:
        st.error(f"❌ Failed to fetch user data: {e}")
        return pd.DataFrame()

# -----------------------------
# 🎯 Streamlit UI
# -----------------------------
st.title("📊 Gibud User Dashboard")

# ✅ Auto-Refresh Toggle
auto_refresh = st.checkbox("🔄 Enable Auto-Refresh Every 10 Seconds", value=False)

# ✅ Display Data
df = fetch_user_data()

if df.empty:
    st.info("ℹ️ No user data found.")
else:
    st.write("### 📋 Complete User Data")
    st.dataframe(df.drop(columns=["Raw Timestamp"]))  # Hide raw timestamp from full view

    # 🛠️ Sort and Filter Section
    with st.expander("🔍 **Sort & Filter Data**"):
        sort_column = st.selectbox("📊 Select Column to Sort/Filter By", [col for col in df.columns if col != "Raw Timestamp"])

        if sort_column == "Payment Status":
            payment_filter = st.radio("🛡️ Filter by Payment Status", ["All", "True", "False"])
            if payment_filter == "True":
                df = df[df["Payment Status"] == True]
            elif payment_filter == "False":
                df = df[df["Payment Status"] == False]

        elif sort_column == "Gender":
            gender_filter = st.radio("🚻 Filter by Gender", ["All", "Male", "Female"])
            if gender_filter != "All":
                df = df[df["Gender"] == gender_filter]

        elif sort_column in ["Age", "Height", "Weight", "Timestamp", "Question Score"]:
            sort_order = st.radio("🔄 Sort Order", ["Ascending", "Descending"])
            ascending = (sort_order == "Ascending")
            if sort_column == "Timestamp":
                # ✅ Safe sort with NaT values at the bottom
                df = df.sort_values(by="Raw Timestamp", ascending=ascending, na_position="last")
            else:
                df = df.sort_values(by=sort_column, ascending=ascending)

        else:
            sort_order = st.radio("🔄 Sort Order", ["Ascending", "Descending"])
            ascending = (sort_order == "Ascending")
            df = df.sort_values(by=sort_column, ascending=ascending)

        df.reset_index(drop=True, inplace=True)
        st.write("### ✅ Filtered/Sorted Data")
        st.dataframe(df.drop(columns=["Raw Timestamp"]))

# 🔄 Auto-Refresh Logic
if auto_refresh:
    with st.spinner("🔄 Refreshing data..."):
        time.sleep(10)
        st.experimental_rerun()
