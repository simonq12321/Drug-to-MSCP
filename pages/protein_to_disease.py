import streamlit as st
import pandas as pd
import re
from styles import apply_global_styles

apply_global_styles()


# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_protein_disease_data():
    df = pd.read_csv("data/protein_to_disease.csv")
    df.columns = df.columns.str.strip()
    return df


df = load_protein_disease_data()


# -----------------------------
# Column Setup
# -----------------------------
METADATA_COLS = [
    "Entry",
    "Protein name",
    "Protein description",
    "Gene"
]

DATA_SOURCE_COLS = [
    col for col in df.columns
    if col not in METADATA_COLS
]


# -----------------------------
# Optional Display Name Mapping
# -----------------------------
DATA_SOURCE_TO_DISEASE = {
    "LSCC-D": "Lung Squamous Cell Carcinoma",
    "GBM-D": "Glioblastoma",
    "OV-C": "Ovarian Cancer",
    "PDAC-D": "Pancreatic Ductal Adenocarcinoma",
    "HNSCC-D": "Head and Neck Squamous Cell Carcinoma",
    "CCRCC-D": "Clear Cell Renal Cell Carcinoma",
    "COAD-C": "Colon Adenocarcinoma",
    "LUAD-D": "Lung Adenocarcinoma",
    "UCEC-D": "Uterine Corpus Endometrial Carcinoma",
    "BRCA-C": "Breast Cancer",
    "RCC-C": "Renal Cell Carcinoma",
    "SEER-plasma": "SEER Plasma",
    "SEER-blood": "SEER Blood",
    "PDAC-T": "Pancreatic Tumor",
    "A549": "A549 Cell Line",
    "COLO205": "COLO205 Cell Line",
    "CCRF_CEM": "CCRF-CEM Cell Line",
    "NCI-H23": "NCI-H23 Cell Line",
    "NCI-H226": "NCI-H226 Cell Line",
    "RPMI8226": "RPMI8226 Cell Line",
    "T47D": "T47D Cell Line",
    "NCI-7": "NCI-7 Cell Line",
    "GC-DIA": "Gastric Cancer DIA",
    "GC-DDA": "Gastric Cancer DDA",
    "PRAD-DIA": "Prostate Cancer DIA",
    "PRAD-DDA": "Prostate Cancer DDA",
    "MC-Blood": "MC Blood",
    "CCDI": "CCDI",
    "MCOF-EDRN": "MCOF EDRN",
    "MCOF-PCDC": "MCOF PCDC",
    "MCOF-AL": "MCOF AL"
}


# -----------------------------
# Helper Functions
# -----------------------------
def normalize_text(text):
    if pd.isna(text):
        return ""

    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def is_associated(value):
    """
    Treats 1, 1.0, and '1.0' as positive associations.
    Blank cells and NaN are treated as not associated.
    """
    if pd.isna(value):
        return False

    value = str(value).strip().lower()
    return value in ["1", "1.0"]


def clean_display_value(value):
    if pd.isna(value):
        return "Unknown"
    return str(value)


def source_display_name(col):
    return DATA_SOURCE_TO_DISEASE.get(col, col)


# -----------------------------
# Page Content
# -----------------------------
st.title("Protein to Dataset Search")

st.write(
    "Search your protein-to-dataset spreadsheet by protein entry, protein name, protein description, or gene."
)

query = st.text_input(
    "Search protein-to-dataset",
    placeholder="Examples: A1BG_HUMAN, Alpha-1B-glycoprotein, A1BG, P04217"
)

show_unassociated = st.checkbox(
    "Show unassociated disease/data sources",
    value=False
)


# -----------------------------
# Search Logic
# -----------------------------
if query:
    query_clean = normalize_text(query)

    search_df = df[METADATA_COLS].copy()

    for col in METADATA_COLS:
        search_df[col] = search_df[col].apply(normalize_text)

    mask = search_df.apply(
        lambda row: any(query_clean in cell for cell in row),
        axis=1
    )

    results = df[mask].copy()

    if results.empty:
        st.warning("No matching protein found.")

    else:
        st.success(f"{len(results)} matching result(s) found.")

        for _, row in results.iterrows():
            entry = clean_display_value(row["Entry"])
            protein_name = clean_display_value(row["Protein name"])
            protein_description = clean_display_value(row["Protein description"])
            gene = clean_display_value(row["Gene"])

            associated_sources = [
                col for col in DATA_SOURCE_COLS
                if is_associated(row[col])
            ]

            unassociated_sources = [
                col for col in DATA_SOURCE_COLS
                if not is_associated(row[col])
            ]

            associated_names = sorted(
                set(source_display_name(col) for col in associated_sources)
            )

            unassociated_names = sorted(
                set(source_display_name(col) for col in unassociated_sources)
            )

            st.markdown(
                f"""
                <div class="protein-card">
                    <div class="protein-title">{protein_name}</div>
                    <div class="protein-meta"><strong>Gene:</strong> {gene}</div>
                    <div class="protein-meta"><strong>Entry:</strong> {entry}</div>
                    <div class="protein-description">{protein_description}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            result_col1, result_col2 = st.columns([1, 1])

            with result_col1:
                st.markdown("**Associated disease/data sources**")

                if associated_names:
                    st.markdown(
                        "<ul class='compact-list'>"
                        + "".join([f"<li>{name}</li>" for name in associated_names])
                        + "</ul>",
                        unsafe_allow_html=True
                    )
                else:
                    st.write("No associated diseases found.")

            if show_unassociated:
                with result_col2:
                    st.markdown("**Unassociated disease/data sources**")

                    if unassociated_names:
                        st.markdown(
                            "<ul class='compact-list'>"
                            + "".join([f"<li>{name}</li>" for name in unassociated_names])
                            + "</ul>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.write("No unassociated sources found.")

            st.divider()

else:
    st.info("Enter a protein entry, protein name, protein description, or gene to begin.")