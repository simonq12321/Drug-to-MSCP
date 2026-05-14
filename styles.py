import streamlit as st


def apply_global_styles():
    st.markdown(
        """
        <style>
            /* -----------------------------
               Entire App Background
            ----------------------------- */
            .stApp {
                background-color: #f8fbff !important;
                color: #0f172a !important;
            }

            section.main {
                background-color: #f8fbff !important;
            }

            .block-container {
                padding-top: 0rem !important;
                max-width: 100% !important;
                background-color: #f8fbff !important;
            }

            /* -----------------------------
               General Text
            ----------------------------- */
            h1, h2, h3, h4, h5, h6,
            p, span, div, label {
                color: #0f172a !important;
            }

            /* -----------------------------
               Sidebar
            ----------------------------- */
            section[data-testid="stSidebar"] {
                background-color: white !important;
                border-right: 1px solid #e6eef8 !important;
            }

            section[data-testid="stSidebar"] > div {
                background-color: white !important;
            }

            section[data-testid="stSidebar"] * {
                color: #0f172a !important;
            }

            section[data-testid="stSidebar"] [aria-selected="true"] {
                background-color: #eaf4ff !important;
                color: #0b4f8a !important;
                border-radius: 10px !important;
            }

            /* -----------------------------
               Header
            ----------------------------- */
            header[data-testid="stHeader"] {
                background-color: #f8fbff !important;
            }

            div[data-testid="stToolbar"] {
                background-color: transparent !important;
            }

            /* -----------------------------
               Text Inputs
            ----------------------------- */
            div[data-testid="stTextInput"] input {
                background-color: white !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
            }

            div[data-testid="stTextInput"] input::placeholder {
                color: #64748b !important;
            }

            /* -----------------------------
               Selectboxes
            ----------------------------- */
            div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
                background-color: white !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
            }

            div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
                color: #0f172a !important;
            }

            div[data-testid="stSelectbox"] svg {
                fill: #0f172a !important;
                color: #0f172a !important;
            }

            /* Dropdown menu */
            div[data-baseweb="popover"] {
                background-color: white !important;
            }

            div[data-baseweb="menu"] {
                background-color: white !important;
            }

            div[data-baseweb="menu"] li {
                background-color: white !important;
                color: #0f172a !important;
            }

            div[data-baseweb="menu"] li:hover {
                background-color: #eaf4ff !important;
                color: #0b4f8a !important;
            }

            /* -----------------------------
            Buttons + Link Buttons
            ----------------------------- */

            /* Regular Streamlit buttons */
            button {
                background-color: white !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
            }

            /* Streamlit link buttons, like Open UniProt */
            div[data-testid="stLinkButton"] a {
                background-color: white !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
                text-decoration: none !important;
                box-shadow: none !important;
            }

            /* Text inside link buttons */
            div[data-testid="stLinkButton"] a p {
                color: #0f172a !important;
            }

            /* Hover effect */
            button:hover,
            div[data-testid="stLinkButton"] a:hover {
                background-color: #eaf4ff !important;
                color: #0b4f8a !important;
                border-color: #0b4f8a !important;
            }

            /* Hover text inside link button */
            div[data-testid="stLinkButton"] a:hover p {
                color: #0b4f8a !important;
            }

            /* -----------------------------
               Tables / DataFrames
            ----------------------------- */
            table, thead, tbody, tr, th, td {
                color: #0f172a !important;
                background-color: white !important;
            }

            div[data-testid="stDataFrame"] {
                background-color: white !important;
            }

            /* -----------------------------
               Cards
            ----------------------------- */
            .section-card {
                background: white !important;
                padding: 24px;
                border-radius: 18px;
                box-shadow: 0 4px 18px rgba(0, 60, 120, 0.08);
                border: 1px solid #e6eef8;
                margin-bottom: 20px;
            }

            .section-title {
                font-size: 26px;
                font-weight: 700;
                color: #0b4f8a !important;
                margin-bottom: 10px;
            }

            .section-text {
                font-size: 17px;
                color: #334155 !important;
                line-height: 1.6;
            }

            /* -----------------------------
               Banner
            ----------------------------- */
            .banner-container {
                width: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }

            .banner-container img {
                width: 100%;
                height: auto;
                display: block;
                border-radius: 0px;
            }

            .content-container {
                padding: 2rem 5rem;
            }

            @media (max-width: 768px) {
                .content-container {
                    padding: 1.25rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True
    )