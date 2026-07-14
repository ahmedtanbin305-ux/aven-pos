import streamlit as st
import json
import os
from datetime import datetime

# ফাইলের নাম (যেখানে ডেটা স্থায়ীভাবে জমা থাকবে)
DATA_FILE = "trades.json"

# ডেটা লোড করার ফাংশন
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"products": {}, "sales": []}

# ডেটা সেভ করার ফাংশন
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# অ্যাপের মেইন ডেটা লোড
data = load_data()

# --- অ্যাপের টাইটেল ও লোগো ---
st.set_page_config(page_title="Aven POS Dashboard", page_icon="🛍️", layout="wide")
st.title("🛍️ Aven POS & Business Dashboard")
st.subheader("আপনার ব্র্যান্ডের ডিজিটাল হিসাব খাতা")

# ৩টি আলাদা ট্যাবে অ্যাপটি ভাগ করা হয়েছে
tab1, tab2, tab3 = st.tabs(["📊 ড্যাশবোর্ড ও সেলস", "📦 প্রোডাক্ট ম্যানেজমেন্ট", "✏️ ভুল সংশোধন (Edit Panel)"])

# ==========================================
# TAB 1: ড্যাশবোর্ড ও সেলস (Sales Entry)
# ==========================================
with tab1:
    st.header("📈 নতুন বিক্রি এবং বর্তমান অবস্থা")
    
    # বর্তমান স্টকের ওপর ভিত্তি করে টোটাল হিসাব
    total_products = len(data["products"])
    total_sales_count = len(data["sales"])
    total_revenue = sum(sale["total_price"] for sale in data["sales"])
    
    # ওপরের ক্যাশ কাউন্টার
    col1, col2, col3 = st.columns(3)
    col1.metric("মোট প্রোডাক্ট প্রকার", f"{total_products} টি")
    col2.metric("মোট বিক্রির সংখ্যা", f"{total_sales_count} টি")
    col3.metric("মোট আয় (Revenue)", f"{total_revenue:,.2f} টাকা")
    
    st.markdown("---")
    st.subheader("🛒 নতুন বিক্রির এন্ট্রি দিন")
    
    if data["products"]:
        available_products = [p for p, info in data["products"].items() if info["stock"] > 0]
        
        if available_products:
            c1, c2 = st.columns(2)
            with c1:
                selected_p = st.selectbox("প্রোডাক্ট সিলেক্ট করুন:", available_products)
            with c2:
                max_stock = data["products"][selected_p]["stock"]
                qty = st.number_input(f"পরিমাণ (স্টকে আছে: {max_stock}টি):", min_value=1, max_value=max_stock, value=1)
                
            price_per_unit = data["products"][selected_p]["price"]
            total_cost = qty * price_per_unit
            st.info(f"💰 প্রতি পিস: {price_per_unit} টাকা | মোট বিল: {total_cost} টাকা")
            
            if st.button("বিক্রি নিশ্চিত করুন (Sell)"):
                # স্টক কমানো
                data["products"][selected_p]["stock"] -= qty
                # সেলস হিস্ট্রিতে যোগ করা
                new_sale = {
                    "product": selected_p,
                    "quantity": qty,
                    "total_price": total_cost,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                data["sales"].append(new_sale)
                save_data(data)
                st.success(f"🎉 {selected_p} সফলভাবে বিক্রি হয়েছে!")
                st.rerun()
        else:
            st.warning("⚠️ দুঃখিত, সব প্রোডাক্টের স্টক শেষ! প্রোডাক্ট ম্যানেজমেন্ট ট্যাব থেকে স্টক বাড়ান।")
    else:
        st.info("💡 এখনো কোনো প্রোডাক্ট যোগ করা হয়নি। আগে প্রোডাক্ট ম্যানেজমেন্ট ট্যাবে গিয়ে প্রোডাক্ট অ্যাড করুন।")

    st.markdown("---")
    st.subheader("📜 সাম্প্রতিক বিক্রির ইতিহাস (Sales Log)")
    if data["sales"]:
        st.table(data["sales"][::-1])
    else:
        st.text("এখনো কোনো বিক্রির রেকর্ড নেই।")

# ==========================================
# TAB 2: প্রোডাক্ট ম্যানেজমেন্ট (Stock Entry)
# ==========================================
with tab2:
    st.header("📦 নতুন প্রোডাক্ট যোগ করুন")
    
    with st.form("add_product_form"):
        p_name = st.text_input("প্রোডাক্টের নাম (যেমন: Aven Premium T-Shirt):").strip()
        p_price = st.number_input("বিক্রয় মূল্য (Price per unit):", min_value=0.0, step=50.0)
        p_stock = st.number_input("স্টক পরিমাণ (Stock Quantity):", min_value=0, step=1)
        
        submit_btn = st.form_submit_button("স্টকে যোগ করুন")
        
        if submit_btn:
            if p_name:
                if p_name in data["products"]:
                    data["products"][p_name]["stock"] += p_stock
                    data["products"][p_name]["price"] = p_price 
                else:
                    data["products"][p_name] = {"price": p_price, "stock": p_stock}
                
                save_data(data)
                st.success(f"🎉 '{p_name}' সফলভাবে স্টকে আপডেট করা হয়েছে!")
                st.rerun()
            else:
                st.error("⚠️ দয়া করে প্রোডাক্টের একটি নাম দিন!")

    st.markdown("---")
    st.subheader("📋 বর্তমান ইনভেন্টরি / স্টক লিস্ট")
    if data["products"]:
        inv_data = [{"প্রোডাক্টের নাম": name, "মূল্য (টাকা)": info["price"], "চলতি স্টক": info["stock"]} for name, info in data["products"].items()]
        st.dataframe(inv_data, use_container_width=True)
    else:
        st.text("স্টক একদম খালি।")

# ==========================================
# TAB 3: ভুল সংশোধন (Edit & Delete Panel)
# ==========================================
with tab3:
    st.header("✏️ এডিট এবং ডিলিট প্যানেল (ভুল সংশোধন)")
    
    edit_choice = st.radio("কোনটি সংশোধন বা ডিলিট করতে চান?", ["প্রোডাক্ট তথ্য", "বিক্রির হিসাব"])
    
    if edit_choice == "প্রোডাক্ট তথ্য":
        if data["products"]:
            all_prods = list(data["products"].keys())
            select_edit_p = st.selectbox("কোন প্রোডাক্টের তথ্য পরিবর্তন করবেন?", all_prods)
            
            curr_p_info = data["products"][select_edit_p]
            
            edit_p_name = st.text_input("প্রোডাক্টের নাম সংশোধন:", value=select_edit_p)
            edit_p_price = st.number_input("মূল্য সংশোধন:", value=float(curr_p_info["price"]))
            edit_p_stock = st.number_input("স্টক সংশোধন:", value=int(curr_p_info["stock"]))
            
            c_update, c_delete = st.columns(2)
            with c_update:
                if st.button("🔄 তথ্য আপডেট করুন", use_container_width=True):
                    if edit_p_name != select_edit_p:
                        del data["products"][select_edit_p]
                    data["products"][edit_p_name] = {"price": edit_p_price, "stock": edit_p_stock}
                    save_data(data)
                    st.success("🎉 প্রোডাক্টের তথ্য সফলভাবে আপডেট হয়েছে!")
                    st.rerun()
            
            with c_delete:
                if st.button("🗑️ প্রোডাক্টটি পুরো ডিলিট করুন", key="del_prod", use_container_width=True):
                    del data["products"][select_edit_p]
                    save_data(data)
                    st.warning(f"❌ '{select_edit_p}' ইনভেন্টরি থেকে ডিলিট করা হয়েছে!")
                    st.rerun()
        else:
            st.info("সংশোধন করার মতো কোনো প্রোডাক্ট নেই।")
            
    elif edit_choice == "বিক্রির হিসাব":
        if data["sales"]:
            sales_list = [f"ID: {i} | {s['product']} - {s['quantity']}টি | সময়: {s['date']}" for i, s in enumerate(data["sales"])]
            select_edit_s = st.selectbox("কোন বিক্রির এন্ট্রিটি সংশোধন/ডিলিট করবেন?", sales_list)
            
            s_id = int(select_edit_s.split("|")[0].replace("ID:", "").strip())
            curr_sale_info = data["sales"][s_id]
            
            st.warning(f"📊 বর্তমান এন্ট্রি: {curr_sale_info['product']} x {curr_sale_info['quantity']} = {curr_sale_info['total_price']} টাকা")
            
            edit_s_qty = st.number_input("সঠিক পরিমাণ (Quantity):", min_value=1, value=int(curr_sale_info["quantity"]))
            
            p_current_price = data["products"].get(curr_sale_info["product"], {}).get("price", curr_sale_info["total_price"]/curr_sale_info["quantity"])
            edit_s_total = edit_s_qty * p_current_price
            
            c_s_update, c_s_delete = st.columns(2)
            with c_s_update:
                if st.button("🔄 বিক্রির হিসাব সংশোধন করুন", use_container_width=True):
                    data["sales"][s_id]["quantity"] = edit_s_qty
                    data["sales"][s_id]["total_price"] = edit_s_total
                    save_data(data)
                    st.success("🎉 বিক্রির হিসাব সংশোধন করা হয়েছে!")
                    st.rerun()
                    
            with c_s_delete:
                if st.button("🗑️ এই বিক্রির এন্ট্রি ডিলিট করুন", key="del_sale", use_container_width=True):
                    p_name_back = curr_sale_info["product"]
                    if p_name_back in data["products"]:
                        data["products"][p_name_back]["stock"] += curr_sale_info["quantity"]
                    
                    data["sales"].pop(s_id)
                    save_data(data)
                    st.warning("❌ বিক্রির এন্ট্রিটি ডিলিট করা হয়েছে এবং স্টক ফেরত দেওয়া হয়েছে!")
                    st.rerun()
                                                                                              
        else:
            st.info("সংশোধন করার মতো কোনো বিক্রির ইতিহাস নেই।")
