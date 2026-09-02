import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date

# --- KONFIGURASI HALAMAN STREAMLIT ---
st.set_page_config(
    page_title="Sistem Informasi Nilai TO, TKA & UTBK",
    page_icon="📊",
    layout="wide"
)

# --- INISIALISASI & KONEKSI DATABASE SQLITE ---
def get_connection():
    return sqlite3.connect("database_to.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabel Pengguna (Admin & Pelihat)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'pelihat')) NOT NULL
        )
    ''')
    
    # Tabel Rekap Nilai TO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nilai_to (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nis TEXT NOT NULL,
            nama TEXT NOT NULL,
            kategori TEXT CHECK(kategori IN ('Internal', 'Eksternal')) NOT NULL,
            nama_to TEXT NOT NULL,
            tanggal DATE NOT NULL,
            -- TKA Subjects
            tka_b_indo REAL DEFAULT 0,
            tka_b_inggris REAL DEFAULT 0,
            tka_math REAL DEFAULT 0,
            tka_mathlan REAL DEFAULT 0,
            tka_b_inggris_lan REAL DEFAULT 0,
            -- UTBK Subtests
            utbk_pu REAL DEFAULT 0,
            utbk_pk REAL DEFAULT 0,
            utbk_ppu REAL DEFAULT 0,
            utbk_pbm REAL DEFAULT 0,
            utbk_lit_indo REAL DEFAULT 0,
            utbk_lit_ing REAL DEFAULT 0,
            utbk_pm REAL DEFAULT 0,
            total_utbk REAL DEFAULT 0
        )
    ''')
    
    # Kredensial Default
    cursor.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin')")
    cursor.execute("INSERT OR IGNORE INTO users VALUES ('pelihat', 'user123', 'pelihat')")
    conn.commit()

init_db()

# --- MANAJEMEN SESI AUTHENTICATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

def login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    if user:
        st.session_state.logged_in = True
        st.session_state.role = user[0]
        st.session_state.username = username
        st.rerun()
    else:
        st.error("❌ Username atau password salah!")

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.rerun()

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔒 Login Sistem Informasi Nilai TO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Masukkan akun Admin atau Pelihat</p>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("Masuk", use_container_width=True)
            if btn_login:
                login(user_input, pass_input)
        st.info("💡 **Akun Default:**\n- **Admin**: `admin` / `admin123` (Akses Penuh CRUD)\n- **Pelihat**: `pelihat` / `user123` (Read-Only / Terkunci)")
    st.stop()

# --- DASHBOARD & SIDEBAR (AFTER LOGIN) ---
st.sidebar.markdown(f"### 👤 Akun: **{st.session_state.username}**")
st.sidebar.markdown(f"**Hak Akses:** `{st.session_state.role.upper()}`")
if st.sidebar.button("Logout 🚪", use_container_width=True):
    logout()

st.sidebar.divider()
menu = st.sidebar.radio(
    "Navigasi Utama",
    ["📊 Dashboard & Grafik Nilai", "➕ Tambah Data (Admin)", "✏️ Edit / Hapus Data (Admin)"]
)

conn = get_connection()

