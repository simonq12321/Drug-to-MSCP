import streamlit as st
from styles import apply_global_styles

st.set_page_config(
    page_title="Mass Spectrometric Detected Cancer Proteins",
    page_icon="",
    layout="wide"
)

apply_global_styles()

pages = {
    "Navigation": [
        st.Page("home.py", title="Home Page"),
        st.Page("pages/drug_search2.py", title="Drug -> Dataset Search"),
        st.Page("pages/gene_to_drug.py", title="Gene -> Drug Search"),
        st.Page("pages/protein_to_disease.py", title="Protein -> Dataset Search"),
    ]
}

pg = st.navigation(pages)
pg.run()