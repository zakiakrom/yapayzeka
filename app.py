import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="E-Commerce Analytics", layout="wide")

# Styling CSS agar mirip dashboard profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_index=True)

# 2. Fungsi Load Data & Model
@st.cache_resource
def load_assets():
    # Nama file harus sesuai dengan yang ada di foldermu
    csv_file = 'ecommerce_clean.csv'
    model_file = 'model_trending.pkl'
    le_file = 'label_encoder.pkl'
    
    if not os.path.exists(csv_file):
        st.error(f"File '{csv_file}' tidak ditemukan! Pastikan sudah dipindah ke folder utama.")
        return None, None, None

    df = pd.read_csv(csv_file)
    # Menyeragamkan nama kolom (menghapus spasi dan jadi huruf kecil)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
    
    model = joblib.load(model_file)
    le = joblib.load(le_file)
    return df, model, le

# Load data
df, model, le = load_assets()

if df is not None:
    # 3. SIDEBAR - INPUT DATA
    st.sidebar.header("🔍 Input Product Details")
    with st.sidebar.form("prediction_form"):
        # Dropdown mengambil data unik dari kolom category asli
        cat_input = st.selectbox("Category", df['category'].unique())
        sub_cat_input = st.selectbox("Sub-Category", df['sub_category'].unique())
        
        u_price = st.number_input("Unit Price ($)", min_value=0.0, value=100.0)
        qty = st.number_input("Quantity", min_value=1, value=1)
        disc = st.slider("Discount", 0.0, 1.0, 0.1)
        
        # Kalkulasi otomatis untuk Sales & Profit
        calc_sales = u_price * qty * (1 - disc)
        calc_profit = calc_sales * 0.1  # Asumsi margin profit 10%
        
        predict_btn = st.form_submit_button("Predict Trend")

    # 4. MAIN PANEL - METRICS
    st.title("🛍️ E-Commerce Sales & Trend Metrics")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", f"{len(df):,}")
    
    # Cek jika kolom is_trending ada
    if 'is_trending' in df.columns:
        col2.metric("Trending Items", f"{df['is_trending'].sum():,}")
    else:
        col2.metric("Trending Items", "N/A")
        
    col3.metric("Avg Profit", f"${df['profit'].mean():.2f}")

    # 5. LOGIKA PREDIKSI
    if predict_btn:
        try:
            # Transformasi kategori ke angka
            cat_n = le.transform([cat_input])[0]
            
            # Buat DataFrame untuk input model (Sesuaikan urutan kolom X saat training)
            # Urutan: category_n, sub_cat_n, quantity, unit_price, discount, sales, profit
            X_input = pd.DataFrame([[cat_n, 0, qty, u_price, disc, calc_sales, calc_profit]], 
                                   columns=['category_n', 'sub_cat_n', 'quantity', 'unit_price', 'discount', 'sales', 'profit'])
            
            res = model.predict(X_input)
            
            st.subheader("🎯 Prediction Result")
            if res[0] == 1:
                st.success(f"🔥 **TRENDING!** Produk di kategori {cat_input} ini diprediksi akan populer.")
            else:
                st.info(f"📊 **NORMAL.** Produk ini diprediksi memiliki performa penjualan biasa.")
                
        except Exception as e:
            st.error(f"Gagal melakukan prediksi: {e}")

    # 6. VISUALISASI
    st.markdown("---")
    st.subheader("📈 Sales vs Profit Analysis")
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.scatterplot(data=df, x='sales', y='profit', hue='category', alpha=0.7, ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)