# ==========================================
# 1. DASHBOARD & GRAFIK PERKEMBANGAN (READ)
# ==========================================
if menu == "📊 Dashboard & Grafik Nilai":
    st.title("📈 Dashboard Rekap & Perkembangan Nilai TO")
    
    # Fetch Data
    df = pd.read_sql_query("SELECT * FROM nilai_to ORDER BY tanggal ASC", conn)
    
    if df.empty:
        st.warning("Belum ada data nilai TO yang tersimpan.")
    else:
        # Filter Section
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            kategori_opt = ["Semua"] + list(df['kategori'].unique())
            sel_kategori = st.selectbox("Filter Kategori TO", kategori_opt)
        with f_col2:
            siswa_opt = ["Semua Siswa"] + list(df['nama'].unique())
            sel_siswa = st.selectbox("Filter Nama Siswa", siswa_opt)
        with f_col3:
            nis_opt = ["Semua NIS"] + list(df['nis'].unique())
            sel_nis = st.selectbox("Filter NIS", nis_opt)

        # Apply Filters
        filtered_df = df.copy()
        if sel_kategori != "Semua":
            filtered_df = filtered_df[filtered_df['kategori'] == sel_kategori]
        if sel_siswa != "Semua Siswa":
            filtered_df = filtered_df[filtered_df['nama'] == sel_siswa]
        if sel_nis != "Semua NIS":
            filtered_df = filtered_df[filtered_df['nis'] == sel_nis]

        st.divider()

        # TAB VIEW
        tab_tka, tab_utbk, tab_data = st.tabs(["📉 Grafik Perkembangan TKA", "📊 Grafik Perkembangan UTBK", "📋 Tabel Data Lengkap"])

        # --- TAB 1: GRAFIK TKA ---
        with tab_tka:
            st.subheader("Grafik Garis Perkembangan Nilai TKA")
            tka_cols = ['tka_b_indo', 'tka_b_inggris', 'tka_math', 'tka_mathlan', 'tka_b_inggris_lan']
            tka_labels = {
                'tka_b_indo': 'B. Indonesia',
                'tka_b_inggris': 'B. Inggris',
                'tka_math': 'Matematika',
                'tka_mathlan': 'Math Lanjut',
                'tka_b_inggris_lan': 'B. Inggris Lanjut'
            }

            if sel_siswa == "Semua Siswa" and len(filtered_df['nama'].unique()) > 1:
                st.info("💡 **Tips:** Pilih nama siswa spesifik di menu filter atas untuk melihat riwayat tren individual.")
            
            # Format Data for Line Chart
            df_tka_melted = filtered_df.melt(
                id_vars=['tanggal', 'nama_to', 'nama', 'nis'],
                value_vars=tka_cols,
                var_name='Mata Pelajaran',
                value_name='Nilai'
            )
            df_tka_melted['Mata Pelajaran'] = df_tka_melted['Mata Pelajaran'].map(tka_labels)
            
            fig_tka = px.line(
                df_tka_melted,
                x='nama_to',
                y='Nilai',
                color='Mata Pelajaran',
                markers=True,
                hover_data=['tanggal', 'nama'],
                title=f"Tren Nilai TKA - {sel_siswa if sel_siswa != 'Semua Siswa' else 'Seluruh Siswa'}"
            )
            fig_tka.update_layout(xaxis_title="Pelaksanaan TO", yaxis_title="Skor TKA", hovermode="x unified")
            st.plotly_chart(fig_tka, use_container_width=True)

        # --- TAB 2: GRAFIK UTBK ---
        with tab_utbk:
            st.subheader("Grafik Garis Perkembangan Nilai UTBK")
            utbk_sub_cols = ['utbk_pu', 'utbk_pk', 'utbk_ppu', 'utbk_pbm', 'utbk_lit_indo', 'utbk_lit_ing', 'utbk_pm']
            utbk_labels = {
                'utbk_pu': 'Penalaran Umum (PU)',
                'utbk_pk': 'Penget. Kuantitatif (PK)',
                'utbk_ppu': 'PPU',
                'utbk_pbm': 'PBM',
                'utbk_lit_indo': 'Literasi B. Indo',
                'utbk_lit_ing': 'Literasi B. Ing',
                'utbk_pm': 'Penalaran Math (PM)',
                'total_utbk': 'TOTAL UTBK'
            }

            # Chart 1: Total Score Progress
            fig_total = px.line(
                filtered_df,
                x='nama_to',
                y='total_utbk',
                color='nama' if sel_siswa == "Semua Siswa" else None,
                markers=True,
                title="📈 Tren Rata-Rata / Total Skor UTBK"
            )
            fig_total.update_layout(xaxis_title="Pelaksanaan TO", yaxis_title="Total Skor UTBK")
            st.plotly_chart(fig_total, use_container_width=True)

            # Chart 2: Subtest Progress Breakdown
            st.markdown("##### Breakdown Per Sub-tes UTBK")
            df_utbk_melted = filtered_df.melt(
                id_vars=['tanggal', 'nama_to', 'nama', 'nis'],
                value_vars=utbk_sub_cols,
                var_name='Subtest UTBK',
                value_name='Skor'
            )
            df_utbk_melted['Subtest UTBK'] = df_utbk_melted['Subtest UTBK'].map(utbk_labels)

            fig_utbk_sub = px.line(
                df_utbk_melted,
                x='nama_to',
                y='Skor',
                color='Subtest UTBK',
                markers=True,
                title="Rincian Sub-tes UTBK"
            )
            fig_utbk_sub.update_layout(xaxis_title="Pelaksanaan TO", yaxis_title="Skor Sub-tes", hovermode="x unified")
            st.plotly_chart(fig_utbk_sub, use_container_width=True)

        # --- TAB 3: TABEL DATA LENGKAP ---
        with tab_data:
            st.subheader("Data Mentah Rekapitulasi TO")
            st.dataframe(filtered_df, use_container_width=True)
            
            # Export CSV Button
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Rekap Data (CSV)",
                data=csv,
                file_name=f"rekap_nilai_to_{date.today()}.csv",
                mime='text/csv'
            )

