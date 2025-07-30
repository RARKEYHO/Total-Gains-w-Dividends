import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf

# App configuration
st.set_page_config(
    page_title="Dividend & Gain Calculator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title
st.title("📈 Dividend & Total Gain/Loss Calculator")

# Initialize session state for additional purchases
if 'num_additional' not in st.session_state:
    st.session_state.num_additional = 0

# Sidebar for inputs
with st.sidebar:
    st.header("Investment Details")
    
    # Main inputs
    ticker = st.text_input("Ticker Symbol", value="AAPL", help="Enter stock symbol (e.g., AAPL, MSFT)")
    purchase_date = st.date_input("Purchase Date", value=datetime(2020, 1, 1), help="Date of initial purchase")
    shares = st.number_input("Number of Shares", min_value=0.0, value=10.0, step=1.0, help="Initial shares purchased")
    cost_basis = st.number_input("Cost Basis per Share ($)", min_value=0.0, value=100.0, step=1.0, help="Purchase price per share")
    drip = st.checkbox("Dividends Reinvested (DRIP)", value=True, help="Check if dividends are automatically reinvested")
    
    st.markdown("---")
    st.subheader("Additional Purchases")
    
    # Additional purchases controls
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.num_additional = st.number_input(
            "Number of Additional Purchases", 
            min_value=0, 
            value=st.session_state.num_additional,
            step=1,
            help="Add more purchases made after initial investment"
        )
    with col2:
        st.markdown("")  # Spacer
        st.markdown("")  # Spacer
        if st.button("🔄 Update"):
            st.experimental_rerun()
    
    # Store additional purchases in session state
    if 'additional_purchases' not in st.session_state:
        st.session_state.additional_purchases = []
    
    # Ensure we have the right number of purchase entries
    while len(st.session_state.additional_purchases) < st.session_state.num_additional:
        st.session_state.additional_purchases.append({
            'date': datetime.today(),
            'shares': 0.0,
            'price': 0.0
        })
    while len(st.session_state.additional_purchases) > st.session_state.num_additional:
        st.session_state.additional_purchases.pop()

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Investment Information")
    
    # Display main investment details
    with st.expander("Initial Investment", expanded=True):
        st.write(f"**Ticker:** {ticker}")
        st.write(f"**Purchase Date:** {purchase_date}")
        st.write(f"**Shares:** {shares}")
        st.write(f"**Cost Basis:** ${cost_basis:,.2f} per share")
        st.write(f"**Dividends Reinvested:** {'Yes' if drip else 'No'}")
    
    # Additional purchases section
    if st.session_state.num_additional > 0:
        st.subheader("Additional Purchases")
        for i in range(st.session_state.num_additional):
            with st.expander(f"Purchase #{i+1}", expanded=True):
                st.session_state.additional_purchases[i]['date'] = st.date_input(
                    f"Date", 
                    value=st.session_state.additional_purchases[i]['date'],
                    key=f"date_{i}"
                )
                st.session_state.additional_purchases[i]['shares'] = st.number_input(
                    f"Shares", 
                    min_value=0.0, 
                    value=st.session_state.additional_purchases[i]['shares'],
                    step=1.0,
                    key=f"shares_{i}"
                )
                st.session_state.additional_purchases[i]['price'] = st.number_input(
                    f"Price per Share ($)", 
                    min_value=0.0, 
                    value=st.session_state.additional_purchases[i]['price'],
                    step=1.0,
                    key=f"price_{i}"
                )

with col2:
    st.subheader("Calculate Results")
    
    # Calculate button
    if st.button("Calculate Investment Performance", type="primary", use_container_width=True):
        with st.spinner("Fetching financial data and calculating..."):
            try:
                # Fetch stock data
                stock = yf.Ticker(ticker)
                hist = stock.history(start=purchase_date)
                
                if hist.empty:
                    st.error("No data found for this ticker and date range")
                else:
                    # Calculate total cost basis
                    total_cost = shares * cost_basis
                    total_shares = shares

                    # Process additional purchases
                    for purchase in st.session_state.additional_purchases:
                        if purchase['date'] and purchase['shares'] and purchase['price']:
                            total_shares += purchase['shares']
                            total_cost += purchase['shares'] * purchase['price']

                    # Get current price
                    current_price = hist['Close'][-1]

                    # Calculate dividends
                    try:
                        dividends = stock.dividends[purchase_date:]
                        if drip and not dividends.empty:
                            # Simulate DRIP effect
                            drip_shares = 0
                            cumulative_shares = shares
                            
                            # Process initial period dividends
                            if st.session_state.additional_purchases:
                                valid_dates = [p['date'] for p in st.session_state.additional_purchases if p['date']]
                                if valid_dates:
                                    first_add_date = min(valid_dates)
                                    initial_dividends = dividends[dividends.index < first_add_date]
                                else:
                                    initial_dividends = dividends
                            else:
                                initial_dividends = dividends
                            
                            for date, div in initial_dividends.items():
                                try:
                                    price_at_div = hist.loc[date.strftime('%Y-%m-%d')]['Close']
                                    drip_shares += (cumulative_shares * div) / price_at_div
                                except:
                                    continue
                            
                            # Process additional purchase periods
                            valid_purchases = [p for p in st.session_state.additional_purchases if p['date']]
                            sorted_purchases = sorted(valid_purchases, key=lambda x: x['date'])
                            
                            for i, purchase in enumerate(sorted_purchases):
                                cumulative_shares += purchase['shares']
                                if i == len(sorted_purchases) - 1:
                                    period_dividends = dividends[dividends.index >= purchase['date']]
                                else:
                                    period_dividends = dividends[
                                        (dividends.index >= purchase['date']) & 
                                        (dividends.index < sorted_purchases[i+1]['date'])
                                    ]
                                
                                for date, div in period_dividends.items():
                                    try:
                                        price_at_div = hist.loc[date.strftime('%Y-%m-%d')]['Close']
                                        drip_shares += (cumulative_shares * div) / price_at_div
                                    except:
                                        continue
                            
                            total_shares += drip_shares
                            total_dividends =