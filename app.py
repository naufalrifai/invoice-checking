import os
import re
from datetime import datetime
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sistem Informasi ERP Perusahaan", layout="wide")

DB_FILE = "data_faktur.csv"
UPLOAD_FOLDER = "penyimpanan_faktur"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inisialisasi memori sesi Streamlit
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "upload_success_msg" not in st.session_state:
    st.session_state.upload_success_msg = None

# Fungsi mengekstrak tanggal dari nama berkas WhatsApp (contoh: 2026-10-03 -> 03-10-2026)
def extract_date_from_filename(filename):
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', str(filename))
    if match:
        year, month, day = match.groups()
        return f"{day}-{month}-{year}"
    return "-"

# Fungsi untuk memuat data dari CSV
def load_data():
    if os.path.exists(DB_FILE):
        df_loaded = pd.read_csv(DB_FILE)
        if "Tanggal Upload" not in df_loaded.columns:
            df_loaded["Tanggal Upload"] = "-"
        
        for idx, row in df_loaded.iterrows():
            if str(row["Tanggal Upload"]).strip() in ["-", "", "nan"]:
                extracted = extract_date_from_filename(row["Nama Berkas"])
                if extracted != "-":
                    df_loaded.at[idx, "Tanggal Upload"] = extracted
        return df_loaded
    else:
        return pd.DataFrame(columns=["Nama Berkas", "Tanggal Upload"])

# Fungsi untuk menghapus 1 faktur tertentu
def delete_invoice(file_name):
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            st.error(f"Gagal menghapus berkas fisik: {e}")

    if os.path.exists(DB_FILE):
        current_df = load_data()
        updated_df = current_df[current_df["Nama Berkas"] != file_name]
        updated_df.to_csv(DB_FILE, index=False)

    st.success(f"🗑️ Faktur '{file_name}' berhasil dihapus!")
    st.rerun()

