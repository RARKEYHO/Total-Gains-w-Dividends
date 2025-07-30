import streamlit as st
import pandas as pd
from datetime import date
import yfinance as yf

# App configuration with lighter theme
st.set_page_config(
    page_title="Dividend & Gain Calculator",
    page_icon="💰",
    layout="wide"
)

# Light green/blue theme styling
st.markdown("""
<style>
    /* Light background */
    .stApp {
        background-color: #f8fbfd;
    }
    
    /* Header */
    header {
        background: linear-gradient(135deg, #e6f4ea, #e1f0fa) !important;
        padding: 1rem 0;
    }
    
    header h1 {
        color: #0d5e2a !important;
        text-align: center;
        font-weight: 600;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #f0f9f4;
        border-right: 1px solid #d1e7dd;
    }
    
    /* Cards and containers */
    div[data-testid="stExpander"] {
        border: 1px solid #d1e7dd;
        border-radius: 8px;
        margin-bottom: 1rem;
        background: white;
    }
    
    div[data-testid="stExpander"] div[role="button"] {
        background: #e6f4ea;
        border-radius: 8px 8px 0 0;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background: #f0f9ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    
    /* Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0d9e4e, #0ea5e9) !important;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border-radius: 6px;
    }
    
    /* Download button */
    a[data-baseweb="button"] {
        background: #0d9e4e !important;
    }
    
    /* Section headers */
    h2, h3 {
        color: #0d5e2a;
    }
    
    h3 {
        border-bottom: 2px solid #a7f3d0;
        padding-bottom: 0.5rem;
    }
    
    /* Dataframe */
    div[data-testid="stDataFrame"] {
        border: 1px solid #d1e7dd;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Info boxes */
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }
    
    .info-box {
        background: #f0f9ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# App