import streamlit as st
import json
import os
import pandas as pd

# ---- Page Config ----
st.set_page_config(page_title="Aven POS Dashboard", page_icon="📊", layout="wide")

DATA_FILE = "data_pos_aven.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"stock": {}, "sales": [], "total_revenue": 0.0, "total_profit": 0.0, "items_sold": 0}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"stock": {}, "sales": [], "total_revenue": 0.0, "total_profit": 0.0, "items_sold": 0}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ---- Sidebar Navigation ----
st.sidebar.title("🛸 AVEN CORE")
st.sidebar.subheader("Navigation")
menu = st.sidebar.radio("Go to:", ["📊 Dashboard & Analytics", "📦 Stock Management", "🛒 Sales POS", "📜 Sales History"])

# ---- 1. DASHBOARD ----
if menu == "📊 Dashboard & Analytics":
    st.title("📊 Aven POS Dashboard & Analytics")
    
    # Metrics Cards
    col1, col2, col3 = st.columns(3)
    col1.metric(label="💰 Total Revenue", value=f"{data['total_revenue']:.2f} TK")
    col2.metric(label="📈 Total Net Profit", value=f"{data['total_profit']:.2f} TK")
    col3.metric(label="🛒 Total Items Sold", value=str(data['items_sold']))
    
    st.markdown("---")
    st.subheader("📦 Current Stock Alert Summary")
    if not data['stock']:
        st.info("No items in stock yet.")
    else:
        df_stock = pd.DataFrame.from_dict(data['stock'], orient='index')
        df_stock.index.name = 'Product Code'
        df_stock = df_stock.rename(columns={'name': 'Product Name', 'buying': 'Buying Price', 'price': 'Selling Price', 'qty': 'Available Qty'})
        st.dataframe(df_stock, use_container_width=True)

# ---- 2. STOCK MANAGEMENT ----
elif menu == "📦 Stock Management":
    st.title("📦 Stock Management")
    
    with st.form("stock_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("Product Code (e.g. AVN-TS-01)").upper().strip()
            name = st.text_input("Product Name")
        with col2:
            buying = st.number_input("Buying Price (TK)", min_value=0.0, step=1.0)
            price = st.number_input("Selling Price (TK)", min_value=0.0, step=1.0)
            qty = st.number_input("Quantity", min_value=1, step=1)
            
        submitted = st.form_submit_button("➕ Add / Update Product")
        
        if submitted:
            if code and name:
                if code in data['stock']:
                    data['stock'][code]['qty'] += qty
                    data['stock'][code]['name'] = name
                    data['stock'][code]['price'] = price
                    data['stock'][code]['buying'] = buying
                else:
                    data['stock'][code] = {"name": name, "buying": buying, "price": price, "qty": qty}
                save_data(data)
                st.success(f"Product [{code}] successfully committed to database!")
                st.rerun()
            else:
                st.error("Please fill up Product Code and Name.")

    st.subheader("📂 Stock Database Logs")
    if data['stock']:
        df_stock = pd.DataFrame.from_dict(data['stock'], orient='index')
        st.dataframe(df_stock, use_container_width=True)

# ---- 3. SALES POS ----
elif menu == "🛒 Sales POS":
    st.title("🛒 Sales Point of Sale (POS)")
    
    if not data['stock']:
        st.warning("No stock available to sell. Please add products first.")
    else:
        code_list = list(data['stock'].keys())
        selected_code = st.selectbox("Select Product Code:", code_list)
        
        if selected_code:
            p_info = data['stock'][selected_code]
            st.info(f"⚡ Product: **{p_info['name']}** | Available Qty: **{p_info['qty']}** | Price: **{p_info['price']:.2f} TK**")
            
            sqty = st.number_input("Quantity to Sell:", min_value=1, max_value=int(p_info['qty']), step=1)
            
            if st.button("🛒 Complete Transaction"):
                revenue = p_info['price'] * sqty
                profit = (p_info['price'] - p_info['buying']) * sqty
                
                # Update database
                data['stock'][selected_code]['qty'] -= sqty
                data['total_revenue'] += revenue
                data['total_profit'] += profit
                data['items_sold'] += sqty
                data['sales'].append({"code": selected_code, "product": p_info['name'], "qty": sqty, "total_bill": revenue})
                
                save_data(data)
                st.success(f"Successfully Sold {sqty}x {p_info['name']}! Total Bill: {revenue:.2f} TK")
                st.rerun()

# ---- 4. SALES HISTORY ----
elif menu == "📜 Sales History":
    st.title("📜 Permanent Sales Logs")
    if not data['sales']:
        st.info("No sales recorded yet.")
    else:
        df_sales = pd.DataFrame(data['sales'])
        df_sales = df_sales.rename(columns={'code': 'Product Code', 'product': 'Product Name', 'qty': 'Quantity', 'total_bill': 'Total Bill (TK)'})
        st.dataframe(df_sales, use_container_width=True)