import streamlit as st
from pathlib import Path
from styles import apply_global_styles

apply_global_styles()

BASE_DIR = Path(__file__).resolve().parent
BANNER_PATH = BASE_DIR / "assets" / "drug_banner2.png"

if BANNER_PATH.exists():
    st.markdown('<div class="banner-container">', unsafe_allow_html=True)
    st.image(str(BANNER_PATH), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("Banner image not found. Make sure it is saved as assets/drug_banner2.png")

st.markdown('<div class="content-container">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">Welcome to the Drug Target Lookup Database</div>
        <div class="section-text">
            This tool allows users to search for a drug, view its associated biological targets,
            connect those targets to UniProt protein annotations, and explore possible disease
            associations using proteomics datasets.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Drug Search</div>
            <div class="section-text">
                Search drugs such as Axitinib, Veliparib, or Nintedanib and view target information.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">UniProt Lookup</div>
            <div class="section-text">
                Match drug targets to UniProt entries and review protein-level annotations.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Disease Mapping</div>
            <div class="section-text">
                Connect proteins to disease datasets and view association tables.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)