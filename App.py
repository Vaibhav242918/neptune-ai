import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="Neptune AI - Web Edition", layout="wide")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("neptune_users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            gmail TEXT,
            mobile TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def register_user(username, password, gmail, mobile):
    try:
        conn = sqlite3.connect("neptune_users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, gmail, mobile) VALUES (?, ?, ?, ?)",
                       (username, password, gmail, mobile))
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists. Try another."

def login_user(identifier, password):
    conn = sqlite3.connect("neptune_users.db")
    cursor = conn.cursor()
    # Allow login via username, gmail, or mobile
    cursor.execute('''
        SELECT * FROM users 
        WHERE (username = ? OR gmail = ? OR mobile = ?) AND password = ?
    ''', (identifier, identifier, identifier, password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect("neptune_users.db")
    df_users = pd.read_sql_query("SELECT id, username, gmail, mobile FROM users", conn)
    conn.close()
    return df_users

# --- SESSION STATE MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- MAIN APP LAYOUT ---
st.title("🌌 Neptune AI - Executive Data Science & ML Hub")

if not st.session_state.logged_in:
    st.markdown("### Secure Access Portal")
    choice = st.sidebar.selectbox("Navigation", ["Sign In", "Sign Up"])
    
    if choice == "Sign Up":
        st.subheader("Create a New Account")
        with st.form("signup_form"):
            new_user = st.text_input("Username")
            new_gmail = st.text_input("Gmail Address")
            new_mobile = st.text_input("Mobile Number")
            new_pass = st.text_input("Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_user and new_gmail and new_mobile and new_pass:
                    success, msg = register_user(new_user, new_pass, new_gmail, new_mobile)
                    if success:
                        st.success(msg + " Please switch to Sign In.")
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in all fields.")
                    
    elif choice == "Sign In":
        st.subheader("Sign In to Your Account")
        with st.form("signin_form"):
            identifier = st.text_input("Username, Gmail, or Mobile Number")
            password = st.text_input("Password", type="password")
            submit_signin = st.form_submit_button("Sign In")
            
            if submit_signin:
                user = login_user(identifier, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user[1] # username column
                    st.success(f"Welcome back, {st.session_state.username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please check your details.")

else:
    # --- LOGGED IN USER INTERFACE ---
    st.sidebar.success(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.header("📁 Data Source Selection")
    data_option = st.sidebar.radio("Choose Dataset Source", ["Use Built-in Sample Dataset", "Upload Custom CSV"])

    df = None
    if data_option == "Use Built-in Sample Dataset":
        data = {
            'Hours_Studied': [7, 4, 8, 3, 7, 3, 7, 5, 4, 2, 5, 6, 6, 1, 4, 5, 7, 3, 2, 6],
            'Previous_Scores': [99, 82, 51, 52, 75, 78, 73, 45, 79, 89, 80, 72, 75, 37, 88, 74, 93, 43, 52, 91],
            'Sleep_Hours': [9, 4, 7, 3, 7, 7, 5, 9, 9, 4, 7, 8, 6, 8, 4, 6, 8, 9, 6, 6],
            'Sample_Question_Papers_Practiced': [1, 2, 2, 2, 5, 2, 6, 2, 2, 0, 2, 3, 4, 1, 3, 1, 3, 3, 2, 3],
            'Performance_Index': [91.0, 65.0, 45.0, 36.0, 66.0, 61.0, 64.0, 48.0, 60.0, 62.0, 64.0, 63.0, 64.0, 34.0, 68.0, 60.0, 85.0, 40.0, 43.0, 78.0]
        }
        df = pd.DataFrame(data)
    else:
        uploaded_file = st.sidebar.file_uploader("Upload custom CSV", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

    # Tabs configuration
    tab_list = ["📊 Data Preview & AutoEDA", "⚡ AutoML Benchmark Arena", "📈 Visualizer & Heatmap"]
    
    # Check if admin is logged in
    is_admin = (st.session_state.username.strip().lower() == "vaibhav2429")
    if is_admin:
        tab_list.append("🛠️ Admin Console")
        
    tabs = st.tabs(tab_list)
    
    with tabs[0]:
        if df is not None:
            st.subheader("Dataset Structure Matrix")
            st.write(f"Total Rows: {df.shape[0]} | Total Columns: {df.shape[1]}")
            st.dataframe(df.head(10))
            st.subheader("Statistical Summary")
            st.write(df.describe())
        else:
            st.info("Please select or upload a dataset.")
            
    with tabs[1]:
        if df is not None:
            st.subheader("AutoML Leaderboard Arena")
            numeric_df = df.select_dtypes(include=[np.number]).dropna()
            if not numeric_df.empty:
                target_col = st.selectbox("Select Target Column", options=numeric_df.columns)
                if st.button("Run AutoML Benchmark"):
                    with st.spinner("Training models..."):
                        X = numeric_df.drop(columns=[target_col])
                        y = numeric_df[target_col]
                        if y.nunique() > 10:
                            y = (y > y.median()).astype(int)
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                        models = {
                            "Logistic Regression": LogisticRegression(max_iter=500),
                            "Random Forest": RandomForestClassifier(n_estimators=50, random_state=42),
                            "Gradient Boosting": GradientBoostingClassifier(random_state=42)
                        }
                        results = {}
                        for name, model in models.items():
                            model.fit(X_train, y_train)
                            preds = model.predict(X_test)
                            results[name] = accuracy_score(y_test, preds)
                        results_df = pd.DataFrame(list(results.items()), columns=["Model", "Accuracy"])
                        st.table(results_df)
                        best_model = max(results, key=results.get)
                        st.success(f"Optimal Model: **{best_model}**")
        else:
            st.info("Please load a dataset first.")
            
    with tabs[2]:
        if df is not None:
            st.subheader("Feature Correlation Heatmap")
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
                st.pyplot(fig)
        else:
            st.info("Please load a dataset first.")
            
    if is_admin:
        with tabs[3]:
            st.subheader("🔒 Admin Console - User Information Database")
            st.write("Welcome, Admin Vaibhav! Here is the complete list of registered users:")
            users_df = get_all_users()
            st.dataframe(users_df, use_container_width=True)