import streamlit as st
import pandas as pd
from datetime import date
import yfinance as yf

# App configuration
st.set_page_config(
    page_title="Dividend & Gain Calculator",
    page_icon="💰",
    layout="wide"
)

# App title
st.title("💰 Dividend & Gain/Loss Calculator")

# Initialize session state
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'dividend_details' not in st.session_state:
    st.session_state.dividend_details = None

# Sidebar for inputs
with st.sidebar:
    st.header("Investment Details")
    
    # Main inputs
    ticker = st.text_input("Ticker Symbol", value="AAPL")
    purchase_date = st.date_input(
        "Purchase Date", 
        value=date(2020, 1, 1),
        min_value=date(1970, 1, 1),
        max_value=date.today()
    )
    shares = st.number_input("Number of Shares", min_value=0.0, value=10.0, step=1.0)
    cost_basis = st.number_input("Cost Basis per Share ($)", min_value=0.0, value=100.0, step=1.0)
    drip = st.checkbox("Dividends Reinvested (DRIP)", value=True)
    
    st.markdown("---")
    st.subheader("Additional Purchases")
    
    # Number of additional purchases
    num_additional = st.number_input("Number of Additional Purchases", min_value=0, value=0, step=1)
    
    # Store additional purchases
    additional_purchases = []
    for i in range(num_additional):
        st.markdown(f"**Purchase {i+1}**")
        add_date = st.date_input(
            f"Date {i+1}", 
            key=f"add_date_{i}",
            min_value=date(1970, 1, 1),
            max_value=date.today()
        )
        add_shares = st.number_input(f"Shares {i+1}", min_value=0.0, value=0.0, step=1.0, key=f"add_shares_{i}")
        add_price = st.number_input(f"Price {i+1} ($)", min_value=0.0, value=0.0, step=1.0, key=f"add_price_{i}")
        additional_purchases.append({
            'date': add_date,
            'shares': add_shares,
            'price': add_price
        })

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Investment Information")
    
    # Display current inputs
    with st.expander("Current Investment Details", expanded=True):
        st.write(f"**Ticker:** {ticker}")
        st.write(f"**Initial Purchase Date:** {purchase_date}")
        st.write(f"**Initial Shares:** {shares}")
        st.write(f"**Cost Basis:** ${cost_basis:,.2f} per share")
        st.write(f"**Dividends Reinvested:** {'Yes' if drip else 'No'}")
        
        if num_additional > 0:
            st.write(f"**Additional Purchases:** {num_additional}")
            for i, purchase in enumerate(additional_purchases):
                st.write(f"Purchase {i+1}: {purchase['date']} - {purchase['shares']} shares at ${purchase['price']:,.2f}")

