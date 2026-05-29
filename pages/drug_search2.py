import streamlit as st
import pandas as pd


DRUG_TARGET_PATH = "data/DRUG-GENE.csv"
PROTEIN_DISEASE_PATH = "data/protein_to_disease.csv"


st.set_page_config(
    page_title="Drug to Cancer Proteome Search",
    layout="wide"
)


@st.cache_data
def load_drug_data():
    df = pd.read_csv(DRUG_TARGET_PATH)

    df.columns = df.columns.str.strip()

    # Clean important ID columns
    df["UNIPROT_ID"] = df["UNIPROT_ID"].astype(str).str.strip()
    df["DRUG_NAME"] = df["DRUG_NAME"].astype(str).str.strip()
    df["GENE_SYMBOL"] = df["GENE_SYMBOL"].astype(str).str.strip()

    # Remove bad rows
    df = df[
        df["UNIPROT_ID"].notna()
        & (df["UNIPROT_ID"] != "")
        & (df["UNIPROT_ID"].str.lower() != "nan")
    ]

    return df


@st.cache_data
def load_protein_disease_data():
    df = pd.read_csv(PROTEIN_DISEASE_PATH)

    df.columns = df.columns.str.strip()

    # Clean UniProt entry column
    df["Entry"] = df["Entry"].astype(str).str.strip()

    return df


@st.cache_data
def merge_data(drug_df, protein_df):
    merged = drug_df.merge(
        protein_df,
        left_on="UNIPROT_ID",
        right_on="Entry",
        how="left"
    )

    return merged


def get_proteome_columns(protein_df):
    """
    Everything after the basic protein info columns is treated as a cancer proteome/source column.
    """
    metadata_cols = ["Entry", "Protein name", "Protein description", "Gene"]

    proteome_cols = [
        col for col in protein_df.columns
        if col not in metadata_cols
    ]

    return proteome_cols


def clean_detection_value(value):
    """
    Convert values like 1.0, 1, '1.0' into detected.
    Empty cells, NaN, 0, and blanks are not detected.
    """
    if pd.isna(value):
        return 0

    value_str = str(value).strip()

    if value_str in ["", "nan", "NaN", "0", "0.0"]:
        return 0

    try:
        return 1 if float(value_str) > 0 else 0
    except ValueError:
        return 0


def split_associated_unassociated(row, proteome_cols):
    associated = []
    unassociated = []

    for col in proteome_cols:
        detected = clean_detection_value(row.get(col))

        if detected == 1:
            associated.append(col)
        else:
            unassociated.append(col)

    return associated, unassociated



def main():
    st.title("Drug to Cancer Proteome Search")

    drug_df = load_drug_data()
    protein_df = load_protein_disease_data()
    merged_df = merge_data(drug_df, protein_df)

    proteome_cols = get_proteome_columns(protein_df)

    st.write(
        "Search for a drug to view its target UniProt ID and whether that protein "
        "was detected across cancer proteomic datasets."
    )

    search_query = st.text_input(
        "Search drug name",
        placeholder="Search a drug such as Amitriptyline, Clomipramine, Axitinib..."
    )

    if search_query.strip() == "":
        st.info("Enter a drug name to begin.")
        return

    drug_matches = merged_df[
        merged_df["DRUG_NAME"].str.contains(search_query, case=False, na=False)
    ].copy()

    if drug_matches.empty:
        st.warning("No matching drug found.")
        return

    st.subheader(f"Search results for: {search_query}")

    # Show matching drugs first
    st.markdown("### Matching Drug-Target Results")

    target_display_df = drug_matches[
        [
            "DRUG_NAME",
            "GENE_SYMBOL",
            "UNIPROT_ID",
            "Datasource",
            "PUBCHEM_CID",
            "HGNC_ID",
            "ENSEMBL_ID",
            "ENTREZ_ID"
        ]
    ].copy()

    target_display_df = target_display_df.rename(columns={
        "DRUG_NAME": "Drug Name",
        "GENE_SYMBOL": "Gene Symbol",
        "UNIPROT_ID": "UniProt ID",
        "Datasource": "Datasource",
        "PUBCHEM_CID": "PubChem CID",
        "HGNC_ID": "HGNC ID",
        "ENSEMBL_ID": "Ensembl ID",
        "ENTREZ_ID": "Entrez ID"
    })

    selected_table = st.dataframe(
        target_display_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )

    selected_rows = selected_table.selection.rows

    if not selected_rows:
        st.info("Select one target row from the table to view cancer proteome associations.")
        return

    selected_index = selected_rows[0]
    selected_row = drug_matches.iloc[selected_index]

    st.markdown("### Drug and Target Information")

    info_cols = st.columns(3)

    with info_cols[0]:
        st.metric("Drug", selected_row.get("DRUG_NAME", "Not available"))

    with info_cols[1]:
        st.metric("Gene Symbol", selected_row.get("GENE_SYMBOL", "Not available"))

    with info_cols[2]:
        st.metric("UniProt ID", selected_row.get("UNIPROT_ID", "Not available"))

    detail_df = pd.DataFrame({
        "Field": [
            "PubChem CID",
            "Datasource",
            "Drug URL",
            "Gene URL",
            "HGNC ID",
            "Ensembl ID",
            "Entrez ID",
            "Protein Name",
            "Protein Description"
        ],
        "Value": [
            selected_row.get("PUBCHEM_CID", "Not available"),
            selected_row.get("Datasource", "Not available"),
            selected_row.get("DRUGURL", "Not available"),
            selected_row.get("GENEURL", "Not available"),
            selected_row.get("HGNC_ID", "Not available"),
            selected_row.get("ENSEMBL_ID", "Not available"),
            selected_row.get("ENTREZ_ID", "Not available"),
            selected_row.get("Protein name", "Not available"),
            selected_row.get("Protein description", "Not available")
        ]
    })

    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    if pd.isna(selected_row.get("Entry")):
        st.warning(
            "This target UniProt ID was not found in the cancer proteome dataset."
        )
        return

    associated, unassociated = split_associated_unassociated(
        selected_row,
        proteome_cols
    )

    st.markdown("### Cancer Proteome Summary")

    summary_cols = st.columns(2)

    with summary_cols[0]:
        st.metric("Associated / Detected Datasets", len(associated))

    with summary_cols[1]:
        st.metric("Unassociated / Not Detected Datasets", len(unassociated))

    st.markdown("### Associated Datasets")

    if associated:
        associated_df = pd.DataFrame({
            "Associated Datasets": associated
        })
        st.dataframe(
            associated_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No associated cancer proteomes found for this target.")

    st.markdown("### Unassociated Datasets")

    if unassociated:
        unassociated_df = pd.DataFrame({
            "Unassociated Datasets": unassociated
        })
        st.dataframe(
            unassociated_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("This target was detected in every listed cancer proteome dataset.")



if __name__ == "__main__":
    main()