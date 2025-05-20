import os
import json
import time

import firebase_admin
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

# -----------------------------
# 🚀 Firebase Initialization
# -----------------------------
def initialize_firebase():
    """Initializes Firebase connection using credentials from environment variables."""
    firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS")

    if not firebase_credentials_json:
        st.error("⚠️ Firebase credentials not found. Please set the 'FIREBASE_CREDENTIALS' variable in your .env file.")
        st.stop()

    try:
        creds_dict = json.loads(firebase_credentials_json)
        cred = credentials.Certificate(creds_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"❌ Failed to initialize Firebase: {e}")
        st.stop()

# Initialize Firestore client
db = initialize_firebase()
st.success("✅ Firebase initialized successfully!")

# -----------------------------
# 📊 Fetch User Data
# -----------------------------
@st.cache_data(ttl=60)
def fetch_user_data():
    """Fetch user data from Firestore and return a DataFrame."""
    try:
        users_ref = db.collection("Users")
        docs = users_ref.stream()
        user_data = []

        for doc in docs:
            data = doc.to_dict()
            if data:
                raw_timestamp = pd.to_datetime(data.get("createdAt"), errors='coerce')
                user_data.append({
                    "Name": data.get("name"),
                    "Email": data.get("email"),
                    "Phone": data.get("phone"),
                    "Age": data.get("age"),
                    "Gender": data.get("gender"),
                    "Height": data.get("height"),
                    "Weight": data.get("weight"),
                    "Payment Status": data.get("gutTestPaymentStatus"),
                    "Raw Timestamp": raw_timestamp,  # Keep for sorting
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
        else:
            sort_order = st.radio("🔄 Sort Order", ["Ascending", "Descending"])
            ascending = (sort_order == "Ascending")

            # Special case for Timestamp
            if sort_column == "Timestamp":
                df = df.sort_values(by="Raw Timestamp", ascending=ascending)
            else:
                df = df.sort_values(by=sort_column, ascending=ascending)

        df.reset_index(drop=True, inplace=True)
        st.write("### ✅ Filtered/Sorted Data")
        st.dataframe(df.drop(columns=["Raw Timestamp"]))

# 🔄 Auto-Refresh Logic
if auto_refresh:
    with st.spinner("🔄 Refreshing data..."):
        time.sleep(10)
        st.experimental_rerun()