with col2:
    st.subheader("Calculate Results")
    
    # Calculate button
    if st.button("Calculate Investment Performance", type="primary", use_container_width=True):
        with st.spinner("Fetching financial data and calculating..."):
            try:
                # Fetch stock data
                stock = yf.Ticker(ticker)
                
                # Fetch maximum available history
                hist = stock.history(period="max")
                
                # Filter to purchase date
                hist = hist[hist.index.date >= purchase_date]
                
                if hist.empty:
                    st.error("No data found for this ticker and date range")
                else:
                    # Calculate total cost basis
                    total_cost = shares * cost_basis
                    total_shares = shares

                    # Process additional purchases
                    for purchase in additional_purchases:
                        if purchase['date'] and purchase['shares'] and purchase['price']:
                            total_shares += purchase['shares']
                            total_cost += purchase['shares'] * purchase['price']

                    # Get current price (most recent)
                    current_price = hist['Close'][-1]

                    # Calculate dividends
                    try:
                        # Fetch maximum dividend history
                        dividends = stock.dividends
                        
                        # Filter dividends to purchase date range
                        dividends = dividends[dividends.index.date >= purchase_date]
                        
                        # Store dividend details for export
                        dividend_details = []
                        
                        if not dividends.empty:
                            # Initialize for DRIP calculations
                            cumulative_shares = total_shares
                            total_dividends_received = 0
                            
                            # Create a list of all significant dates (purchase dates + dividend dates)
                            all_dates = [purchase_date] + [p['date'] for p in additional_purchases if p['date']]
                            dividend_dates = list(dividends.index.date)
                            all_significant_dates = sorted(set(all_dates + dividend_dates))
                            
                            # Process each dividend payment chronologically
                            for date_idx, div_amount in dividends.items():
                                dividend_date = date_idx.date()
                                
                                # Find share count at time of dividend
                                shares_at_time = cumulative_shares
                                
                                # Calculate dividend received at this time
                                dividend_received = shares_at_time * div_amount
                                total_dividends_received += dividend_received
                                
                                # Add to dividend details
                                dividend_details.append({
                                    'Date': dividend_date.strftime('%Y-%m-%d'),
                                    'Dividend Per Share': div_amount,
                                    'Shares at Time': shares_at_time,
                                    'Total Dividends': dividend_received
                                })
                                
                                # If DRIP is enabled, reinvest the dividend
                                if drip:
                                    try:
                                        price_date = dividend_date.strftime('%Y-%m-%d')
                                        if price_date in hist.index.strftime('%Y-%m-%d'):
                                            price_at_div = hist.loc[price_date]['Close']
                                        else:
                                            # Get the closest previous trading day
                                            hist_before = hist[hist.index.date <= dividend_date]
                                            if not hist_before.empty:
                                                price_at_div = hist_before['Close'][-1]
                                            else:
                                                continue
                                        
                                        # Calculate new shares from reinvestment
                                        new_shares = dividend_received / price_at_div
                                        cumulative_shares += new_shares
                                    except:
                                        continue
                            
                            # Update total shares if DRIP was used
                            if drip:
                                total_shares = cumulative_shares
                                total_dividends = total_dividends_received
                            else:
                                # For non-DRIP, dividends based on final share count
                                total_dividends = dividends.sum() * total_shares
                        else:
                            # No dividends
                            total_dividends = 0
                            drip_shares = 0
                        
                        # Calculate DRIP shares (difference between final and initial shares)
                        drip_shares = total_shares - (shares + sum(p['shares'] for p in additional_purchases if p['shares']))
                        if drip_shares < 0:
                            drip_shares = 0
                        
                        # Store dividend details in session state
                        st.session_state.dividend_details = dividend_details
                        
                    except Exception as e:
                        st.warning(f"Could not fetch dividend data: {str(e)}")
                        total_dividends = 0
                        drip_shares = 0
                        st.session_state.dividend_details = []

                    # Calculate current value
                    current_value = total_shares * current_price

                    # Calculate gains/losses
                    total_gain_loss = current_value + total_dividends - total_cost
                    total_gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0

                    # Store results
                    st.session_state.results = {
                        'Ticker': ticker,
                        'Initial Purchase Date': purchase_date.strftime('%Y-%m-%d'),
                        'Initial Shares': shares,
                        'Additional Shares': sum(p['shares'] for p in additional_purchases if p['shares']),
                        'DRIP Shares': round(drip_shares, 4),
                        'Total Shares': round(total_shares, 4),
                        'Total Cost Basis': round(total_cost, 2),
                        'Current Price': round(current_price, 2),
                        'Current Value': round(current_value, 2),
                        'Total Dividends': round(total_dividends, 2),
                        'Total Gain/Loss': round(total_gain_loss, 2),
                        'Total Gain/Loss %': round(total_gain_loss_percent, 2)
                    }
                    
                    st.session_state.calculated = True
                    st.success("Calculation complete!")
                    
                    # Show info about dividend data
                    if not dividends.empty:
                        st.info(f"Found {len(dividends)} dividend payments since {purchase_date}")
                    else:
                        st.warning("No dividend data available for this stock/ticker")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Display results if available
    if st.session_state.calculated and st.session_state.results:
        st.markdown("---")
        st.subheader("Export Results")
        
        # Create comprehensive export data
        main_df = pd.DataFrame([st.session_state.results])
        
        if st.session_state.dividend_details:
            dividend_df = pd.DataFrame(st.session_state.dividend_details)
        else:
            dividend_df = pd.DataFrame(columns=['Date', 'Dividend Per Share', 'Shares at Time', 'Total Dividends'])
        
        # Combine into one CSV
        csv_string = "INVESTMENT SUMMARY\n"
        csv_string += main_df.to_csv(index=False) + "\n"
        csv_string += "DIVIDEND DETAILS\n"
        csv_string += dividend_df.to_csv(index=False)
        
        st.download_button(
            label="Download Comprehensive CSV",
            data=csv_string,
            file_name=f"{st.session_state.results['Ticker']}_investment_report.csv",
            mime="text/csv",
            use_container_width=True
        )

