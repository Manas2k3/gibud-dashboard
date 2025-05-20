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
