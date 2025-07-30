import streamlit as st
import pandas as pd
from datetime import datetime

# Try to import yfinance, install if not available
try:
    import yfinance as yf
except ImportError:
    st.error("yfinance not installed. Please check requirements.txt")
    st.stop()

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

def calculate_metrics():
    # Get inputs
    ticker = st.session_state.ticker.upper()
    purchase_date = st.session_state.purchase_date
    shares = st.session_state.shares
    cost_basis = st.session_state.cost_basis
    drip = st.session_state.drip
    additional_purchases = st.session_state.additional_purchases

    try:
        # Fetch stock data
        with st.spinner(f"Fetching data for {ticker}..."):
            stock = yf.Ticker(ticker)
            hist = stock.history(start=purchase_date)
        
        if hist.empty:
            st.error("No data found for this ticker and date range")
            return None

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
            
        except Exception as e:
            total_dividends = 0
            drip_shares = 0

        # Calculate current value
        current_value = total_shares * current_price

        # Calculate gains/losses
        total_gain_loss = current_value + total_dividends - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0

        return {
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
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
        return None

# Streamlit UI
st.set_page_config(page_title="Dividend & Gain Calculator", layout="wide")
st.title("📈 Dividend & Total Gain/Loss Calculator")

# Sidebar for inputs
with st.sidebar:
    st.header("Investment Details")
    ticker = st.text_input("Ticker Symbol", value="AAPL", key="ticker")
    purchase_date = st.date_input("Purchase Date", value=datetime(2020, 1, 1), key="purchase_date")
    shares = st.number_input("Number of Shares", min_value=0.0, value=10.0, key="shares")
    cost_basis = st.number_input("Cost Basis per Share ($)", min_value=0.0, value=100.0, key="cost_basis")
    drip = st.checkbox("Dividends Reinvested (DRIP)", value=True, key="drip")
    
    st.subheader("Additional Purchases")
    num_additional = st.number_input("Number of Additional Purchases", min_value=0, value=0, step=1)
    
    # Initialize additional purchases in session state
    if 'additional_purchases' not in st.session_state:
        st.session_state.additional_purchases = []
    
    # Adjust additional purchases list size
    while len(st.session_state.additional_purchases) < num_additional:
        st.session_state.additional_purchases.append({
            'date': None,
            'shares': 0.0,
            'price': 0.0
        })
    while len(st.session_state.additional_purchases) > num_additional:
        st.session_state.additional_purchases.pop()
    
    # Create inputs for additional purchases
    for i in range(num_additional):
        st.markdown(f"**Purchase {i+1}**")
        st.session_state.additional_purchases[i]['date'] = st.date_input(
            f"Date {i+1}", 
            key=f"date_{i}"
        )
        st.session_state.additional_purchases[i]['shares'] = st.number_input(
            f"Shares {i+1}", 
            min_value=0.0, 
            value=0.0,
            key=f"shares_{i}"
        )
        st.session_state.additional_purchases[i]['price'] = st.number_input(
            f"Price {i+1} ($)", 
            min_value=0.0, 
            value=0.0,
            key=f"price_{i}"
        )

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Calculate", type="primary", use_container_width=True):
        with st.spinner("Calculating..."):
            st.session_state.results = calculate_metrics()

with col2:
    if st.session_state.results:
        csv = pd.DataFrame([st.session_state.results]).to_csv(index=False)
        st.download_button(
            label="Download Results (CSV)",
            data=csv,
            file_name=f"{st.session_state.results['Ticker']}_investment_summary.csv",
            mime="text/csv",
            use_container_width=True
        )

# Display results
if st.session_state.results:
    st.subheader("Results")
    results_df = pd.DataFrame([st.session_state.results])
    st.dataframe(results_df.style.format({
        'Total Cost Basis': '${:,.2f}',
        'Current Price': '${:,.2f}',
        'Current Value': '${:,.2f}',
        'Total Dividends': '${:,.2f}',
        'Total Gain/Loss': '${:,.2f}',
        'Total Gain/Loss %': '{:,.2f}%'
    }), use_container_width=True)
    
    # Visualization
    st.subheader("Performance Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Value", f"${st.session_state.results['Current Value']:,.2f}")
    
    with col2:
        st.metric("Total Dividends", f"${st.session_state.results['Total Dividends']:,.2f}")
    
    with col3:
        st.metric(
            "Total Gain/Loss", 
            f"${st.session_state.results['Total Gain/Loss']:,.2f}",
            f"{st.session_state.results['Total Gain/Loss %']:,.2f}%",
            delta_color=("normal" if st.session_state.results['Total Gain/Loss'] >= 0 else "inverse")
        )

# Instructions
st.info("""
**How to use:**
1. Enter your stock ticker symbol (e.g., AAPL)
2. Set your initial purchase date and share details
3. Indicate if dividends are reinvested (DRIP)
4. Add any additional share purchases
5. Click "Calculate" to see results
6. Download results as CSV for spreadsheet use
""")