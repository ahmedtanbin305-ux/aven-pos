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
    return {f"{item['name']} (Size: {item.get('size', 'N/A')})": item for item in data["stock"]}

# --- PAGE 1: DASHBOARD & ANALYTICS ---
if page == "📊 Dashboard & Analytics":
    st.title("📊 Aven POS Dashboard & Analytics")
    
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

    total_sales_revenue = sum(s["total_price"] for s in sales_filtered)
    total_items_sold = sum(s["quantity"] for s in sales_filtered)
    
    stock_dict = get_stock_dict()
    total_profit = 0
    for s in sales_filtered:
        sale_key = f"{s['name']} (Size: {s.get('size', 'N/A')})"
        if sale_key in stock_dict:
            buy_price = stock_dict[sale_key]["buy_price"]
            profit_per_item = s["sell_price"] - buy_price
            total_profit += profit_per_item * s["quantity"]

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Revenue (BDT)", f"{total_sales_revenue:,.2f} tk")
    col2.metric("📈 Total Net Profit (BDT)", f"{total_profit:,.2f} tk")
    col3.metric("🛒 Total Items Sold", total_items_sold)

    st.markdown("---")
    
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
        st.info("No items in stock yet.")

# --- PAGE 2: STOCK MANAGEMENT ---
elif page == "📦 Stock Management":
    st.title("📦 Stock & Product Management")
    
    st.subheader("🔍 Instant Code Search")
    search_code = st.text_input("Enter Product Code to check stock instantly:", placeholder="Type code...").strip()
    
    if search_code:
        found_item = None
        for item in data["stock"]:
            if str(item.get("code", "")).lower() == search_code.lower():
                found_item = item
                break
        
        if found_item:
            st.success(f"🎉 Product Found!")
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Product Name", found_item["name"])
            sc2.metric("Size", found_item.get("size", "N/A"))
            sc3.metric("Available Stock", f"{found_item['quantity']} units")
            sc4.metric("Selling Price", f"{found_item['sell_price']} tk")
            if found_item["quantity"] <= 0: sc5.error("🔴 Out of Stock")
            elif found_item["quantity"] <= 5: sc5.warning("🟡 Low Stock")
            else: sc5.info("🟢 In Stock")
        else:
            st.error(f"❌ No product found with Code: '{search_code}'")
            
    st.markdown("---")
    
    st.subheader("📝 Add / Edit Product Information")
    with st.form("product_form", clear_on_submit=True):
        if st.session_state.edit_mode:
            st.warning(f"Editing: {data['stock'][st.session_state.edit_index]['name']}")
            default_code = data["stock"][st.session_state.edit_index].get("code", "")
            default_name = data["stock"][st.session_state.edit_index]["name"]
            default_size = data["stock"][st.session_state.edit_index].get("size", "")
            default_qty = data["stock"][st.session_state.edit_index]["quantity"]
            default_buy = data["stock"][st.session_state.edit_index]["buy_price"]
            default_sell = data["stock"][st.session_state.edit_index]["sell_price"]
            button_label = "Update Product"
        else:
            default_code, default_name, default_size = "", "", ""
            default_qty, default_buy, default_sell = 0, 0.0, 0.0
            button_label = "Add Product to Stock"

        prod_code = st.text_input("Product Code / Barcode:", value=default_code).strip()
        col_n, col_s = st.columns([3, 1])
        prod_name = col_n.text_input("Product Name:", value=default_name)
        prod_size = col_s.text_input("Size (e.g. M, 42):", value=default_size).strip()
        prod_qty = st.number_input("Quantity:", min_value=0, step=1, value=default_qty)
        prod_buy = st.number_input("Buying Price (BDT):", min_value=0.0, step=0.5, value=default_buy)
        prod_sell = st.number_input("Selling Price (BDT):", min_value=0.0, step=0.5, value=default_sell)
        
        # CORRECTED LINE BELOW
        submitted = st.form_submit_button(button_label)
        
        if submitted:
            if not prod_code or not prod_name:
                st.error("Code and Name are required!")
            else:
                final_size = prod_size if prod_size else "N/A"
                new_item = {"code": prod_code, "name": prod_name, "size": final_size, "quantity": prod_qty, "buy_price": prod_buy, "sell_price": prod_sell}
                
                if st.session_state.edit_mode:
                    data["stock"][st.session_state.edit_index] = new_item
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = -1
                else:
                    data["stock"].append(new_item)
                
                save_data(data)
                st.rerun()

    if st.session_state.edit_mode and st.button("Cancel Edit"):
        st.session_state.edit_mode = False
        st.rerun()

    st.markdown("---")
    st.subheader("📋 Inventory List")
    if data["stock"]:
        for idx, item in enumerate(data["stock"]):
            col0, col1, col_sz, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 0.8, 0.8, 1.2, 1.2, 0.5, 0.5])
            col0.write(f"`{item.get('code', 'N/A')}`")
            col1.write(f"**{item['name']}**")
            col_sz.write(f"{item.get('size', 'N/A')}")
            col2.write(f"Qty: {item['quantity']}")
            col3.write(f"{item['buy_price']} tk")
            col4.write(f"{item['sell_price']} tk")
            if col5.button("✏️", key=f"edit_{idx}"):
                st.session_state.edit_mode, st.session_state.edit_index = True, idx
                st.rerun()
            if col6.button("🗑️", key=f"del_{idx}"):
                data["stock"].pop(idx)
                save_data(data)
                st.rerun()

# --- PAGE 3: SALES POS ---
elif page == "🛒 Sales POS":
    st.title("🛒 Sales Point of Sale (POS)")
    if not data["stock"]:
        st.warning("Please add stock first!")
    else:
        options = [f"[{i.get('code','N/A')}] {i['name']} (Size: {i.get('size','N/A')})" for i in data["stock"] if i["quantity"] > 0]
        if not options:
            st.error("Out of Stock!")
        else:
            selected = st.selectbox("Search Product:", options)
            # Find original index
            target_idx = -1
            for idx, item in enumerate(data["stock"]):
                if f"[{item.get('code','N/A')}] {item['name']} (Size: {item.get('size','N/A')})" == selected:
                    target_idx = idx
                    break
            
            item = data["stock"][target_idx]
            qty = st.number_input("Qty:", min_value=1, max_value=item["quantity"], value=1)
            price = st.number_input("Price:", min_value=0.0, value=float(item['sell_price']))
            st.write(f"### Total: {qty * price:,.2f} tk")
            if st.button("✅ Complete Sale"):
                data["stock"][target_idx]["quantity"] -= qty
                data["sales"].append({"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "name": item["name"], "size": item.get("size","N/A"), "quantity": qty, "sell_price": price, "total_price": qty * price})
                save_data(data)
                st.success("Sold!")
                st.rerun()

# --- PAGE 4: SALES HISTORY ---
elif page == "📜 Sales History":
    st.title("📜 Sales Records")
    if data["sales"]:
        st.table(list(reversed(data["sales"])))
        if st.button("🗑️ Clear History") and st.checkbox("Confirm"):
            data["sales"] = []
            save_data(data)
            st.rerun()
    else:
        st.info("No records.")
