import streamlit as st
import json
from datetime import datetime, timedelta
import os

# --- Configuration ---
st.set_page_config(page_title="Business POS Dashboard", page_icon="🏢", layout="wide")

DB_FILE = "business.json"

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
    st.session_state.edit_name = ""
    st.session_state.edit_qty = 0
    st.session_state.edit_b_price = 0.0
    st.session_state.edit_s_price = 0.0

# --- Sidebar ---
st.sidebar.title("🏢 Navigation")
menu = st.sidebar.radio("Go To", ["📈 Financial Report", "📦 Inventory Management", "🛒 Point of Sale (POS)"])

# --- 1. FINANCIAL REPORT (With Today, Weekly, Monthly & Lifetime Filter) ---
if menu == "📈 Financial Report":
    st.title("📊 Business Financial Report")
    
    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox("Select Report Period", ["Today's Summary", "Weekly Summary", "Monthly Summary", "Lifetime Summary"])
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    total_sales = 0
    total_cost = 0
    filtered_sales = []
    
    for sale in data["sales"]:
        # বিক্রির তারিখ থেকে শুধু দিন-মাস-বছর আলাদা করা (যেমন: '2026-06-03 13:16' থেকে '2026-06-03')
        sale_date_str = sale.get("date", "").split(" ")[0]
        try:
            sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d")
        except:
            continue
            
        # ফিল্টারিং লজিক
        if report_type == "Today's Summary" and sale_date_str != today_str:
            continue
        elif report_type == "Weekly Summary" and (now - sale_date).days > 7:
            continue
        elif report_type == "Monthly Summary" and (now - sale_date).days > 30:
            continue
            
        total_sales += sale["sell_price"] * sale["quantity"]
        total_cost += sale["buying_price"] * sale["quantity"]
        filtered_sales.append(sale)
        
    net_profit = total_sales - total_cost

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Revenue", f"{total_sales:,.2f} BDT")
    m2.metric("Total Cost", f"{total_cost:,.2f} BDT")
    
    if net_profit >= 0:
        m3.metric("Net Profit 💚", f"{net_profit:,.2f} BDT")
    else:
        m3.metric("Net Loss 💔", f"{abs(net_profit):,.2f} BDT", delta_color="inverse")

    st.subheader("📝 Sales Log")
    if filtered_sales:
        st.table(filtered_sales)
    else:
        st.info(f"No sales recorded for {report_type.lower()}.")

# --- 2. INVENTORY MANAGEMENT (With Smooth Edit & Delete) ---
elif menu == "📦 Inventory Management":
    st.title("📋 Stock & Inventory Control")
    
    with st.form("stock_form", clear_on_submit=True):
        if st.session_state.edit_mode:
            st.subheader(f"📝 Editing Product: {st.session_state.edit_name.capitalize()}")
        else:
            st.subheader("➕ Add New Product")
            
        name = st.text_input("Product Name", value=st.session_state.edit_name).strip().lower()
        quantity = st.number_input("Quantity", min_value=0, step=1, value=st.session_state.edit_qty)
        b_price = st.number_input("Buying Price (BDT)", min_value=0.0, value=st.session_state.edit_b_price)
        s_price = st.number_input("Selling Price (BDT)", min_value=0.0, value=st.session_state.edit_s_price)
        
        btn_label = "Save Changes" if st.session_state.edit_mode else "Add to Inventory"
        
        if st.form_submit_button(btn_label):
            if name:
                updated = False
                for item in data["stock"]:
                    if item["name"] == name:
                        item["quantity"] = quantity
                        item["buying_price"] = b_price
                        item["selling_price"] = s_price
                        updated = True
                        break
                if not updated:
                    data["stock"].append({"name": name, "quantity": quantity, "buying_price": b_price, "selling_price": s_price})
                
                save_data(data)
                
                # এডিট মোড রিসেট করা
                st.session_state.edit_mode = False
                st.session_state.edit_name = ""
                st.session_state.edit_qty = 0
                st.session_state.edit_b_price = 0.0
                st.session_state.edit_s_price = 0.0
                
                st.success("Inventory Updated Successfully!")
                st.rerun()

    st.subheader("📦 Current Stock List")
    if data["stock"]:
        for idx, item in enumerate(data["stock"]):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
            col1.write(f"**{item['name'].capitalize()}**")
            col2.write(f"Stock: {item['quantity']}")
            col3.write(f"Buy: {item['buying_price']} BDT")
            col4.write(f"Sell: {item['selling_price']} BDT")
            
            # Edit Button (📝)
            if col5.button("📝", key=f"edit_{idx}"):
                st.session_state.edit_mode = True
                st.session_state.edit_name = item["name"]
                st.session_state.edit_qty = item["quantity"]
                st.session_state.edit_b_price = item["buying_price"]
                st.session_state.edit_s_price = item["selling_price"]
                st.rerun()
                
            # Delete Button (❌)
            if col6.button("❌", key=f"del_{idx}"):
                data["stock"].pop(idx)
                save_data(data)
                st.rerun()
    else:
        st.info("Inventory is empty.")

# --- 3. POINT OF SALE (POS) ---
elif menu == "🛒 Point of Sale (POS)":
    st.title("🛒 Sales Counter")
    if not data["stock"]:
        st.warning("Add products first!")
    else:
        product_names = [i["name"].capitalize() for i in data["stock"] if i["quantity"] > 0]
        with st.form("sale_form"):
            choice = st.selectbox("Select Product", product_names).lower()
            item = next(i for i in data["stock"] if i["name"] == choice)
            qty = st.number_input(f"Qty (Max: {item['quantity']})", min_value=1, max_value=item["quantity"])
            price = st.number_input("Selling Price", value=item["selling_price"])
            cust = st.text_input("Customer Name") or "Guest"
            phone = st.text_input("Customer Phone") or "N/A"
            
            if st.form_submit_button("Complete Sale"):
                item["quantity"] -= qty
                curr_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                data["sales"].append({
                    "date": curr_date,
                    "name": choice, "quantity": qty, "sell_price": price, 
                    "buying_price": item["buying_price"], "customer": cust, "phone": phone
                })
                save_data(data)
                st.success("Sold!")
                
                # ক্যাশ মেমো রিসিট
                st.markdown("### 📄 CASH MEMO / RECEIPT")
                st.code(f"""
==========================================
             CASH MEMO
==========================================
Date/Time: {curr_date}
Customer : {cust}
Phone    : {phone}
------------------------------------------
Item     : {choice.capitalize()}
Quantity : {qty} pcs
Unit Price: {price:.2f} BDT
------------------------------------------
TOTAL PAID: {price * qty:.2f} BDT
==========================================
        Thank you for shopping!
==========================================
                """)
                st.balloons()