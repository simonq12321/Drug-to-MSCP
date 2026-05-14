import streamlit as st
import pandas as pd
import requests
import re
from styles import apply_global_styles

# -----------------------------
# Global Styles
# -----------------------------
apply_global_styles()

st.markdown('<div class="content-container">', unsafe_allow_html=True)

# -----------------------------
# Page Header
# -----------------------------
st.title("Drug → Target → UniProt → Disease Lookup")

st.write(
    "Search for a drug, select one of its targets, convert aliases when needed, "
    "retrieve matching UniProt entries, and display proteome associations."
)

# -----------------------------
# File Paths
# -----------------------------
DRUG_DATA_PATH = "data/drugs_to_target.csv"
PROTEIN_DISEASE_PATH = "data/protein_to_disease.csv"
TARGET_ALIAS_PATH = "data/target_alias.csv"

INVALID_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
    "other",
    "others"
}

# -----------------------------
# Load Drug Data
# -----------------------------
@st.cache_data
def load_drug_data():
    df = pd.read_csv(DRUG_DATA_PATH)
    df.columns = df.columns.str.strip()

    required_cols = ["Drug Name", "Target"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column in drug table: {col}")
            st.stop()

    df["Drug Name"] = df["Drug Name"].fillna("").astype(str)
    df["Target"] = df["Target"].fillna("").astype(str)

    return df


# -----------------------------
# Load Protein-Disease Data
# -----------------------------
@st.cache_data
def load_protein_disease_data():
    df = pd.read_csv(PROTEIN_DISEASE_PATH)
    df.columns = df.columns.str.strip()

    required_cols = [
        "Entry",
        "Protein name",
        "Protein description",
        "Gene"
    ]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column in protein-disease table: {col}")
            st.stop()

    df["Entry"] = df["Entry"].fillna("").astype(str)
    df["Protein name"] = df["Protein name"].fillna("").astype(str)
    df["Protein description"] = df["Protein description"].fillna("").astype(str)
    df["Gene"] = df["Gene"].fillna("").astype(str)

    return df


# -----------------------------
# Load Target Alias Data
# -----------------------------
@st.cache_data
def load_target_aliases():
    df = pd.read_csv(TARGET_ALIAS_PATH)
    df.columns = df.columns.str.strip()

    required_cols = ["Original Target", "Search Term"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column in target alias table: {col}")
            st.stop()

    df["Original Target"] = df["Original Target"].fillna("").astype(str)
    df["Search Term"] = df["Search Term"].fillna("").astype(str)

    return df


# -----------------------------
# Split Multiple Targets
# Example:
# "c-Kit,PDGFR,VEGFR" -> ["c-Kit", "PDGFR", "VEGFR"]
# -----------------------------
def split_targets(target_string):
    if pd.isna(target_string):
        return []

    targets = re.split(r"[,;/|]+", str(target_string))

    targets = [
        target.strip()
        for target in targets
        if target.strip() != ""
        and target.strip().lower() not in INVALID_VALUES
    ]

    return targets


# -----------------------------
# Convert Target to UniProt Search Terms
# Uses data/target_alias.csv
# -----------------------------
def get_uniprot_search_terms(selected_target, alias_df):
    selected_target_clean = selected_target.strip().lower()

    match = alias_df[
        alias_df["Original Target"].str.strip().str.lower()
        == selected_target_clean
    ]

    # If no alias exists, use the selected target itself
    if match.empty:
        return [selected_target.strip()]

    search_value = match.iloc[0]["Search Term"].strip()

    search_terms = re.split(r"[,;/|]+", search_value)

    search_terms = [
        term.strip()
        for term in search_terms
        if term.strip() != ""
        and term.strip().lower() not in INVALID_VALUES
    ]

    return search_terms


# -----------------------------
# Helper: Safely Extract Protein Name from UniProt JSON
# -----------------------------
def extract_protein_name(result):
    protein_description = result.get("proteinDescription", {})

    recommended_name = protein_description.get("recommendedName", {})
    full_name = recommended_name.get("fullName", {})

    if "value" in full_name:
        return full_name["value"]

    # Fallback: submitted names
    submitted_names = protein_description.get("submissionNames", [])

    if len(submitted_names) > 0:
        submitted_full_name = submitted_names[0].get("fullName", {})
        return submitted_full_name.get("value", "N/A")

    return "N/A"


# -----------------------------
# Helper: Safely Extract Gene Names from UniProt JSON
# -----------------------------
def extract_gene_names(result):
    genes = result.get("genes", [])
    gene_names = []

    for gene in genes:
        if "geneName" in gene:
            gene_names.append(gene["geneName"]["value"])

        for synonym in gene.get("synonyms", []):
            if "value" in synonym:
                gene_names.append(synonym["value"])

    # Remove duplicates while preserving order
    gene_names = list(dict.fromkeys(gene_names))

    if len(gene_names) == 0:
        return "N/A"

    return ", ".join(gene_names)


# -----------------------------
# UniProt Search
# Searches all alias terms and returns all matching results
# -----------------------------
@st.cache_data
def search_uniprot(search_terms):
    url = "https://rest.uniprot.org/uniprotkb/search"

    # Allow function to receive either one string or a list
    if isinstance(search_terms, str):
        search_terms = [search_terms]

    all_results = []
    seen_accessions = set()

    for raw_term in search_terms:
        term = raw_term.strip()

        if term == "":
            continue

        clean_term = term.replace("*", "").strip()

        queries_to_try = []

        # Query 1: gene-focused search
        # Best for EGFR, PARP, ADRA*, VEGFR*, etc.
        if "*" in term:
            queries_to_try.append(
                f"(gene:{clean_term}* OR gene_exact:{clean_term}) "
                f"AND organism_id:9606 AND reviewed:true"
            )
        else:
            queries_to_try.append(
                f"(gene_exact:{clean_term} OR gene:{clean_term}) "
                f"AND organism_id:9606 AND reviewed:true"
            )

        # Query 2: broader fallback
        queries_to_try.append(
            f"(protein_name:{clean_term} OR {clean_term}) "
            f"AND organism_id:9606 AND reviewed:true"
        )

        for query in queries_to_try:
            params = {
                "query": query,
                "fields": "accession,id,gene_names,protein_name,organism_name",
                "format": "json",
                "size": 25
            }

            try:
                response = requests.get(url, params=params, timeout=15)
            except requests.exceptions.RequestException:
                continue

            if response.status_code != 200:
                continue

            data = response.json()
            results = data.get("results", [])

            for result in results:
                accession = result.get("primaryAccession", "N/A")

                if accession in seen_accessions:
                    continue

                seen_accessions.add(accession)

                protein_name = extract_protein_name(result)
                gene_names = extract_gene_names(result)

                all_results.append({
                    "accession": accession,
                    "entry_name": result.get("uniProtkbId", "N/A"),
                    "protein_name": protein_name,
                    "gene_names": gene_names,
                    "searched_term": term
                })

            # If the gene-focused search worked, skip fallback for this term
            if len(results) > 0:
                break

    return all_results


# -----------------------------
# Get Proteome Associations
# Returns associated and unassociated proteomes
# -----------------------------
def get_proteome_associations(uniprot_entry, protein_df):
    match = protein_df[protein_df["Entry"] == uniprot_entry]

    if match.empty:
        return None

    row = match.iloc[0]

    info_columns = [
        "Entry",
        "Protein name",
        "Protein description",
        "Gene"
    ]

    proteome_columns = [
        col for col in protein_df.columns
        if col not in info_columns
    ]

    associated_proteomes = []
    unassociated_proteomes = []

    for col in proteome_columns:
        value = row[col]
        is_associated = False

        if pd.notna(value) and str(value).strip() != "":
            try:
                is_associated = float(value) > 0
            except Exception:
                is_associated = True

        if is_associated:
            associated_proteomes.append(col)
        else:
            unassociated_proteomes.append(col)

    return {
        "protein_name": row.get("Protein name", "N/A"),
        "protein_description": row.get("Protein description", "N/A"),
        "gene": row.get("Gene", "N/A"),
        "associated_proteomes": associated_proteomes,
        "unassociated_proteomes": unassociated_proteomes
    }


# -----------------------------
# Compact Proteome List Display
# -----------------------------
def display_compact_proteome_lists(associated_proteomes, unassociated_proteomes):
    st.markdown(
        """
        <style>
            .proteome-box {
                background-color: white;
                border: 1px solid #e6eef8;
                border-radius: 14px;
                padding: 14px 16px;
                margin-top: 6px;
                margin-bottom: 8px;
            }

            .proteome-heading {
                font-weight: 700;
                color: #0b4f8a !important;
                margin-bottom: 6px;
                font-size: 16px;
            }

            .proteome-list {
                line-height: 1.1;
                margin-top: 0px;
                margin-bottom: 0px;
                padding-left: 18px;
            }

            .proteome-list li {
                margin-top: 0px;
                margin-bottom: 1px;
                padding-top: 0px;
                padding-bottom: 0px;
                font-size: 14px;
                color: #0f172a !important;
            }

            .proteome-empty {
                font-size: 14px;
                color: #64748b !important;
                margin: 0;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    col_assoc, col_unassoc = st.columns(2)

    with col_assoc:
        if len(associated_proteomes) == 0:
            assoc_html = """
            <div class="proteome-box">
                <div class="proteome-heading">Associated Proteomes</div>
                <p class="proteome-empty">None found.</p>
            </div>
            """
        else:
            assoc_items = "".join(
                [f"<li>{proteome}</li>" for proteome in associated_proteomes]
            )

            assoc_html = f"""
            <div class="proteome-box">
                <div class="proteome-heading">Associated Proteomes</div>
                <ul class="proteome-list">
                    {assoc_items}
                </ul>
            </div>
            """

        st.markdown(assoc_html, unsafe_allow_html=True)

    with col_unassoc:
        if len(unassociated_proteomes) == 0:
            unassoc_html = """
            <div class="proteome-box">
                <div class="proteome-heading">Unassociated Proteomes</div>
                <p class="proteome-empty">None found.</p>
            </div>
            """
        else:
            unassoc_items = "".join(
                [f"<li>{proteome}</li>" for proteome in unassociated_proteomes]
            )

            unassoc_html = f"""
            <div class="proteome-box">
                <div class="proteome-heading">Unassociated Proteomes</div>
                <ul class="proteome-list">
                    {unassoc_items}
                </ul>
            </div>
            """

        st.markdown(unassoc_html, unsafe_allow_html=True)


# -----------------------------
# Main App
# -----------------------------
drug_df = load_drug_data()
protein_disease_df = load_protein_disease_data()
alias_df = load_target_aliases()

drug_search = st.text_input(
    "Search Drug",
    placeholder="Examples: Axitinib, Veliparib, Nintedanib"
)

if drug_search:
    matches = drug_df[
        drug_df["Drug Name"].str.contains(
            drug_search,
            case=False,
            na=False
        )
    ]

    if matches.empty:
        st.error("No matching drug found.")

    else:
        selected_drug = st.selectbox(
            "Select Drug",
            matches["Drug Name"].tolist()
        )

        drug_row = drug_df[
            drug_df["Drug Name"] == selected_drug
        ].iloc[0]

        raw_targets = drug_row["Target"]
        target_options = split_targets(raw_targets)

        st.subheader("Selected Drug")

        st.write(f"**Drug:** {selected_drug}")

        # -----------------------------
        # Display Clinical Phase
        # -----------------------------
        if "Clinical phase" in drug_df.columns:
            clinical_phase = drug_row.get("Clinical phase", "N/A")

            if pd.isna(clinical_phase) or str(clinical_phase).strip() == "":
                clinical_phase = "N/A"

            st.write(f"**Clinical Phase:** {clinical_phase}")
        else:
            st.warning("Clinical Phase column not found in drugs_to_target.csv")

        st.write(f"**All Targets:** {raw_targets}")

        if len(target_options) == 0:
            st.error("No targets found for this drug.")

        else:
            selected_target = st.selectbox(
                "Select Target",
                target_options
            )

            search_terms = get_uniprot_search_terms(
                selected_target,
                alias_df
            )

            st.write(f"**Selected Target:** {selected_target}")
            st.write(
                f"**UniProt Search Term(s):** "
                f"`{', '.join(search_terms)}`"
            )

            with st.spinner("Searching UniProt..."):
                uniprot_results = search_uniprot(search_terms)

            st.subheader("UniProt Results")

            if len(uniprot_results) == 0:
                st.error("No UniProt result found.")

            else:
                uniprot_results_df = pd.DataFrame(uniprot_results)

                st.dataframe(
                    uniprot_results_df,
                    use_container_width=True
                )

                result_options = [
                    (
                        f"{r['accession']} | "
                        f"{r['gene_names']} | "
                        f"{r['protein_name']} | "
                        f"searched: {r['searched_term']}"
                    )
                    for r in uniprot_results
                ]

                selected_result_label = st.selectbox(
                    "Select UniProt Entry",
                    result_options
                )

                selected_index = result_options.index(selected_result_label)
                selected_result = uniprot_results[selected_index]

                accession = selected_result["accession"]

                st.success(f"Selected UniProt Entry: {accession}")

                st.write(
                    f"**Gene Name(s):** "
                    f"{selected_result['gene_names']}"
                )

                st.write(
                    f"**Protein Name:** "
                    f"{selected_result['protein_name']}"
                )

                st.write(
                    f"**Matched Search Term:** "
                    f"{selected_result['searched_term']}"
                )

                st.link_button(
                    "Open UniProt",
                    f"https://www.uniprot.org/uniprotkb/{accession}/entry"
                )

                proteome_result = get_proteome_associations(
                    accession,
                    protein_disease_df
                )

                st.subheader("Proteome Associations")

                if proteome_result is None:
                    st.error(
                        "No matching protein entry found in "
                        "protein_to_disease.csv."
                    )

                else:
                    st.write(
                        f"**Protein Name:** "
                        f"{proteome_result['protein_name']}"
                    )

                    st.write(
                        f"**Description:** "
                        f"{proteome_result['protein_description']}"
                    )

                    st.write(
                        f"**Gene:** "
                        f"{proteome_result['gene']}"
                    )

                    associated_proteomes = proteome_result["associated_proteomes"]
                    unassociated_proteomes = proteome_result["unassociated_proteomes"]

                    display_compact_proteome_lists(
                        associated_proteomes,
                        unassociated_proteomes
                    )

else:
    st.info("Search for a drug to begin.")

# -----------------------------
# Close Content Container
# -----------------------------
st.markdown('</div>', unsafe_allow_html=True)