# Fungsi untuk menghapus semua faktur pada tanggal tertentu
def delete_invoices_by_date(selected_date):
    if os.path.exists(DB_FILE):
        current_df = load_data()
        to_delete = current_df[current_df["Tanggal Upload"] == selected_date]
        
        for file_name in to_delete["Nama Berkas"]:
            file_path = os.path.join(UPLOAD_FOLDER, file_name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    pass

        updated_df = current_df[current_df["Tanggal Upload"] != selected_date]
        updated_df.to_csv(DB_FILE, index=False)
        st.success(f"🗑️ Berhasil menghapus {len(to_delete)} faktur pada tanggal {selected_date}!")
        st.rerun()

df = load_data()

# --- BILAH NAVIGASI PALING ATAS (ERP HORIZONTAL MENU) ---
st.markdown("### 🏢 Sistem Informasi ERP Perusahaan")

st.markdown("""
<style>
    div[role="radiogroup"] {
        flex-direction: row;
        background-color: #f1f3f5;
        padding: 10px;
        border-radius: 6px;
        border-bottom: 3px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

dept_option = st.radio(
    "Navigasi Departemen",
    ["OLDI", "SPV", "PRINCIPAL", "WAREHOUSE", "DELIVERY", "FINANCE & ACCOUNTING", "UTILITY", "PAYROLL"],
    horizontal=True,
    index=5,
    label_visibility="collapsed"
)

st.markdown("---")

# --- SUB MENU SESUAI DEPARTEMEN ---
if dept_option == "FINANCE & ACCOUNTING":
    sub_menu = st.selectbox(
        "📂 Pilih Menu Finance & Accounting:",
        ["📸 Menu Input Foto Faktur"]
    )
    
    if sub_menu == "📸 Menu Input Foto Faktur":
        
        # 1. Header & Kartu Statistik Dashboard
        st.title("📊 Dashboard Management Faktur")

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total Faktur Tersimpan", len(df))
        with col_m2:
            total_dates = len(df["Tanggal Upload"].unique()) if not df.empty else 0
            st.metric("Total Hari Unggahan", total_dates)
        with col_m3:
            last_date = df["Tanggal Upload"].iloc[-1] if not df.empty else "-"
            st.metric("Unggahan Terakhir", last_date)

        st.markdown("---")

        # 2. Tab Navigasi Pengelolaan Faktur
        tab1, tab2, tab3 = st.tabs([
            "📸 Unggah Faktur Baru", 
            "📅 Pengelolaan Per Tanggal", 
            "🔍 Cari & Panggil Faktur"
        ])

        # TAB 1: UNGGAH FAKTUR BARU
        with tab1:
            st.subheader("📸 Menu Input Foto Faktur")
            
            if st.session_state.upload_success_msg:
                st.success(st.session_state.upload_success_msg)
                st.session_state.upload_success_msg = None

            uploaded_files = st.file_uploader(
                "Unggah berkas faktur PDF atau Foto dari WhatsApp (JPG, PNG)", 
                type=["pdf", "jpg", "jpeg", "png"], 
                accept_multiple_files=True,
                key=f"uploader_{st.session_state.uploader_key}"
            )

            if uploaded_files:
                st.markdown("---")
                st.info("✏️ **Pop-Up Konfirmasi Nama Berkas:** Ubah atau sesuaikan nama berkas di bawah ini sebelum disimpan.")

                with st.form("form_rename_files"):
                    new_filename_inputs = []
                    today_date = datetime.now().strftime("%d-%m-%Y")

                    for f_idx, file in enumerate(uploaded_files):
                        original_name = file.name
                        file_ext = os.path.splitext(original_name)[1]
                        base_name_no_ext = os.path.splitext(original_name)[0]

                        st.markdown(f"**Berkas Ke-{f_idx + 1}:** `{original_name}`")
                        edited_name_no_ext = st.text_input(
                            f"Nama Berkas Baru (tanpa ekstensi `{file_ext}`):",
                            value=base_name_no_ext,
                            key=f"rename_input_{f_idx}"
                        )
                        final_filename = edited_name_no_ext.strip() + file_ext
                        new_filename_inputs.append((file, final_filename))
                        st.write("---")

                    col_btn1, col_btn2 = st.columns([1, 4])
                    with col_btn1:
                        submit_save = st.form_submit_button("✅ Simpan Faktur", use_container_width=True)
                    with col_btn2:
                        submit_cancel = st.form_submit_button("❌ Batal Upload", use_container_width=True)

                    if submit_save:
                        new_data = []
                        has_error = False

                        for original_file, final_filename in new_filename_inputs:
                            file_path = os.path.join(UPLOAD_FOLDER, final_filename)

                            file_exists_in_csv = not df.empty and final_filename in df["Nama Berkas"].values
                            file_exists_in_folder = os.path.exists(file_path)

                            if file_exists_in_csv or file_exists_in_folder:
                                st.error(f"❌ Nama berkas '{final_filename}' sudah ada di sistem! Silakan gunakan nama lain.")
                                has_error = True
                                break

                            with open(file_path, "wb") as f:
                                f.write(original_file.getbuffer())

                            extracted_tgl = extract_date_from_filename(original_file.name)
                            file_date = extracted_tgl if extracted_tgl != "-" else today_date

                            new_data.append({
                                "Nama Berkas": final_filename,
                                "Tanggal Upload": file_date
                            })

                        if not has_error and new_data:
                            new_df = pd.DataFrame(new_data)
                            df_base = df[["Nama Berkas", "Tanggal Upload"]] if "Nama Berkas" in df.columns and "Tanggal Upload" in df.columns else df
                            df = pd.concat([df_base, new_df], ignore_index=True)
                            df.to_csv(DB_FILE, index=False)
                            st.session_state.upload_success_msg = f"✅ Berhasil menyimpan {len(new_data)} berkas faktur baru!"
                            st.session_state.uploader_key += 1
                            st.rerun()

                    if submit_cancel:
                        st.session_state.uploader_key += 1
                        st.rerun()

        # TAB 2: PENGELOLAAN PER TANGGAL
        with tab2:
            st.subheader("📅 Pengelolaan & Hapus Per Tanggal Upload")

            if not df.empty:
                available_dates = sorted(df["Tanggal Upload"].unique().tolist())
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_date_to_delete = st.selectbox(
                        "Pilih tanggal upload yang ingin dikelola:", 
                        options=available_dates,
                        key="sb_date_tab2"
                    )
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Hapus Semua di Tanggal Ini", key="btn_del_date_tab2"):
                        st.session_state[f"confirm_date_{selected_date_to_delete}"] = True

                if st.session_state.get(f"confirm_date_{selected_date_to_delete}", False):
                    st.warning(f"⚠️ **Apakah Anda yakin ingin menghapus seluruh faktur pada tanggal `{selected_date_to_delete}`?**")
                    c_yes, c_no = st.columns([1, 1])
                    with c_yes:
                        if st.button("✅ Ya, Hapus Semua", key="yes_del_date_tab2"):
                            st.session_state[f"confirm_date_{selected_date_to_delete}"] = False
                            delete_invoices_by_date(selected_date_to_delete)
                    with c_no:
                        if st.button("❌ Tidak, Batal", key="no_del_date_tab2"):
                            st.session_state[f"confirm_date_{selected_date_to_delete}"] = False
                            st.rerun()

                files_on_selected_date = df[df["Tanggal Upload"] == selected_date_to_delete]["Nama Berkas"].tolist()
                if files_on_selected_date:
                    st.markdown(f"📋 **Daftar faktur pada tanggal `{selected_date_to_delete}` ({len(files_on_selected_date)} berkas):**")
                    
                    for f_idx, f_name in enumerate(files_on_selected_date):
                        f_path = os.path.join(UPLOAD_FOLDER, f_name)
                        
                        with st.expander(f"🖼️ {f_name}"):
                            if os.path.exists(f_path):
                                f_ext = f_name.split(".")[-1].lower()
                                
                                if f_ext in ["jpg", "jpeg", "png"]:
                                    st.image(f_path, caption=f"Foto Faktur: {f_name}", use_column_width=True)
                                
                                with open(f_path, "rb") as f_data:
                                    st.download_button(
                                        label=f"📥 Unduh / Buka Berkas Asli ({f_name})",
                                        data=f_data,
                                        file_name=f_name,
                                        mime="application/pdf" if f_ext == "pdf" else f"image/{f_ext}",
                                        key=f"dl_tab2_{f_idx}"
                                    )
                            else:
                                st.warning("⚠️ Berkas fisik tidak ditemukan di folder penyimpanan.")
            else:
                st.info("Belum ada data faktur yang tersimpan.")

        # TAB 3: CARI & PANGGIL FAKTUR
        with tab3:
            st.subheader("🔍 Cari & Panggil Faktur")

            search_query = st.text_input("🔍 Masukkan kata kunci pencarian (berdasarkan nama faktur / berkas):", key="search_input_tab3")

            if search_query:
                keywords = search_query.strip().split()
                
                def match_filename_keywords(row):
                    file_name_text = str(row['Nama Berkas']).lower()
                    return all(kw.lower() in file_name_text for kw in keywords)

                filtered_df = df[df.apply(match_filename_keywords, axis=1)]
            else:
                filtered_df = df

            st.write(f"Menampilkan **{len(filtered_df)}** dari total **{len(df)}** faktur yang tersimpan.")

            if not filtered_df.empty:
                for idx, row in filtered_df.iterrows():
                    tgl = row.get("Tanggal Upload", "-")
                    file_name = row["Nama Berkas"]
                    file_path = os.path.join(UPLOAD_FOLDER, file_name)

                    with st.expander(f"📁 {file_name}  |  📅 Upload: {tgl}"):
                        st.markdown(f"**Nama Berkas / Faktur:** `{file_name}`")
                        st.markdown(f"**Tanggal Diunggah / Foto:** `{tgl}`")
                        
                        st.markdown("---")
                        st.markdown("**🖼️ Berkas / Foto Faktur Asli:**")
                        
                        if os.path.exists(file_path):
                            file_ext = file_name.split(".")[-1].lower()
                            
                            if file_ext in ["jpg", "jpeg", "png"]:
                                st.image(file_path, caption=f"Pratinjau Foto: {file_name}", use_column_width=True)
                            
                            with open(file_path, "rb") as f_data:
                                st.download_button(
                                    label=f"📥 Unduh / Buka Berkas Asli ({file_name})",
                                    data=f_data,
                                    file_name=file_name,
                                    mime="application/pdf" if file_ext == "pdf" else f"image/{file_ext}",
                                    key=f"dl_tab3_{idx}"
                                )
                        else:
                            st.warning("⚠️ Berkas fisik tidak ditemukan di folder penyimpanan.")
                        
                        st.markdown("---")
                        
                        col_del1, col_del2 = st.columns(2)
                        with col_del1:
                            if st.button(f"🗑️ Hapus Faktur Ini Saja", key=f"btn_del_single_tab3_{idx}"):
                                st.session_state[f"confirm_single_{idx}"] = True

                        with col_del2:
                            if tgl != "-":
                                if st.button(f"🗑️ Hapus Semua Faktur Tanggal {tgl}", key=f"btn_del_date_tab3_{idx}"):
                                    st.session_state[f"confirm_date_tab3_{idx}"] = True

                        # Konfirmasi Hapus Faktur Ini Saja
                        if st.session_state.get(f"confirm_single_{idx}", False):
                            st.warning(f"⚠️ **Apakah Anda yakin ingin menghapus faktur `{file_name}`?**")
                            cy, cn = st.columns([1, 1])
                            with cy:
                                if st.button("✅ Ya, Hapus", key=f"yes_single_tab3_{idx}"):
                                    st.session_state[f"confirm_single_{idx}"] = False
                                    delete_invoice(file_name)
                            with cn:
                                if st.button("❌ Tidak, Batal", key=f"no_single_tab3_{idx}"):
                                    st.session_state[f"confirm_single_{idx}"] = False
                                    st.rerun()

                        # Konfirmasi Hapus Semua Per Tanggal
                        if st.session_state.get(f"confirm_date_tab3_{idx}", False):
                            st.warning(f"⚠️ **Apakah Anda yakin ingin menghapus SELURUH faktur pada tanggal `{tgl}`?**")
                            cyd, cnd = st.columns([1, 1])
                            with cyd:
                                if st.button("✅ Ya, Hapus Semua", key=f"yes_date_tab3_{idx}"):
                                    st.session_state[f"confirm_date_tab3_{idx}"] = False
                                    delete_invoices_by_date(tgl)
                            with cnd:
                                if st.button("❌ Tidak, Batal", key=f"no_date_tab3_{idx}"):
                                    st.session_state[f"confirm_date_tab3_{idx}"] = False
                                    st.rerun()
            else:
                st.info("Belum ada faktur yang tersimpan atau cocok dengan nama pencarian.")

else:
    st.info(f"ℹ️ Modul **{dept_option}** sedang dalam tahap pengembangan.")