# ==========================================
# 2. TAMBAH DATA (CREATE - ADMIN ONLY)
# ==========================================
elif menu == "➕ Tambah Data (Admin)":
    st.title("➕ Input Nilai Try Out Baru")
    
    if st.session_state.role != "admin":
        st.error("🔒 **Akses Ditolak:** Halaman ini hanya untuk pengguna dengan role Admin. Akun Pelihat hanya dapat membaca data.")
    else:
        with st.form("form_tambah_nilai"):
            st.subheader("📌 Informasi Siswa & TO")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                nis = st.text_input("NIS Siswa", placeholder="Contoh: 2024001")
            with c2:
                nama = st.text_input("Nama Siswa", placeholder="Contoh: Budi Santoso")
            with c3:
                kategori = st.selectbox("Kategori TO", ["Internal", "Eksternal"])
            with c4:
                nama_to = st.text_input("Nama/Seri TO", placeholder="Contoh: TO-1 Ganesha")
            
            tanggal = st.date_input("Tanggal Pelaksanaan", value=date.today())

            st.divider()
            st.subheader("📚 Nilai TKA (Tes Kemampuan Akademik)")
            tk1, tk2, tk3, tk4, tk5 = st.columns(5)
            with tk1:
                tka_b_indo = st.number_input("B. Indonesia", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
            with tk2:
                tka_b_inggris = st.number_input("B. Inggris", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
            with tk3:
                tka_math = st.number_input("Matematika", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
            with tk4:
                tka_mathlan = st.number_input("Math Lanjut", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
            with tk5:
                tka_b_inggris_lan = st.number_input("B. Inggris Lanjut", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)

            st.divider()
            st.subheader("🎯 Nilai Sub-tes UTBK")
            ut1, ut2, ut3, ut4 = st.columns(4)
            with ut1:
                utbk_pu = st.number_input("Penalaran Umum (PU)", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
                utbk_lit_indo = st.number_input("Literasi B. Indonesia", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
            with ut2:
                utbk_pk = st.number_input("Pengetahuan Kuantitatif (PK)", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
                utbk_lit_ing = st.number_input("Literasi B. Inggris", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
            with ut3:
                utbk_ppu = st.number_input("PPU", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
                utbk_pm = st.number_input("Penalaran Matematika (PM)", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
            with ut4:
                utbk_pbm = st.number_input("PBM", min_value=0.0, max_value=1000.0, value=0.0, step=5.0)
                # Auto Calculate Average UTBK
                calc_total = (utbk_pu + utbk_pk + utbk_ppu + utbk_pbm + utbk_lit_indo + utbk_lit_ing + utbk_pm) / 7.0
                st.markdown(f"**Auto Rata-Rata UTBK:** `{calc_total:.2f}`")

            total_utbk = st.number_input("Total / Rata-rata Skor UTBK (Bisa Diubah Manual)", min_value=0.0, max_value=1000.0, value=round(calc_total, 2))

            submitted = st.form_submit_button("Simpan Data Nilai", use_container_width=True)
            if submitted:
                if not nis or not nama or not nama_to:
                    st.error("Mohon lengkapi NIS, Nama Siswa, dan Nama TO!")
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO nilai_to (
                            nis, nama, kategori, nama_to, tanggal,
                            tka_b_indo, tka_b_inggris, tka_math, tka_mathlan, tka_b_inggris_lan,
                            utbk_pu, utbk_pk, utbk_ppu, utbk_pbm, utbk_lit_indo, utbk_lit_ing, utbk_pm, total_utbk
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        nis, nama, kategori, nama_to, str(tanggal),
                        tka_b_indo, tka_b_inggris, tka_math, tka_mathlan, tka_b_inggris_lan,
                        utbk_pu, utbk_pk, utbk_ppu, utbk_pbm, utbk_lit_indo, utbk_lit_ing, utbk_pm, total_utbk
                    ))
                    conn.commit()
                    st.success(f"✅ Data nilai TO '{nama_to}' untuk {nama} berhasil disimpan!")

# ==========================================
# 3. EDIT & HAPUS DATA (UPDATE/DELETE - ADMIN ONLY)
# ==========================================
elif menu == "✏️ Edit / Hapus Data (Admin)":
    st.title("✏️ Kelola & Hapus Record Data Nilai")
    
    if st.session_state.role != "admin":
        st.error("🔒 **Akses Ditolak:** Halaman ini hanya untuk pengguna dengan role Admin. Akun Pelihat hanya dapat membaca data.")
    else:
        df_edit = pd.read_sql_query("SELECT * FROM nilai_to", conn)
        
        if df_edit.empty:
            st.info("Belum ada data untuk dikelola.")
        else:
            st.dataframe(df_edit, use_container_width=True)
            
            st.divider()
            col_act1, col_act2 = st.columns(2)
            
            # --- HAPUS DATA ---
            with col_act1:
                st.subheader("🗑️ Hapus Data")
                id_hapus = st.number_input("Masukkan ID Data yang akan dihapus", min_value=1, step=1)
                if st.button("Hapus Record Data", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM nilai_to WHERE id=?", (id_hapus,))
                    if cursor.fetchone():
                        cursor.execute("DELETE FROM nilai_to WHERE id=?", (id_hapus,))
                        conn.commit()
                        st.success(f"Data dengan ID {id_hapus} berhasil dihapus!")
                        st.rerun()
                    else:
                        st.error(f"Data ID {id_hapus} tidak ditemukan.")

            # --- EDIT DATA ---
            with col_act2:
                st.subheader("✏️ Edit Data")
                id_edit = st.number_input("Masukkan ID Data yang akan diedit", min_value=1, step=1)
                
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM nilai_to WHERE id=?", (id_edit,))
                row = cursor.fetchone()
                
                if row:
                    st.success(f"Editing ID: {id_edit} - Nama: {row[2]}")
                    with st.form("form_update"):
                        u_nis = st.text_input("NIS", value=row[1])
                        u_nama = st.text_input("Nama", value=row[2])
                        u_kategori = st.selectbox("Kategori", ["Internal", "Eksternal"], index=0 if row[3] == "Internal" else 1)
                        u_nama_to = st.text_input("Nama TO", value=row[4])
                        u_tka_b_indo = st.number_input("TKA B. Indo", value=float(row[6]))
                        u_tka_mathlan = st.number_input("TKA Mathlan", value=float(row[9]))
                        u_total_utbk = st.number_input("Total UTBK", value=float(row[17]))
                        
                        btn_update = st.form_submit_button("Update Data")
                        if btn_update:
                            cursor.execute('''
                                UPDATE nilai_to SET nis=?, nama=?, kategori=?, nama_to=?, tka_b_indo=?, tka_mathlan=?, total_utbk=?
                                WHERE id=?
                            ''', (u_nis, u_nama, u_kategori, u_nama_to, u_tka_b_indo, u_tka_mathlan, u_total_utbk, id_edit))
                            conn.commit()
                            st.success(f"Data ID {id_edit} berhasil di-update!")
                            st.rerun()
