import streamlit as st
import pandas as pd
import re

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Reverse Search", layout="wide")

st.title("Reverse Disease / Data Source Search")
st.write(
    "Select a disease/data source and find drugs whose targets are related "
    "to proteins associated with that source."
)

# -----------------------------
# File paths
# -----------------------------
DRUG_DATA_PATH = "data/drugs_to_target.csv"
PROTEIN_DISEASE_PATH = "data/protein_to_disease.csv"

# These are not real targets and should never be matched
INVALID_TARGETS = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
    "others",
    "other"
}


# -----------------------------
# Load drug data
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

    # Remove rows where the entire Target cell is invalid
    df = df[
        ~df["Target"].str.strip().str.lower().isin(INVALID_TARGETS)
    ].copy()

    return df


# -----------------------------
# Load protein-disease data
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
# Clean text for matching
# -----------------------------
def normalize_text(text):
    if pd.isna(text):
        return ""

    text = str(text).lower().strip()

    replacements = {
        "_human": "",
        "-": "",
        " ": "",
        "/": "",
        "_": "",
        "(": "",
        ")": "",
        ".": "",
        ",": "",
        ":": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# -----------------------------
# Split target strings
# Example:
# "c-Kit,PDGFR,VEGFR" -> ["c-Kit", "PDGFR", "VEGFR"]
# -----------------------------
def split_targets(target_string):
    if pd.isna(target_string):
        return []

    target_string = str(target_string).strip()

    if target_string.lower() in INVALID_TARGETS:
        return []

    targets = [
        target.strip()
        for target in re.split(r"[,;/|]+", target_string)
        if target.strip()
    ]

    # Remove invalid target values after splitting
    cleaned_targets = []

    for target in targets:
        target_clean = target.strip().lower()
        target_norm = normalize_text(target)

        if target_clean in INVALID_TARGETS:
            continue

        if target_norm in INVALID_TARGETS:
            continue

        cleaned_targets.append(target)

    return cleaned_targets


# -----------------------------
# Expand broad target names into gene/prefix aliases
# -----------------------------
def expand_target_aliases(target):
    if pd.isna(target):
        return []

    target = str(target).strip()

    if target.lower() in INVALID_TARGETS:
        return []

    target_norm = normalize_text(target)

    if target_norm == "" or target_norm in INVALID_TARGETS:
        return []

    alias_map = {
        # DNA damage / PARP
        "parp": ["parp"],

        # Tyrosine kinases / angiogenesis
        "vegfr": ["vegfr", "flt", "kdr"],
        "pdgfr": ["pdgfr"],
        "fgfr": ["fgfr"],
        "egfr": ["egfr", "erbb"],
        "her2": ["erbb2"],
        "src": ["src"],
        "bcrabl": ["abl", "bcr"],
        "ckit": ["kit"],
        "kit": ["kit"],
        "cmet": ["met"],
        "met": ["met"],
        "alk": ["alk"],
        "cret": ["ret"],
        "ret": ["ret"],
        "flt3": ["flt3"],

        # PI3K/Akt/mTOR
        "mtor": ["mtor"],
        "akt": ["akt"],
        "pi3k": ["pik3"],

        # MAPK pathway
        "mek": ["map2k"],
        "raf": ["raf"],

        # Epigenetics
        "hdac": ["hdac"],
        "dnamethyltransferase": ["dnmt"],

        # Cell cycle
        "cdk": ["cdk"],
        "aurorakinase": ["aurka", "aurkb", "aurkc"],

        # DNA/RNA synthesis
        "topoisomerase": ["top"],
        "dnarna synthesis": [],
        "dnarnasynthesis": [],
        "dhfr": ["dhfr"],

        # Proteasome / protein degradation
        "proteasome": ["psm"],
        "e3ligase": ["crbn", "cul"],

        # Cytoskeletal / tubulin
        "microtubuleassociated": ["tub", "tuba", "tubb"],
        "vda": ["tub", "tuba", "tubb"],

        # Hormone receptors
        "androgenreceptor": ["ar"],
        "aromatase": ["cyp19a1"],
        "estrogenprogestogenreceptor": ["esr", "pgr"],

        # Immune / cytokine
        "tnfalpha": ["tnf"],

        # GPCR / neuronal
        "gabareceptor": ["gabra", "gabrb", "gabrg"],
        "adrenergicreceptor": ["adra", "adrb"],

        # Transporters
        "cftr": ["cftr"],

        # Viral / infection
        "hcvprotease": ["hcv"],
        "hivprotease": ["hiv"],

        # Heat shock proteins
        "hsp": ["hsp"],
        "hspeg hsp90": ["hsp90", "hsp"],
    }

    search_terms = [target_norm]

    if target_norm in alias_map:
        search_terms.extend(alias_map[target_norm])

    # Remove empty aliases
    search_terms = [
        term for term in search_terms
        if term and term.lower() not in INVALID_TARGETS
    ]

    return list(set(search_terms))


# -----------------------------
# Find related drugs for selected source
# -----------------------------
@st.cache_data
def find_related_drugs(drug_df, protein_df, selected_source):
    # 1. Get proteins associated with the selected data source
    associated_proteins = protein_df[
        pd.to_numeric(protein_df[selected_source], errors="coerce").fillna(0) > 0
    ].copy()

    # 2. Create fast gene lookup set
    associated_genes = set(
        associated_proteins["Gene"]
        .dropna()
        .astype(str)
        .map(normalize_text)
        .tolist()
    )

    # Remove invalid/empty genes
    associated_genes = {
        gene for gene in associated_genes
        if gene and gene.lower() not in INVALID_TARGETS
    }

    # 3. Create one searchable protein text string
    associated_protein_text = " ".join(
        associated_proteins["Protein name"].fillna("").astype(str).tolist()
        + associated_proteins["Protein description"].fillna("").astype(str).tolist()
    )

    associated_protein_text_norm = normalize_text(associated_protein_text)

    matched_rows = []

    # 4. Loop through drugs only
    for _, drug_row in drug_df.iterrows():
        drug_name = drug_row["Drug Name"]
        raw_targets = drug_row["Target"]

        target_list = split_targets(raw_targets)

        if len(target_list) == 0:
            continue

        matched_target_terms = []

        for target in target_list:
            target_clean = target.strip().lower()
            target_norm = normalize_text(target)

            if target_clean in INVALID_TARGETS:
                continue

            if target_norm in INVALID_TARGETS or target_norm == "":
                continue

            expanded_terms = expand_target_aliases(target)

            if len(expanded_terms) == 0:
                continue

            for term in expanded_terms:
                term_norm = normalize_text(term)

                if term_norm == "" or term_norm in INVALID_TARGETS:
                    continue

                # Gene matching
                gene_match = any(
                    gene.startswith(term_norm) or term_norm in gene
                    for gene in associated_genes
                )

                # Protein name/description fallback matching
                protein_text_match = term_norm in associated_protein_text_norm

                if gene_match or protein_text_match:
                    matched_target_terms.append(target)
                    break

        if matched_target_terms:
            matched_rows.append({
                "Data Source": selected_source,
                "Drug Name": drug_name,
                "Drug Target": raw_targets,
                "Matched Target Term": ", ".join(sorted(set(matched_target_terms))),
                "Clinical Phase": drug_row.get("Clinical phase", ""),
                "Status": drug_row.get("Status", ""),
                "Pathway": drug_row.get("Pathway", ""),
                "Information": drug_row.get("Information", ""),
                "URL": drug_row.get("URL", "")
            })

    results_df = pd.DataFrame(matched_rows)

    if not results_df.empty:
        results_df = results_df.drop_duplicates()

        # Extra safety: remove rows where matched target is invalid
        results_df = results_df[
            ~results_df["Matched Target Term"]
            .str.strip()
            .str.lower()
            .isin(INVALID_TARGETS)
        ]

    return results_df, associated_proteins


# -----------------------------
# Main app
# -----------------------------
drug_df = load_drug_data()
protein_df = load_protein_disease_data()

info_columns = [
    "Entry",
    "Protein name",
    "Protein description",
    "Gene"
]

data_source_columns = [
    col for col in protein_df.columns
    if col not in info_columns
]

st.subheader("Choose a disease/data source")

search_term = st.text_input(
    "Search data source",
    placeholder="Example: BRCA, LUAD, GBM, OV, PDAC"
)

if search_term:
    matching_sources = [
        col for col in data_source_columns
        if search_term.lower() in col.lower()
    ]
else:
    matching_sources = data_source_columns

if len(matching_sources) == 0:
    st.warning("No matching data sources found.")
    st.stop()

selected_source = st.selectbox(
    "Select data source",
    options=matching_sources,
    index=None,
    placeholder="Choose a data source..."
)

if selected_source:
    st.divider()

    with st.spinner("Finding related drugs..."):
        results_df, associated_proteins = find_related_drugs(
            drug_df,
            protein_df,
            selected_source
        )

    st.subheader(f"Related Drugs for {selected_source}")

    if results_df.empty:
        st.warning("No related drugs found for this data source.")
        st.write(
            "This usually means the drug target names do not directly match "
            "the gene/protein names in the protein-disease table. You may need "
            "to add more aliases."
        )

    else:
        st.success(
            f"Found {results_df['Drug Name'].nunique()} related drugs for {selected_source}."
        )

        display_cols = [
            "Data Source",
            "Drug Name",
            "Drug Target",
            "Matched Target Term",
            "Clinical Phase",
            "Status",
            "Pathway",
            "Information",
            "URL"
        ]

        display_cols = [
            col for col in display_cols
            if col in results_df.columns
        ]

        st.dataframe(
            results_df[display_cols],
            use_container_width=True
        )

        st.download_button(
            label="Download related drugs as CSV",
            data=results_df[display_cols].to_csv(index=False),
            file_name=f"{selected_source}_related_drugs.csv",
            mime="text/csv"
        )

    with st.expander("Debug info"):
        st.write(f"Associated proteins found: {len(associated_proteins)}")
        st.write(f"Drugs searched after target cleanup: {len(drug_df)}")

        cleaned_drug_targets = drug_df["Target"].dropna().astype(str)
        invalid_target_rows = cleaned_drug_targets[
            cleaned_drug_targets.str.strip().str.lower().isin(INVALID_TARGETS)
        ]

        st.write(f"Invalid target rows remaining: {len(invalid_target_rows)}")

else:
    st.info("Select a data source to begin.")