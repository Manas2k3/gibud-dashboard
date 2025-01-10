import json
import os
import time

import firebase_admin
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

# -----------------------------
# 🔑 Environment Setup
# -----------------------------
load_dotenv()


# -----------------------------
# 🚀 Firebase Initialization
# -----------------------------
def initialize_firebase():
    """Initializes Firebase connection."""
    firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')

    if not firebase_credentials:
        st.error("⚠️ Firebase credentials not found in environment variables. Please set 'FIREBASE_CREDENTIALS'.")
        st.stop()

    try:
        cred = credentials.Certificate(json.loads(firebase_credentials))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"❌ Firebase initialization failed: {e}")
        st.stop()


# Initialize Firestore Database
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
        user_data = [
            {
                "Name": data.get("name"),
                "Email": data.get("email"),
                "Phone": data.get("phone"),
                "Age": data.get("age"),
                "Gender": data.get("gender"),
                "Height": data.get("height"),
                "Weight": data.get("weight"),
                "Payment Status": data.get("gutTestPaymentStatus"),
                "Timestamp": pd.to_datetime(data.get("createdAt"), errors='coerce').strftime('%d-%m-%Y %H:%M:%S')
                if data.get("createdAt") else "N/A"
            }
            for doc in docs if (data := doc.to_dict())
        ]
        return pd.DataFrame(user_data) if user_data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Failed to fetch user data: {e}")
        return pd.DataFrame()


# -----------------------------
# 🎯 Streamlit UI
# -----------------------------
st.title("📊 Gibud User Dashboard")

# ✅ Auto-Refresh Toggle
auto_refresh = st.checkbox("🔄 Enable Auto-Refresh Every 10 Seconds", value=False)

# ✅ Fetch and Display Data
df = fetch_user_data()

if df.empty:
    st.info("ℹ️ No user data found.")
else:
    st.write("### 📋 Complete User Data")
    st.dataframe(df)

    # 🛠️ Sort and Filter
    with st.expander("🔍 **Sort & Filter Data**"):
        sort_column = st.selectbox("📊 Select Column to Sort/Filter By", df.columns)
        if sort_column == "Payment Status":
            payment_filter = st.radio("🛡️ Filter by Payment Status", ["All", "True", "False"])
            if payment_filter == "True":
                df = df[df["Payment Status"] == True]
            elif payment_filter == "False":
                df = df[df["Payment Status"] == False]
        else:
            sort_order = st.radio("🔄 Sort Order", ["Ascending", "Descending"])
            df = df.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))

        df.reset_index(drop=True, inplace=True)

        st.write("### ✅ Filtered/Sorted Data")
        st.dataframe(df)

# 🔄 Auto-Refresh Logic
if auto_refresh:
    with st.spinner("🔄 Refreshing data..."):
        time.sleep(10)
        st.experimental_rerun()
