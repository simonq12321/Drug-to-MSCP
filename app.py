import streamlit as st

st.set_page_config(
    page_title="Drug Database",
    layout="wide"
)

st.title("Drug Database")

st.write("""
Welcome to the drug database.

Use the sidebar to navigate between pages.
""")

st.markdown("""
### Available Pages

- **Drug Search**: Search a drug, select a target, view UniProt results, and see disease associations.
- **Reverse Search**: Search a disease and find drugs connected to disease-associated proteins.
""")