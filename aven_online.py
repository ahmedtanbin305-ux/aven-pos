import streamlit as st
import json
import os

# ফাইলের নাম (তোমার কোডের সাথে মিলিয়ে নিও)
DATA_FILE = "trades.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"products": {}, "sales": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- এডিট অপশনের মেইন কোড ---
st.markdown("---")
st.header("✏️ ভুল সংশোধন (Edit Panel)")

data = load_data()
edit_type = st.radio("কোনটি সংশোধন করতে চান?", ["প্রোডাক্ট ইনফো (Product)", "বিক্রির হিসাব (Sales History)"])

if edit_type == "প্রোডাক্ট ইনফো (Product)":
    if data["products"]:
        prod_list = list(data["products"].keys())
        selected_prod = st.selectbox("কোন প্রোডাক্টটি এডিট করবেন?", prod_list)
        
        current_details = data["products"][selected_prod]
        
        # আগের ডেটা বক্সে দেখানো হচ্ছে
        new_name = st.text_input("প্রোডাক্টের নতুন নাম:", value=selected_prod)
        new_price = st.number_input("নতুন দাম (Price):", value=float(current_details.get("price", 0)))
        new_stock = st.number_input("নতুন স্টক (Stock):", value=int(current_details.get("stock", 0)))
        
        if st.button("প্রোডাক্ট আপডেট করুন"):
            # নাম চেঞ্জ হলে আগেরটা ডিলিট করে নতুন নামে সেভ হবে
            if new_name != selected_prod:
                del data["products"][selected_prod]
            
            data["products"][new_name] = {"price": new_price, "stock": new_stock}
            save_data(data)
            st.success(f"🎉 '{new_name}' এর তথ্য সফলভাবে আপডেট হয়েছে!")
            st.rerun()
    else:
        st.info("কোনো প্রোডাক্ট পাওয়া যায়নি।")

elif edit_type == "বিক্রির হিসাব (Sales History)":
    if data.get("sales"):
        sales_indices = [f"ID: {i} | {sale['product']} - {sale['quantity']}টি ({sale['date']})" for i, sale in enumerate(data["sales"])]
        selected_sale_str = st.selectbox("কোন বিক্রির এন্ট্রিটি সংশোধন করবেন?", sales_indices)
        
        # ইনডেক্স বের করা
        sale_idx = int(selected_sale_str.split("|")[0].replace("ID:", "").strip())
        current_sale = data["sales"][sale_idx]
        
        st.write(f"**বর্তমান এন্ট্রি:** {current_sale['product']} x {current_sale['quantity']} = {current_sale['total_price']} টাকা")
        
        # সংশোধনের ইনপুট
        new_qty = st.number_input("সঠিক পরিমাণ (Quantity):", value=int(current_sale["quantity"]), min_value=1)
        # দাম অটো ক্যালকুলেট করার চেষ্টা (যদি প্রোডাক্টের দাম পাওয়া যায়)
        prod_price = data["products"].get(current_sale["product"], {}).get("price", current_sale["total_price"]/current_sale["quantity"])
        new_total = new_qty * prod_price
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("হিসাব সংশোধন করুন"):
                data["sales"][sale_idx]["quantity"] = new_qty
                data["sales"][sale_idx]["total_price"] = new_total
                save_data(data)
                st.success("🎉 বিক্রির হিসাব সংশোধন করা হয়েছে!")
                st.rerun()
        with col2:
            if st.button("🔴 এই এন্ট্রিটি পুরো ডিলিট করুন", key="delete_sale"):
                data["sales"].pop(sale_idx)
                save_data(data)
                st.warning("🗑️ বিক্রির এন্ট্রিটি ডিলিট করা হয়েছে!")
                st.rerun()
    else:
        st.info("কোনো বিক্রির ইতিহাস পাওয়া যায়নি।")