# Results display area
if st.session_state.calculated and st.session_state.results:
    st.markdown("---")
    st.header("Investment Summary")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Value", f"${st.session_state.results['Current Value']:,.2f}")
    
    with col2:
        st.metric("Total Dividends", f"${st.session_state.results['Total Dividends']:,.2f}")
    
    with col3:
        st.metric(
            "Total Gain/Loss", 
            f"${st.session_state.results['Total Gain/Loss']:,.2f}",
            delta_color=("normal" if st.session_state.results['Total Gain/Loss'] >= 0 else "inverse")
        )
    
    with col4:
        st.metric(
            "Return %", 
            f"{st.session_state.results['Total Gain/Loss %']:,.2f}%",
            delta_color=("normal" if st.session_state.results['Total Gain/Loss %'] >= 0 else "inverse")
        )
    
    # Detailed results table
    st.subheader("Detailed Breakdown")
    results_df = pd.DataFrame([st.session_state.results])
    st.dataframe(results_df.style.format({
        'Total Cost Basis': '${:,.2f}',
        'Current Price': '${:,.2f}',
        'Current Value': '${:,.2f}',
        'Total Dividends': '${:,.2f}',
        'Total Gain/Loss': '${:,.2f}',
        'Total Gain/Loss %': '{:,.2f}%'
    }), use_container_width=True)
    
    # Share breakdown
    st.subheader("Share Breakdown")
    share_col1, share_col2, share_col3, share_col4 = st.columns(4)
    
    with share_col1:
        st.metric("Initial Shares", st.session_state.results['Initial Shares'])
    
    with share_col2:
        st.metric("Additional Shares", st.session_state.results['Additional Shares'])
    
    with share_col3:
        st.metric("DRIP Shares", st.session_state.results['DRIP Shares'])
    
    with share_col4:
        st.metric("Total Shares", st.session_state.results['Total Shares'])
    
    # Dividend details table
    if st.session_state.dividend_details:
        st.subheader("Dividend History")
        dividend_df = pd.DataFrame(st.session_state.dividend_details)
        st.dataframe(dividend_df.style.format({
            'Dividend Per Share': '${:,.4f}',
            'Shares at Time': '{:,.4f}',
            'Total Dividends': '${:,.4f}'
        }), use_container_width=True)
    else:
        st.subheader("Dividend History")
        st.info("No dividend data available for this ticker")

# Instructions
with st.expander("How to Use This Calculator", expanded=True):
    st.markdown("""
    1. Enter your investment details in the sidebar
    2. Add any additional purchases if applicable
    3. Click "Calculate Investment Performance"
    4. View results and download comprehensive CSV report
    
    **Note:** 
    - Date range extended to Jan 1, 1970
    - Dividend data depends on Yahoo Finance availability
    - DRIP calculations now properly compound with increasing dividends
    - Export includes both summary and detailed dividend information
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center;">
        <p>If you found this helpful, you can buy me a coffee 🙂</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the button
    button_col1, button_col2, button_col3 = st.columns([1, 2, 1])
    with button_col2:
        st.link_button("☕ Buy me a coffee", "https://paypal.me/nidwannaya", use_container_width=True)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <p>© 2025 Rajesh Nidwannaya. All rights reserved. ~ raj@nidwannaya.com ~ www.nidwannaya.com</p>
    </div>
    """, unsafe_allow_html=True)