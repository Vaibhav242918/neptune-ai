import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="Neptune AI - Web Edition", layout="wide")

st.title("🌌 Neptune AI - Executive Data Science & ML Hub")
st.markdown("Welcome to the web deployment edition of Neptune! Explore automated EDA, correlation heatmaps, and AutoML benchmarking below.")

# Sidebar for controls and data selection
st.sidebar.header("📁 Data Source Selection")
data_option = st.sidebar.radio("Choose Dataset Source", ["Use Built-in Sample Dataset", "Upload Custom CSV"])

df = None

if data_option == "Use Built-in Sample Dataset":
    # Built-in default sample data so you never have to upload manually
    data = {
        'Hours_Studied': [7, 4, 8, 3, 7, 3, 7, 5, 4, 2, 5, 6, 6, 1, 4, 5, 7, 3, 2, 6],
        'Previous_Scores': [99, 82, 51, 52, 75, 78, 73, 45, 79, 89, 80, 72, 75, 37, 88, 74, 93, 43, 52, 91],
        'Sleep_Hours': [9, 4, 7, 3, 7, 7, 5, 9, 9, 4, 7, 8, 6, 8, 4, 6, 8, 9, 6, 6],
        'Sample_Question_Papers_Practiced': [1, 2, 2, 2, 5, 2, 6, 2, 2, 0, 2, 3, 4, 1, 3, 1, 3, 3, 2, 3],
        'Performance_Index': [91.0, 65.0, 45.0, 36.0, 66.0, 61.0, 64.0, 48.0, 60.0, 62.0, 64.0, 63.0, 64.0, 34.0, 68.0, 60.0, 85.0, 40.0, 43.0, 78.0]
    }
    df = pd.DataFrame(data)
    st.sidebar.success("Loaded built-in sample dataset successfully!")
else:
    uploaded_file = st.sidebar.file_uploader("Upload your custom CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("Custom CSV uploaded successfully!")

if df is not None:
    # Tabs for features
    tab1, tab2, tab3 = st.tabs(["📊 Data Preview & AutoEDA", "⚡ AutoML Benchmark Arena", "📈 Visualizer & Heatmap"])
    
    with tab1:
        st.subheader("Dataset Structure Matrix")
        st.write(f"Total Rows: {df.shape[0]} | Total Columns: {df.shape[1]}")
        st.dataframe(df.head(10))
        
        st.subheader("Statistical Summary")
        st.write(df.describe())
        
    with tab2:
        st.subheader("AutoML Leaderboard Arena")
        numeric_df = df.select_dtypes(include=[np.number]).dropna()
        if not numeric_df.empty:
            target_col = st.selectbox("Select Target Column for Classification", options=numeric_df.columns)
            if st.button("Run AutoML Benchmark"):
                with st.spinner("Training models across the arena..."):
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
                        acc = accuracy_score(y_test, preds)
                        results[name] = acc
                        
                    results_df = pd.DataFrame(list(results.items()), columns=["Model", "Accuracy"])
                    st.table(results_df)
                    best_model = max(results, key=results.get)
                    st.success(f"Optimal Model Selected: **{best_model}** with highest accuracy!")
        else:
            st.warning("Selected dataset does not contain valid numeric columns.")
            
    with tab3:
        st.subheader("Feature Correlation Heatmap")
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
            st.pyplot(fig)
        else:
            st.warning("No numeric columns available for heatmap generation.")
else:
    st.info("Please select or upload a dataset using the sidebar to ignite Neptune's web core.")