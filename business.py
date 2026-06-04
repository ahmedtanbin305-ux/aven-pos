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
    # Unique key combined of name and size to avoid mixups
    return {f"{item['name']} (Size: {item.get('size', 'N/A')})": item for item in data["stock"]}

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
        sale_key = f"{s['name']} (Size: {s.get('size', 'N/A')})"
        if sale_key in stock_dict:
            buy_price = stock_dict[sale_key]["buy_price"]
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
                "Product Code": item.get("code", "N/A"),
                "Product Name": item["name"],
                "Size": item.get("size", "N/A"),
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
    
    # --- SEARCH BY PRODUCT CODE ---
    st.subheader("🔍 Instant Code Search (Stock Checker)")
    search_code = st.text_input("Enter Product Code to check stock instantly:", placeholder="Type code here...").strip()
    
    if search_code:
        found_item = None
        for item in data["stock"]:
            if item.get("code", "").lower() == search_code.lower():
                found_item = item
                break
        
        if found_item:
            st.success(f"🎉 Product Found!")
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Product Name", found_item["name"])
            sc2.metric("Size", found_item.get("size", "N/A"))
            sc3.metric("Available Stock", f"{found_item['quantity']} units")
            sc4.metric("Selling Price", f"{found_item['sell_price']} tk")
            
            # Show status color
            if found_item["quantity"] <= 0:
                sc5.error("🔴 Out of Stock")
            elif found_item["quantity"] <= 5:
                sc5.warning("🟡 Low Stock Alert")
            else:
                sc5.info("🟢 Safe In Stock")
        else:
            st.error(f"❌ No product found with Code: '{search_code}'")
            
    st.markdown("---")
    
    # Form to Add/Edit Product
    st.subheader("📝 Add / Edit Product Information")
    with st.form("product_form", clear_on_submit=True):
        if st.session_state.edit_mode:
            st.warning(f"Editing Product: {data['stock'][st.session_state.edit_index]['name']}")
            default_code = data["stock"][st.session_state.edit_index].get("code", "")
            default_name = data["stock"][st.session_state.edit_index]["name"]
            default_size = data["stock"][st.session_state.edit_index].get("size", "")
            default_qty = data["stock"][st.session_state.edit_index]["quantity"]
            default_buy = data["stock"][st.session_state.edit_index]["buy_price"]
            default_sell = data["stock"][st.session_state.edit_index]["sell_price"]
            button_label = "Update Product"
        else:
            default_code = ""
            default_name = ""
            default_size = ""
            default_qty = 0
            default_buy = 0.0
            default_sell = 0.0
            button_label = "Add Product to Stock"

        prod_code = st.text_input("Product Code / Barcode (Unique):", value=default_code).strip()
        
        col_n, col_s = st.columns([3, 1])
        prod_name = col_n.text_input("Product Name:", value=default_name)
        prod_size = col_s.text_input("Size (e.g. M, XL, 42):", value=default_size).strip()
        
        prod_qty = st.number_input("Quantity:", min_value=0, step=1, value=default_qty)
        prod_buy = st.number_input("Buying Price per item (BDT):", min_value=0.0, step=0.5, value=default_buy)
        prod_sell = st.number_input("Selling Price per item (BDT):", min_value=0.0, step=0.5, value=default_sell)
        
        submitted = st.form_submit_with_button(button_label)
        
        if submitted:
            if not prod_code:
                st.error("Product Code cannot be empty!")
            elif not prod_name:
                st.error("Product name cannot be empty!")
            elif prod_sell < prod_buy:
                st.error("Selling price should not be less than buying price!")
            else:
                final_size = prod_size if prod_size else "N/A"
                
                if st.session_state.edit_mode:
                    # Update Existing
                    data["stock"][st.session_state.edit_index] = {
                        "code": prod_code,
                        "name": prod_name,
                        "size": final_size,
                        "quantity": prod_qty,
                        "buy_price": prod_buy,
                        "sell_price": prod_sell
                    }
                    st.success(f"Product '{prod_name}' updated successfully!")
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = -1
                else:
                    # Check if duplicate code or name+size combo
                    existing_codes = [str(i.get("code", "")).lower() for i in data["stock"]]
                    existing_combos = [f"{i['name'].lower()}-{str(i.get('size','N/A')).lower()}" for i in data["stock"]]
                    current_combo = f"{prod_name.lower()}-{final_size.lower()}"
                    
                    if prod_code.lower() in existing_codes:
                        st.error("This Product Code already exists! Each product must have a unique code.")
                    elif current_combo in existing_combos:
                        st.error(f"Product '{prod_name}' with Size '{final_size}' already exists! Please edit the existing item.")
                    else:
                        # Add New
                        data["stock"].append({
                            "code": prod_code,
                            "name": prod_name,
                            "size": final_size,
                            "quantity": prod_qty,
                            "buy_price": prod_buy,
                            "sell_price": prod_sell
                        })
                        st.success(f"Product '{prod_name}' (Size: {final_size}) added to stock!")
                
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
            col0, col1, col_sz, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 0.8, 0.8, 1.2, 1.2, 0.5, 0.5])
            col0.write(f"`Code: {item.get('code', 'N/A')}`")
            col1.write(f"**{item['name']}**")
            col_sz.write(f"Size: {item.get('size', 'N/A')}")
            col2.write(f"Qty: {item['quantity']}")
            col3.write(f"Buy: {item['buy_price']} tk")
            col4.write(f"Sell: {item['sell_price']} tk")
            
            if col5.button("✏️", key=f"edit_{idx}"):
                st.session_state.edit_mode = True
                st.session_state.edit_index = idx
                st.rerun()
                
            if col6.button("🗑️", key=f"del_{idx}"):
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
        # Create select options displaying Code + Name + Size
        available_products = []
        product_map = {} # Maps the option string back to a unique map identifier
        
        for idx, item in enumerate(data["stock"]):
            if item["quantity"] > 0:
                display_string = f"[{item.get('code', 'N/A')}] {item['name']} (Size: {item.get('size', 'N/A')})"
                available_products.append(display_string)
                product_map[display_string] = idx
        
        if not available_products:
            st.error("All products are currently OUT OF STOCK! Please update stock levels.")
        else:
            st.subheader("New Instant Sale Transaction")
            
            selected_option = st.selectbox("Search/Select Product (By Code, Name or Size):", available_products)
            target_idx = product_map[selected_option]
            
            matched_item = data["stock"][target_idx]
            max_qty = matched_item["quantity"]
            
            st.info(f"Available Quantity in Stock: {max_qty} units | Standard Price: {matched_item['sell_price']} tk")
            
            sell_qty = st.number_input("Quantity to Sell:", min_value=1, max_value=max_qty, step=1, value=1)
            custom_price = st.number_input("Custom Selling Price per unit (BDT) [Optional]:", 
                                           min_value=0.0, 
                                           value=float(matched_item['sell_price']), 
                                           step=0.5)
            
            total_payable = sell_qty * custom_price
            st.markdown(f"### 💰 Total Payable Amount: **{total_payable:,.2f} tk**")
            
            if st.button("✅ Complete Sale & Print Entry"):
                # Deduct inventory qty directly using index
                data["stock"][target_idx]["quantity"] -= sell_qty
                
                # Record the sale log (saving size as well)
                sale_entry = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": matched_item["name"],
                    "size": matched_item.get("size", "N/A"),
                    "quantity": sell_qty,
                    "sell_price": custom_price,
                    "total_price": total_payable
                }
                data["sales"].append(sale_entry)
                
                save_data(data)
                st.success(f"Sale successful! Sold {sell_qty} units of '{matched_item['name']}' (Size: {matched_item.get('size', 'N/A')}).")
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
                "Size": sale.get("size", "N/A"),
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
