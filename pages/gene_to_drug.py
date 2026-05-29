import streamlit as st
import pandas as pd


DATA_PATH = "data/DRUG-GENE.csv"


@st.cache_data
def load_gene_drug_data():
    df = pd.read_csv(DATA_PATH)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Clean important text columns
    text_columns = [
        "DRUG_NAME",
        "Datasource",
        "GENE_SYMBOL",
        "UNIPROT_ID",
        "HGNC_ID",
        "ENSEMBL_ID",
        "ENTREZ_ID",
        "GENEURL",
        "DRUGURL"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df


def show_gene_to_drug_page():
    st.title("Gene to Drug Search")

    st.write(
        "Search for a gene symbol to find all drugs associated with that gene."
    )

    df = load_gene_drug_data()

    required_columns = [
        "PUBCHEM_CID",
        "DRUG_NAME",
        "Datasource",
        "GENEURL",
        "DRUGURL",
        "UNIPROT_ID",
        "HGNC_ID",
        "ENSEMBL_ID",
        "ENTREZ_ID",
        "GENE_SYMBOL"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return

    # Main gene search box
    gene_query = st.text_input(
        "Enter a gene symbol",
        placeholder="Example: HTR2C, EGFR, TP53, PARP1"
    )

    if gene_query.strip() == "":
        st.info("Enter a gene symbol above to begin searching.")
        return

    gene_query_clean = gene_query.strip().upper()

    # Match gene symbol exactly, ignoring capitalization
    results = df[
        df["GENE_SYMBOL"].str.upper() == gene_query_clean
    ].copy()

    if results.empty:
        st.warning(f"No drugs found for gene symbol: {gene_query_clean}")
        return

    # Remove duplicate drug-gene associations
    results = results.drop_duplicates(
        subset=[
            "PUBCHEM_CID",
            "DRUG_NAME",
            "Datasource",
            "UNIPROT_ID",
            "GENE_SYMBOL"
        ]
    )

    results = results.sort_values(by=["DRUG_NAME", "Datasource"])

    st.success(
        f"Found {results['DRUG_NAME'].nunique()} associated drug(s) for {gene_query_clean}."
    )

    st.metric("Associated Drugs", results["DRUG_NAME"].nunique())

    st.subheader("Associated Drug Results")

    # Secondary drug search bar
    drug_filter = st.text_input(
        "Search within associated drugs",
        placeholder="Example: Amitriptyline, Clomipramine, Fluoxetine"
    )

    filtered_results = results.copy()

    if drug_filter.strip() != "":
        drug_filter_clean = drug_filter.strip().lower()

        filtered_results = filtered_results[
            filtered_results["DRUG_NAME"]
            .str.lower()
            .str.contains(drug_filter_clean, na=False)
        ]

    if filtered_results.empty:
        st.warning("No associated drugs match your current drug search.")
        return

    st.caption(
        f"Showing {filtered_results['DRUG_NAME'].nunique()} drug(s) from "
        f"{len(filtered_results)} drug-gene association(s)."
    )

    display_columns = [
        "DRUG_NAME",
        "PUBCHEM_CID",
        "Datasource",
        "GENE_SYMBOL",
        "UNIPROT_ID",
        "HGNC_ID",
        "ENSEMBL_ID",
        "ENTREZ_ID",
        "DRUGURL",
        "GENEURL"
    ]

    display_df = filtered_results[display_columns].copy()

    display_df = display_df.rename(columns={
        "DRUG_NAME": "Drug Name",
        "PUBCHEM_CID": "PubChem CID",
        "Datasource": "Data Source",
        "GENE_SYMBOL": "Gene Symbol",
        "UNIPROT_ID": "UniProt ID",
        "HGNC_ID": "HGNC ID",
        "ENSEMBL_ID": "Ensembl ID",
        "ENTREZ_ID": "Entrez ID",
        "DRUGURL": "Drug URL",
        "GENEURL": "Gene URL"
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Drug URL": st.column_config.LinkColumn("Drug URL"),
            "Gene URL": st.column_config.LinkColumn("Gene URL")
        }
    )

    csv = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered results as CSV",
        data=csv,
        file_name=f"{gene_query_clean}_associated_drugs.csv",
        mime="text/csv"
    )


show_gene_to_drug_page()