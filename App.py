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
st.markdown("Welcome to the web deployment edition of Neptune! Upload a CSV dataset below to begin exploration, automated EDA, and AutoML benchmarking.")

uploaded_file = st.file_uploader("Upload your CSV dataset", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("Dataset successfully loaded into Neptune's web core!")
    
    # Tabs for features
    tab1, tab2, tab3 = st.tabs(["📊 Data Preview & AutoEDA", "⚡ AutoML Benchmark Arena", "📈 Visualizer & Heatmap"])
    
    with tab1:
        st.subheader("Dataset Structure")
        st.write(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")
        st.dataframe(df.head())
        
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
            st.warning("Please upload a dataset containing numeric columns.")
            
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
    st.info("Awaiting CSV dataset upload to ignite Neptune's web core...")