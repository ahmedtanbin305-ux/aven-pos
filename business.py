import streamlit as st
import json
from datetime import datetime, timedelta
import os

# --- Configuration ---
st.set_page_config(page_title="Aven POS Dashboard", page_icon="🏪", layout="wide")

DB_FILE = "business.json"
st.sidebar.image("logo.png", use_container_width=True)

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"stock": [], "sales": []}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# Edit করার জন্য টেম্পোরারি স্টেট
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "edit_index" not in st.session_state:
    st.session_state.edit_index = -1

# --- Navigation ---
st.sidebar.title("🏪 Aven POS Navigation")
page = st.sidebar.radio("Go to:", ["📊 Dashboard & Analytics", "📦 Stock Management", "🛒 Sales POS", "📜 Sales History"])

# --- Helper Functions for Calculations ---
def get_stock_dict():
    return {item["name"]: item for item in data["stock"]}

# --- PAGE 1: DASHBOARD & ANALYTICS ---
if page == "📊 Dashboard & Analytics":
    st.title("📊 Aven POS Dashboard & Analytics")
    
    # Time Filters
    filter_option = st.selectbox("Select Time Range:", ["Today", "Last 7 Days", "This Month", "All Time"])
    
    now = datetime.now()
    sales_filtered = []
    
    for sale in data["sales"]:
        try:
            sale_date = datetime.strptime(sale["date"], "%Y-%m-%d %H:%M:%S")
        except:
            try:
                sale_date = datetime.strptime(sale["date"], "%Y-%m-%d")
            except:
                continue
                
        if filter_option == "Today" and sale_date.date() == now.date():
            sales_filtered.append(sale)
        elif filter_option == "Last 7 Days" and sale_date >= now - timedelta(days=7):
            sales_filtered.append(sale)
        elif filter_option == "This Month" and sale_date.month == now.month and sale_date.year == now.year:
            sales_filtered.append(sale)
        elif filter_option == "All Time":
            sales_filtered.append(sale)

    # Metrics Calculations
    total_sales_revenue = sum(s["total_price"] for s in sales_filtered)
    total_items_sold = sum(s["quantity"] for s in sales_filtered)
    
    # Calculate Total Profit
    stock_dict = get_stock_dict()
    total_profit = 0
    for s in sales_filtered:
        if s["name"] in stock_dict:
            buy_price = stock_dict[s["name"]]["buy_price"]
            profit_per_item = s["sell_price"] - buy_price
            total_profit += profit_per_item * s["quantity"]

    # Top KPI Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Revenue (BDT)", f"{total_sales_revenue:,.2f} tk")
    col2.metric("📈 Total Net Profit (BDT)", f"{total_profit:,.2f} tk")
    col3.metric("🛒 Total Items Sold", total_items_sold)

    st.markdown("---")
    
    # Stock Summary View
    st.subheader("📦 Quick Stock Alert & Summary")
    if data["stock"]:
        stock_df = []
        for item in data["stock"]:
            status = "✅ In Stock"
            if item["quantity"] <= 0:
                status = "❌ Out of Stock"
            elif item["quantity"] <= 5:
                status = "⚠️ Low Stock"
                
            stock_df.append({
                "Product Name": item["name"],
                "Quantity Left": item["quantity"],
                "Buying Price (tk)": f"{item['buy_price']:.2f}",
                "Selling Price (tk)": f"{item['sell_price']:.2f}",
                "Status": status
            })
        st.table(stock_df)
    else:
        st.info("No items in stock yet. Go to Stock Management to add items.")

