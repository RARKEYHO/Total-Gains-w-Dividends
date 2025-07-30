import streamlit as st
import pandas as pd
from datetime import datetime, date
import yfinance as yf

# Set page config with favicon
st.set_page_config(
    page_title="Dividend & Gain Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for financial theme
st.markdown("""
<style>
    /* Main background and text colors */
    :root {
        --primary: #0a2540;
        --secondary: #1a365d;
        --accent: #3182ce;
        --light: #f0f4f8;
        --success: #38a169;
        --danger: #e53e3e;
        --warning: #dd6b20;
    }
    
    /* Main background */
    .stApp {
        background-color: #f8fafc;
        color: #1a202c;
    }
    
    /* Header styling */
    header {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        padding: 2rem 0;
    }
    
    header h1 {
        color: white !important;
        text-align: center;
        font-weight: 700;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Card styling */
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    div[data-testid="stExpander"] div[role="button"] {
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1rem;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), #2b6cb0) !important;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border-radius: 6px;
    }
    
    /* Input fields */
    input, select, textarea {
        border: 1px solid #cbd5e0 !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
    }
    
    /* Dataframe styling */
    div[data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Success and error messages */
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }
    
    /* Download button */
    a[data-baseweb="button"] {
        background-color: var(--success) !important;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 500;
    }
    
    /* Section headers */
    h2, h3 {
        color: var(--primary);
    }
    
    h3 {
        border-bottom: 2px solid var(--accent);
        padding-bottom: 0.5rem;
    }
    
    /* Info box */
    div[data-testid="stExpander"] div[role="button"] p {
        color: var(--primary);
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("""
<div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #0a2540, #1a365d); margin-bottom: 2rem; border-radius: 0 0 10px 10px;">
    <h1>💰 Dividend & Gain/Loss Calculator</h1>
    <p style="color: #cbd5e0; font-size: 1.2rem; margin-top: 0.5rem;">
        Track your investment performance with dividend reinvestment calculations
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
if 'results' not in st.session_state:
    st.session_state.results = None

# Sidebar for inputs
with st.sidebar:
    st.markdown("## 📊 Investment Details")
    
    # Main inputs with icons
    ticker = st.text_input("📈 Ticker Symbol", value="AAPL", key="ticker_input", 
                          help="Enter stock symbol (e.g., AAPL, MSFT)")
    purchase_date = st.date_input("📅 Purchase Date", value=date(2020, 1, 1), key="date_input",
                                 help="Date of initial purchase")
    shares = st.number_input("📊 Number of Shares", min_value=0.0, value=10.0, step=1.0, key="shares_input",
                            help="Initial shares purchased")
    cost_basis = st.number_input("💵 Cost Basis per Share ($)", min_value=0.0, value=100.0, step=1.0, key="cost_input",
                                help="Purchase price per share")
    drip = st.checkbox("🔁 Dividends Reinvested (DRIP)", value=True, key="drip_input",
                      help="Check if dividends are automatically reinvested")
    
    st.markdown("---")
    st.markdown("## ➕ Additional Purchases")
    
    # Number of additional purchases
    num_additional = st.number_input("Number of Additional Purchases", min_value=0, value=0, step=1, key="num_add_input")
    
    # Store additional purchases
    additional_purchases = []
    for i in range(num_additional):
        st.markdown(f"### Purchase {i+1}")
        add_date = st.date_input(f"📅 Date", key=f"add_date_{i}")
        add_shares = st.number_input(f"📊 Shares", min_value=0.0, value=0.0, step=1.0, key=f"add_shares_{i}")
        add_price = st.number_input(f"💵 Price per Share ($)", min_value=0.0, value=0.0, step=1.0, key=f"add_price_{i}")
        additional_purchases.append({
            'date': add_date,
            'shares': add_shares,
            'price': add_price
        })
    
    st.markdown("---")
    st.markdown("### ℹ️ How to Use")
    st.markdown("""
    1. Enter your investment details
    2. Add any additional purchases
    3. Click 'Calculate Performance'
    4. View results and download CSV
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## 📈 Investment Information")
    
    # Display current inputs
    with st.expander("Current Investment Details", expanded=True):
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div style="background: #f1f5f9; padding: 1rem; border-radius: 8px;">
                <p style="margin: 0; color: #4a5568; font-size: 0.9rem;">Ticker</p>
                <h3 style="margin: 0.25rem 0 0;">{ticker}</h3>
            </div>
            <div style="background: #f1f5f9; padding: 1rem; border-radius: 8px;">
                <p style="margin: 0; color: #4a5568; font-size: 0.9rem;">Initial Purchase</p>
                <h3 style="margin: 0.25rem 0 0;">{purchase_date}</h3>
            </div>
            <div style="background: #f1f5f9; padding: 1rem; border-radius: 8px;">
                <p style="margin: 0; color: #4a5568; font-size: 0.9rem;">Initial Shares</p>
                <h3 style="margin: 0.25rem 0 0;">{shares:,.2f}</h3>
            </div>
            <div style="background: #f1f5f9; padding: 1rem; border-radius: 8px;">
                <p style="margin: 0; color: #4a5568; font-size: 0.9rem;">Cost Basis</p>
                <h3 style="margin: 0.25rem 0 0;">${cost_basis:,.2f}</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="margin-top: 1rem; padding: 1rem; background: {'#e6fffa' if drip else '#fed7d7'}; border-radius: 8px; text-align: center;">
            <p style="margin: 0; font-weight: 600; color: {'#234e52' if drip else '#822727'};">
                Dividends Reinvested: {'✅ YES' if drip else '❌ NO'}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if num_additional > 0:
            st.markdown("### Additional Purchases")
            for i, purchase in enumerate(additional_purchases):
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: #f8fafc; border-radius: 6px; margin-bottom: 0.5rem; border: 1px solid #e2e8f0;">
                    <div>
                        <strong>Purchase {i+1}</strong><br>
                        <small>{purchase['date']}</small>
                    </div>
                    <div style="text-align: right;">
                        {purchase['shares']} shares<br>
                        <strong>${purchase['price']:,.2f}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

with col2:
    st.markdown("## 🧮 Calculate Results")
    
    # Calculate button with icon
    if st.button("📊 Calculate Investment Performance", type="primary", use_container_width=True):
        with st.spinner("Fetching financial data and calculating..."):
            try:
                # Fetch stock data
                stock = yf.Ticker(ticker)
                hist = stock.history(start=purchase_date)
                
                if hist.empty:
                    st.error("❌ No data found for this ticker and date range")
                else:
                    # Calculate total cost basis
                    total_cost = shares * cost_basis
                    total_shares = shares

                    # Process additional purchases
                    for purchase in additional_purchases:
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
                            if additional_purchases:
                                valid_dates = [p['date'] for p in additional_purchases if p['date']]
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
                            valid_purchases = [p for p in additional_purchases if p['date']]
                            if valid_purchases:
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
                            total_dividends = dividends.sum() * shares
                            for purchase in valid_purchases:
                                if purchase['date']:
                                    purchase_dividends = dividends[dividends.index >= purchase['date']].sum()
                                    total_dividends += purchase_dividends * purchase['shares']
                        else:
                            drip_shares = 0
                            total_dividends = dividends.sum() * total_shares if not dividends.empty else 0
                        
                    except Exception:
                        total_dividends = 0
                        drip_shares = 0

                    # Calculate current value
                    current_value = total_shares * current_price

                    # Calculate gains/losses
                    total_gain_loss = current_value + total_dividends - total_cost
                    total_gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0

                    # Store results
                    st.session_state.results = {
                        'Ticker': ticker,
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
                    st.success("✅ Calculation complete!")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display results if available
    if st.session_state.calculated and st.session_state.results:
        st.markdown("---")
        st.markdown("## 📥 Export Results")
        
        # Download button
        csv = pd.DataFrame([st.session_state.results]).to_csv(index=False)
        st.download_button(
            label="💾 Download CSV Report",
            data=csv,
            file_name=f"{st.session_state.results['Ticker']}_investment_summary.csv",
            mime="text/csv",
            use_container_width=True
        )

# Results display area
if st.session_state.calculated and st.session_state.results:
    st.markdown("---")
    st.markdown("## 📊 Investment Summary")
    
    # Key metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Current Value", f"${st.session_state.results['Current Value']:,.2f}")
    
    with col2:
        st.metric("💸 Total Dividends", f"${st.session_state.results['Total Dividends']:,.2f}")
    
    with col3:
        color = "normal" if st.session_state.results['Total Gain/Loss'] >= 0 else "inverse"
        st.metric(
            "📊 Total Gain/Loss", 
            f"${st.session_state.results['Total Gain/Loss']:,.2f}",
            delta_color=color
        )
    
    with col4:
        color = "normal" if st.session_state.results['Total Gain/Loss %'] >= 0 else "inverse"
        st.metric(
            "📈 Return %", 
            f"{st.session_state.results['Total Gain/Loss %']:,.2f}%",
            delta_color=color
        )
    
    # Progress bar for visual representation
    st.markdown("### Performance Visualization")
    performance_percent = st.session_state.results['Total Gain/Loss %']
    performance_color = "#38a169" if performance_percent >= 0 else "#e53e3e"
    st.markdown(f"""
    <div style="background: #e2e8f0; border-radius: 10px; height: 30px; overflow: hidden;">
        <div style="width: {min(abs(performance_percent), 100)}%; height: 100%; background: {performance_color}; 
                    display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
            {performance_percent:.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Detailed results table
    st.markdown("### Detailed Breakdown")
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
    st.markdown("### Share Composition")
    share_col1, share_col2, share_col3, share_col4 = st.columns(4)
    
    with share_col1:
        st.metric("Initial Shares", f"{st.session_state.results['Initial Shares']:,.2f}")
    
    with share_col2:
        st.metric("Additional Shares", f"{st.session_state.results['Additional Shares']:,.2f}")
    
    with share_col3:
        st.metric("DRIP Shares", f"{st.session_state.results['DRIP Shares']:,.4f}")
    
    with share_col4:
        st.metric("Total Shares", f"{st.session_state.results['Total Shares']:,.4f}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; padding: 1rem;">
    <p>Dividend & Gain/Loss Calculator | Data provided by Yahoo Finance</p>
    <p style="font-size: 0.9rem;">© 2023 Investment Analytics Tool</p>
</div>
""", unsafe_allow_html=True)