# --- PAGE 2: STOCK MANAGEMENT ---
elif page == "📦 Stock Management":
    st.title("📦 Stock & Product Management")
    
    # Form to Add/Edit Product
    st.subheader("📝 Add / Edit Product Information")
    with st.form("product_form", clear_on_submit=True):
        if st.session_state.edit_mode:
            st.warning(f"Editing Product: {data['stock'][st.session_state.edit_index]['name']}")
            default_name = data["stock"][st.session_state.edit_index]["name"]
            default_qty = data["stock"][st.session_state.edit_index]["quantity"]
            default_buy = data["stock"][st.session_state.edit_index]["buy_price"]
            default_sell = data["stock"][st.session_state.edit_index]["sell_price"]
            button_label = "Update Product"
        else:
            default_name = ""
            default_qty = 0
            default_buy = 0.0
            default_sell = 0.0
            button_label = "Add Product to Stock"

        prod_name = st.text_input("Product Name:", value=default_name)
        prod_qty = st.number_input("Quantity:", min_value=0, step=1, value=default_qty)
        prod_buy = st.number_input("Buying Price per item (BDT):", min_value=0.0, step=0.5, value=default_buy)
        prod_sell = st.number_input("Selling Price per item (BDT):", min_value=0.0, step=0.5, value=default_sell)
        
        submitted = st.form_submit_with_button(button_label)
        
        if submitted:
            if not prod_name:
                st.error("Product name cannot be empty!")
            elif prod_sell < prod_buy:
                st.error("Selling price should not be less than buying price!")
            else:
                if st.session_state.edit_mode:
                    # Update Existing
                    data["stock"][st.session_state.edit_index] = {
                        "name": prod_name,
                        "quantity": prod_qty,
                        "buy_price": prod_buy,
                        "sell_price": prod_sell
                    }
                    st.success(f"Product '{prod_name}' updated successfully!")
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = -1
                else:
                    # Check if duplicate name
                    existing_names = [i["name"].lower() for i in data["stock"]]
                    if prod_name.lower() in existing_names:
                        st.error("Product with this name already exists! Please edit the existing item instead.")
                    else:
                        # Add New
                        data["stock"].append({
                            "name": prod_name,
                            "quantity": prod_qty,
                            "buy_price": prod_buy,
                            "sell_price": prod_sell
                        })
                        st.success(f"Product '{prod_name}' added to stock!")
                
                save_data(data)
                st.rerun()

    if st.session_state.edit_mode:
        if st.button("Cancel Edit"):
            st.session_state.edit_mode = False
            st.session_state.edit_index = -1
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Current Inventory List")
    
    if data["stock"]:
        for idx, item in enumerate(data["stock"]):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1.5, 1.5, 1, 1])
            col1.write(f"**{item['name']}**")
            col2.write(f"Qty: {item['quantity']}")
            col3.write(f"Buy: {item['buy_price']} tk")
            col4.write(f"Sell: {item['sell_price']} tk")
            
            if col5.button("✏️ Edit", key=f"edit_{idx}"):
                st.session_state.edit_mode = True
                st.session_state.edit_index = idx
                st.rerun()
                
            if col6.button("🗑️ Delete", key=f"del_{idx}"):
                deleted_name = data["stock"].pop(idx)["name"]
                save_data(data)
                st.success(f"Deleted '{deleted_name}' from inventory.")
                st.rerun()
    else:
        st.info("Inventory is empty.")

# --- PAGE 3: SALES POS ---
elif page == "🛒 Sales POS":
    st.title("🛒 Sales Point of Sale (POS)")
    
    if not data["stock"]:
        st.warning("Please add products to your stock before starting sales!")
    else:
        stock_dict = get_stock_dict()
        available_products = [item["name"] for item in data["stock"] if item["quantity"] > 0]
        
        if not available_products:
            st.error("All products are currently OUT OF STOCK! Please update stock levels.")
        else:
            st.subheader("New Instant Sale Transaction")
            
            selected_product = st.selectbox("Select Product to Sell:", available_products)
            max_qty = stock_dict[selected_product]["quantity"]
            st.info(f"Available Quantity in Stock: {max_qty} units | Standard Price: {stock_dict[selected_product]['sell_price']} tk")
            
            sell_qty = st.number_input("Quantity to Sell:", min_value=1, max_value=max_qty, step=1, value=1)
            custom_price = st.number_input("Custom Selling Price per unit (BDT) [Optional]:", 
                                           min_value=0.0, 
                                           value=float(stock_dict[selected_product]['sell_price']), 
                                           step=0.5)
            
            total_payable = sell_qty * custom_price
            st.markdown(f"### 💰 Total Payable Amount: **{total_payable:,.2f} tk**")
            
            if st.button("✅ Complete Sale & Print Entry"):
                # Deduct inventory qty
                for item in data["stock"]:
                    if item["name"] == selected_product:
                        item["quantity"] -= sell_qty
                        break
                
                # Record the sale log
                sale_entry = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": selected_product,
                    "quantity": sell_qty,
                    "sell_price": custom_price,
                    "total_price": total_payable
                }
                data["sales"].append(sale_entry)
                
                save_data(data)
                st.success(f"Sale successful! Sold {sell_qty} units of '{selected_product}'. Stock automatically updated.")
                st.rerun()

# --- PAGE 4: SALES HISTORY ---
elif page == "📜 Sales History":
    st.title("📜 Sales Records & Invoice History")
    
    if data["sales"]:
        # Inverse order to see latest sales first
        reversed_sales = list(reversed(data["sales"]))
        
        sales_log_table = []
        for idx, sale in enumerate(reversed_sales):
            sales_log_table.append({
                "Date & Time": sale["date"],
                "Item Name": sale["name"],
                "Qty Sold": sale["quantity"],
                "Price/Unit (tk)": f"{sale['sell_price']:.2f}",
                "Total Paid (tk)": f"{sale['total_price']:.2f}"
            })
            
        st.table(sales_log_table)
        
        st.markdown("---")
        if st.button("🗑️ Clear Entire Sales History Log"):
            if st.checkbox("Yes, I am absolutely sure I want to wipe out all data permanently."):
                data["sales"] = []
                save_data(data)
                st.success("All historical sales entries wiped successfully!")
                st.rerun()
    else:
        st.info("No sales transactions recorded yet.")
