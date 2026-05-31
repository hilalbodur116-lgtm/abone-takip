"""
╔══════════════════════════════════════════════════════════╗
║        ABONE TAKİP SİSTEMİ  —  Subscription Tracker     ║
║        Streamlit + SQLite  |  Türkçe Arayüz              ║
╚══════════════════════════════════════════════════════════╝
Kurulum:
    pip install streamlit matplotlib seaborn pandas
    
Çalıştırma:
    streamlit run app.py
"""

import sqlite3
import datetime
import io
import math

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ──────────────────────────────────────────────
#  SAYFA YAPISI & TEMA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Abone Takip Sistemi",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
#  ÖZEL CSS  (modern, koyu tema)
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* ---- Google Fonts ---- */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ---- Genel ---- */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0f1a;
    color: #e8e9f0;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #111326 0%, #0d0f1a 100%);
    border-right: 1px solid #1e2140;
}
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Syne', sans-serif;
    color: #a78bfa;
}

/* ---- Metric Kartları ---- */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a1d35 0%, #161830 100%);
    border: 1px solid #2a2d50;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
div[data-testid="metric-container"] label {
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #7c7fa8 !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif;
    font-size: 1.9rem !important;
    font-weight: 800;
    color: #a78bfa !important;
}

/* ---- Başlıklar ---- */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
}

/* ---- Uyarı kutuları ---- */
.alert-box {
    background: linear-gradient(135deg, #2d1a1a 0%, #1e1010 100%);
    border: 1px solid #ef4444;
    border-left: 4px solid #ef4444;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    animation: pulse-border 2s ease-in-out infinite;
}
@keyframes pulse-border {
    0%,100% { border-left-color: #ef4444; }
    50%      { border-left-color: #f97316; }
}
.alert-box strong { color: #fca5a5; font-family: 'Syne', sans-serif; }
.alert-box span   { color: #e5e7eb; font-size: 0.88rem; }

/* ---- Tablo ---- */
.stDataFrame, iframe { border-radius: 12px !important; }

/* ---- Butonlar ---- */
div.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    color: white;
    border: none;
    border-radius: 10px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 0.5rem 1.4rem;
    transition: all 0.2s ease;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(124,58,237,0.45);
}

/* ---- Separator ---- */
hr { border-color: #1e2140; margin: 1.5rem 0; }

/* ---- Input alanları ---- */
input, textarea, select {
    background-color: #1a1d35 !important;
    color: #e8e9f0 !important;
    border: 1px solid #2a2d50 !important;
    border-radius: 8px !important;
}

/* ---- Başlık bölgesi ---- */
.page-header {
    background: linear-gradient(135deg, #1a1d35 0%, #111326 100%);
    border: 1px solid #2a2d50;
    border-radius: 18px;
    padding: 28px 36px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.page-header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: #c4b5fd;
    margin: 0;
}
.page-header p {
    color: #7c7fa8;
    margin: 4px 0 0 0;
    font-size: 0.9rem;
}

/* ---- Kategori badge ---- */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'Syne', sans-serif;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  SABİT DÖVİZ KURLARI (TRY bazlı)
# ──────────────────────────────────────────────
DOVIZ_KURLARI: dict[str, float] = {
    "TRY": 1.0,
    "USD": 32.5,
    "EUR": 35.0,
    "GBP": 41.0,
    "JPY": 0.22,
}

KATEGORILER = [
    "🎬 Eğlence",
    "📚 Eğitim",
    "❤️ Sağlık",
    "💻 Yazılım",
    "🎵 Müzik",
    "🎮 Oyun",
    "📰 Haber",
    "☁️ Depolama",
    "🛒 Alışveriş",
    "🔧 Diğer",
]

# ──────────────────────────────────────────────
#  VERİTABANI  (SQLite)
# ──────────────────────────────────────────────
DB_PATH = "abonelikler.db"


def db_baglanti() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def tablo_olustur():
    conn = db_baglanti()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS abonelikler (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ad              TEXT    NOT NULL,
            ucret           REAL    NOT NULL,
            para_birimi     TEXT    NOT NULL DEFAULT 'TRY',
            kategori        TEXT    NOT NULL,
            sonraki_odeme   TEXT    NOT NULL,
            notlar          TEXT,
            olusturma_tarihi TEXT   DEFAULT (date('now'))
        )
    """)
    conn.commit()
    conn.close()


def abonelik_ekle(ad, ucret, para_birimi, kategori, sonraki_odeme, notlar=""):
    conn = db_baglanti()
    conn.execute(
        """INSERT INTO abonelikler (ad, ucret, para_birimi, kategori, sonraki_odeme, notlar)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (ad, ucret, para_birimi, kategori, str(sonraki_odeme), notlar),
    )
    conn.commit()
    conn.close()


def abonelik_sil(abonelik_id: int):
    conn = db_baglanti()
    conn.execute("DELETE FROM abonelikler WHERE id = ?", (abonelik_id,))
    conn.commit()
    conn.close()


def abonelik_guncelle(abonelik_id, ad, ucret, para_birimi, kategori, sonraki_odeme, notlar):
    conn = db_baglanti()
    conn.execute(
        """UPDATE abonelikler SET ad=?, ucret=?, para_birimi=?, kategori=?,
           sonraki_odeme=?, notlar=? WHERE id=?""",
        (ad, ucret, para_birimi, kategori, str(sonraki_odeme), notlar, abonelik_id),
    )
    conn.commit()
    conn.close()


def tum_abonelikler() -> pd.DataFrame:
    conn = db_baglanti()
    df = pd.read_sql_query(
        "SELECT * FROM abonelikler ORDER BY sonraki_odeme ASC", conn
    )
    conn.close()
    return df


# ──────────────────────────────────────────────
#  YARDIMCI FONKSİYONLAR
# ──────────────────────────────────────────────

def try_cevir(ucret: float, para_birimi: str) -> float:
    return ucret * DOVIZ_KURLARI.get(para_birimi, 1.0)


def gunler_kaldi(tarih_str: str) -> int:
    try:
        tarih = datetime.date.fromisoformat(str(tarih_str))
        delta = tarih - datetime.date.today()
        return delta.days
    except Exception:
        return 999


def email_gonder_simule(abonelik_adi: str) -> str:
    """SMTP simülasyonu – gerçek e-posta göndermez."""
    return (
        f"✅ **'{abonelik_adi}'** aboneliği için hatırlatma e-postası "
        f"**kullanici@ornek.com** adresine başarıyla gönderildi!\n\n"
        f"📧 *Gönderim zamanı: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*"
    )


# ──────────────────────────────────────────────
#  DEMO VERİSİ (ilk çalıştırmada)
# ──────────────────────────────────────────────

def demo_veri_yukle():
    conn = db_baglanti()
    count = conn.execute("SELECT COUNT(*) FROM abonelikler").fetchone()[0]
    conn.close()
    if count == 0:
        bugun = datetime.date.today()
        demo = [
            ("Netflix",      "6.99",  "USD", "🎬 Eğlence",  bugun + datetime.timedelta(days=2),  "Aile planı"),
            ("Spotify",      "4.99",  "USD", "🎵 Müzik",    bugun + datetime.timedelta(days=15), "Bireysel"),
            ("GitHub Pro",   "4.00",  "USD", "💻 Yazılım",  bugun + datetime.timedelta(days=22), ""),
            ("ChatGPT Plus", "20.00", "USD", "💻 Yazılım",  bugun + datetime.timedelta(days=7),  ""),
            ("Udemy",        "299",   "TRY", "📚 Eğitim",   bugun + datetime.timedelta(days=30), "Yıllık plan"),
            ("iCloud 50GB",  "3.99",  "TRY", "☁️ Depolama", bugun + datetime.timedelta(days=3),  ""),
            ("Xbox Game Pass","1.00", "USD", "🎮 Oyun",     bugun + datetime.timedelta(days=45), "Ultimate"),
            ("Blutv",        "199",   "TRY", "🎬 Eğlence",  bugun + datetime.timedelta(days=18), ""),
        ]
        for row in demo:
            abonelik_ekle(*row)


# ──────────────────────────────────────────────
#  GRAFİKLER
# ──────────────────────────────────────────────

GRAFIK_BG   = "#0d0f1a"
GRAFIK_TEXT = "#c4b5fd"
PALET = [
    "#7c3aed","#a78bfa","#c4b5fd","#6d28d9",
    "#8b5cf6","#ddd6fe","#5b21b6","#ede9fe",
]


def pasta_grafigi(df: pd.DataFrame, value_col: str = "try_ucret") -> plt.Figure:
    kat_df = df.copy()
    if value_col not in kat_df.columns:
        kat_df["try_ucret"] = kat_df.apply(
            lambda r: try_cevir(float(r["ucret"]), r["para_birimi"]), axis=1
        )
        plot_col = "try_ucret"
    else:
        plot_col = value_col
    grup = kat_df.groupby("kategori")[plot_col].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(6, 5), facecolor=GRAFIK_BG)
    ax.set_facecolor(GRAFIK_BG)

    wedges, texts, autotexts = ax.pie(
        grup.values,
        labels=None,
        autopct="%1.1f%%",
        colors=PALET[: len(grup)],
        startangle=140,
        wedgeprops=dict(width=0.55, edgecolor=GRAFIK_BG, linewidth=2),
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(9)
        at.set_fontweight("bold")

    legend_labels = [f"{k}  ({v:,.0f} ₺)" for k, v in zip(grup.index, grup.values)]
    ax.legend(
        wedges, legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.22),
        ncol=2,
        fontsize=8,
        frameon=False,
        labelcolor=GRAFIK_TEXT,
    )
    ax.set_title("Kategoriye Göre Harcama Dağılımı", color=GRAFIK_TEXT,
                 fontsize=13, fontweight="bold", pad=16)
    fig.tight_layout()
    return fig


def sutun_grafigi(df: pd.DataFrame, value_col: str = "try_ucret") -> plt.Figure:
    bar_df = df.copy()
    if value_col not in bar_df.columns:
        bar_df["try_ucret"] = bar_df.apply(
            lambda r: try_cevir(float(r["ucret"]), r["para_birimi"]), axis=1
        )
        plot_col = "try_ucret"
    else:
        plot_col = value_col
    bar_df = bar_df.sort_values(plot_col, ascending=True)

    fig, ax = plt.subplots(figsize=(7, max(4, len(bar_df) * 0.55)), facecolor=GRAFIK_BG)
    ax.set_facecolor(GRAFIK_BG)

    colors = [PALET[i % len(PALET)] for i in range(len(bar_df))]
    bars = ax.barh(bar_df["ad"], bar_df["try_ucret"], color=colors,
                   height=0.6, edgecolor="none")

    for bar, val in zip(bars, bar_df["try_ucret"]):
        ax.text(val + max(bar_df["try_ucret"]) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,.1f} ₺", va="center", ha="left",
                color=GRAFIK_TEXT, fontsize=8.5, fontweight="bold")

    ax.set_xlabel("Aylık Maliyet (TRY)", color="#7c7fa8", fontsize=9)
    ax.set_title("Platform Bazlı Maliyet Karşılaştırması", color=GRAFIK_TEXT,
                 fontsize=13, fontweight="bold", pad=14)
    ax.tick_params(colors="#9ca3b0", labelsize=9)
    ax.spines[:].set_color("#1e2140")
    ax.xaxis.label.set_color("#7c7fa8")
    ax.yaxis.label.set_color("#7c7fa8")
    ax.grid(axis="x", color="#1e2140", linewidth=0.8, linestyle="--")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────
#  UYGULAMA GİRİŞ NOKTASI
# ──────────────────────────────────────────────

tablo_olustur()
demo_veri_yukle()

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 💳 Abone Takip")
    st.markdown("---")
    menu = st.radio(
        "Menü",
        ["🏠 Dashboard", "➕ Abonelik Ekle", "📋 Aboneliklerim",
         "✏️ Güncelle", "📊 Raporlar"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### 💱 Döviz Kurları (TRY)")
    for para, kur in DOVIZ_KURLARI.items():
        if para != "TRY":
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:4px 0;color:#9ca3b0;font-size:0.85rem'>"
                f"<span>1 {para}</span><span style='color:#a78bfa;font-weight:700'>= {kur:.2f} ₺</span></div>",
                unsafe_allow_html=True,
            )
    st.markdown("---")
    st.caption(f"🕒 {datetime.date.today().strftime('%d %B %Y')}")


# ════════════════════════════════════════════════
#  SAYFA 1: DASHBOARD
# ════════════════════════════════════════════════
if menu == "🏠 Dashboard":

    st.markdown("""
    <div class="page-header">
        <div>
            <h1>📊 Genel Bakış</h1>
            <p>Tüm aboneliklerinizin anlık özeti</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = tum_abonelikler()

    if df.empty:
        st.info("Henüz abonelik eklenmedi. Sol menüden 'Abonelik Ekle' seçeneğini kullanın.")
        st.stop()

    with st.expander("🔎 Abonelikleri filtrele", expanded=True):
        filtre_kategoriler = st.multiselect(
            "Kategori",
            options=df["kategori"].unique().tolist(),
            default=df["kategori"].unique().tolist(),
            help="Dashboard verilerini kategori bazında filtreleyin.",
        )
        arama = st.text_input("🔍 Abonelik ara", placeholder="İsim ile ara...")

        col_t1, col_t2 = st.columns(2)
        baslangic_tarihi = col_t1.date_input(
            "Başlangıç tarihi",
            value=datetime.date.today() - datetime.timedelta(days=30),
            min_value=datetime.date.today() - datetime.timedelta(days=365),
            max_value=datetime.date.today() + datetime.timedelta(days=365),
        )
        bitis_tarihi = col_t2.date_input(
            "Bitiş tarihi",
            value=datetime.date.today() + datetime.timedelta(days=90),
            min_value=baslangic_tarihi,
            max_value=datetime.date.today() + datetime.timedelta(days=730),
        )

        ozet_tipi = st.radio(
            "Maliyet Görünümü",
            ["Aylık", "Yıllık"],
            horizontal=True,
            help="Dashboard raporunu aylık veya yıllık bazda gör."
        )

    if filtre_kategoriler:
        df = df[df["kategori"].isin(filtre_kategoriler)]
    if arama:
        df = df[df["ad"].str.contains(arama, case=False, na=False)]

    df["tarih"] = df["sonraki_odeme"].apply(lambda x: datetime.date.fromisoformat(str(x)))
    df = df[(df["tarih"] >= baslangic_tarihi) & (df["tarih"] <= bitis_tarihi)]

    if df.empty:
        st.warning("Seçilen filtrelere uygun abonelik bulunamadı. Lütfen filtreleri genişletin.")
        st.stop()

    df["try_ucret"] = df.apply(lambda r: try_cevir(float(r["ucret"]), r["para_birimi"]), axis=1)
    df["gun_kaldi"] = df["sonraki_odeme"].apply(gunler_kaldi)

    toplam_aylik  = df["try_ucret"].sum()
    toplam_yillik = toplam_aylik * 12
    aktif_sayi    = len(df)
    en_pahali_idx = df["try_ucret"].idxmax()
    en_pahali_ad  = df.loc[en_pahali_idx, "ad"]
    en_pahali_ucr = df.loc[en_pahali_idx, "try_ucret"]
    yaklaşan_sayı = (df["gun_kaldi"] <= 3).sum()

    if ozet_tipi == "Yıllık":
        ana_etiket = "💰 Toplam Yıllık Gider"
        ana_deger = toplam_yillik
    else:
        ana_etiket = "💰 Toplam Aylık Gider"
        ana_deger = toplam_aylik

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(ana_etiket, f"{ana_deger:,.2f} ₺")
    col2.metric("📌 Aktif Abonelik", f"{aktif_sayi} adet")
    col3.metric("🔥 En Yüksek Maliyet", f"{en_pahali_ad}", f"{en_pahali_ucr:,.2f} ₺")
    col4.metric("⚠️ Yaklaşan Ödeme", f"{yaklaşan_sayı} adet", delta_color="inverse")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Yaklaşan uyarılar ──
    yaklasan = df[df["gun_kaldi"] <= 3].sort_values("gun_kaldi")
    if not yaklasan.empty:
        st.markdown("### 🚨 Yaklaşan Ödemeler")
        for _, row in yaklasan.iterrows():
            gun = int(row["gun_kaldi"])
            gun_label = (
                "⏰ **BUGÜN**" if gun == 0
                else f"⏳ **{gun} gün sonra**" if gun > 0
                else "❌ **Gecikmiş!**"
            )
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.markdown(
                    f"""<div class="alert-box">
                        <strong>{row['ad']}</strong> &nbsp;|&nbsp;
                        <span>{row['ucret']} {row['para_birimi']} &nbsp;·&nbsp;
                        {gun_label} &nbsp;·&nbsp; {row['sonraki_odeme']}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col_b:
                if st.button("📧 Hatırlat", key=f"hatirla_{row['id']}"):
                    st.success(email_gonder_simule(row["ad"]))

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Mini tablo ──
    st.markdown("### 📋 Tüm Abonelikler")
    goster = df[["id", "ad", "ucret", "para_birimi", "try_ucret", "kategori", "sonraki_odeme", "gun_kaldi"]].copy()
    goster.columns = ["ID", "Ad", "Ücret", "Para Birimi", "TRY Karşılık", "Kategori", "Sonraki Ödeme", "Kalan Gün"]
    goster["TRY Karşılık"] = goster["TRY Karşılık"].map("{:,.2f} ₺".format)
    st.dataframe(goster, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════
#  SAYFA 2: ABONELİK EKLE
# ════════════════════════════════════════════════
elif menu == "➕ Abonelik Ekle":

    st.markdown("""
    <div class="page-header">
        <div><h1>➕ Yeni Abonelik</h1><p>Takip listene yeni bir abonelik ekle</p></div>
    </div>""", unsafe_allow_html=True)

    with st.form("ekle_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        ad            = col1.text_input("Abonelik Adı *", placeholder="Örn: Netflix")
        kategori      = col2.selectbox("Kategori *", KATEGORILER)

        col3, col4, col5 = st.columns([2, 1, 1])
        ucret         = col3.number_input("Ücret *", min_value=0.01, value=9.99, step=0.01, format="%.2f")
        para_birimi   = col4.selectbox("Para Birimi", list(DOVIZ_KURLARI.keys()))
        sonraki_odeme = col5.date_input(
            "Sonraki Ödeme *",
            value=datetime.date.today() + datetime.timedelta(days=30),
            min_value=datetime.date.today() - datetime.timedelta(days=365),
        )

        notlar = st.text_area("Notlar (isteğe bağlı)", placeholder="Ek bilgi, plan türü...")

        submitted = st.form_submit_button("💾 Kaydet", use_container_width=True)

    if submitted:
        if not ad.strip():
            st.error("❗ Abonelik adı boş olamaz.")
        else:
            abonelik_ekle(ad.strip(), ucret, para_birimi, kategori, sonraki_odeme, notlar)
            try_eq = try_cevir(ucret, para_birimi)
            st.success(
                f"✅ **{ad}** başarıyla eklendi!  "
                f"TRY karşılığı: **{try_eq:,.2f} ₺/ay**"
            )
            st.balloons()


# ════════════════════════════════════════════════
#  SAYFA 3: ABONELİKLERİM (Listeleme + Silme)
# ════════════════════════════════════════════════
elif menu == "📋 Aboneliklerim":

    st.markdown("""
    <div class="page-header">
        <div><h1>📋 Aboneliklerim</h1><p>Kayıtlı aboneliklerini yönet</p></div>
    </div>""", unsafe_allow_html=True)

    df = tum_abonelikler()

    if df.empty:
        st.info("Kayıtlı abonelik bulunamadı.")
        st.stop()

    df["try_ucret"] = df.apply(lambda r: try_cevir(float(r["ucret"]), r["para_birimi"]), axis=1)
    df["gun_kaldi"] = df["sonraki_odeme"].apply(gunler_kaldi)

    # Filtreler
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    secili_kat = col_f1.multiselect(
        "Kategoriye göre filtrele",
        options=df["kategori"].unique().tolist(),
        default=[],
    )
    arama = col_f2.text_input("🔍 Abonelik ara", placeholder="İsim ile ara...")
    tarih_filtre = col_f3.selectbox(
        "Tarih filtresi",
        options=["Tümü", "Bu Ay", "Bu Yıl"],
        help="Sonraki ödeme tarihine göre abonelikleri filtrele.",
    )

    filtre_df = df.copy()
    if secili_kat:
        filtre_df = filtre_df[filtre_df["kategori"].isin(secili_kat)]
    if arama:
        filtre_df = filtre_df[filtre_df["ad"].str.contains(arama, case=False, na=False)]

    if tarih_filtre != "Tümü":
        bugun = datetime.date.today()
        if tarih_filtre == "Bu Ay":
            filtre_df = filtre_df[filtre_df["sonraki_odeme"].apply(
                lambda x: datetime.date.fromisoformat(str(x)).month == bugun.month
                and datetime.date.fromisoformat(str(x)).year == bugun.year
            )]
        else:
            filtre_df = filtre_df[filtre_df["sonraki_odeme"].apply(
                lambda x: datetime.date.fromisoformat(str(x)).year == bugun.year
            )]

    st.markdown(f"**{len(filtre_df)}** abonelik listeleniyor")
    csv_export = filtre_df["id ad ucret para_birimi kategori sonraki_odeme notlar".split()].to_csv(index=False)
    st.download_button(
        "⬇️ Filtrelenen Abonelikleri CSV Olarak İndir",
        csv_export,
        file_name="abonelikler.csv",
        mime="text/csv",
    )

    for _, row in filtre_df.iterrows():
        gun = int(row["gun_kaldi"])
        renk = "#ef4444" if gun <= 3 else ("#f59e0b" if gun <= 7 else "#22c55e")

        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 1, 1])
            c1.markdown(f"**{row['ad']}**  \n`{row['kategori']}`")
            c2.markdown(f"💰 {row['ucret']} {row['para_birimi']}  \n≈ {row['try_ucret']:,.1f} ₺")
            c3.markdown(f"📅 {row['sonraki_odeme']}")
            c4.markdown(
                f"<span style='color:{renk};font-weight:700'>"
                f"{'BUGÜN' if gun==0 else f'{gun} gün' if gun>0 else 'GECİKMİŞ'}"
                f"</span>", unsafe_allow_html=True
            )
            if c5.button("📧", key=f"mail_{row['id']}", help="Hatırlatma e-postası gönder"):
                st.success(email_gonder_simule(row["ad"]))
            if c6.button("🗑️", key=f"sil_{row['id']}", help="Sil"):
                abonelik_sil(int(row["id"]))
                st.success(f"**{row['ad']}** silindi.")
                st.rerun()
            st.divider()


# ════════════════════════════════════════════════
#  SAYFA 4: GÜNCELLE
# ════════════════════════════════════════════════
elif menu == "✏️ Güncelle":

    st.markdown("""
    <div class="page-header">
        <div><h1>✏️ Abonelik Güncelle</h1><p>Mevcut abonelik bilgilerini düzenle</p></div>
    </div>""", unsafe_allow_html=True)

    df = tum_abonelikler()
    if df.empty:
        st.info("Güncellenecek abonelik yok.")
        st.stop()

    secenekler = {f"[{r['id']}] {r['ad']}": r for _, r in df.iterrows()}
    secim_key  = st.selectbox("Güncellenecek aboneliği seç", list(secenekler.keys()))
    secim      = secenekler[secim_key]

    with st.form("guncelle_form"):
        col1, col2 = st.columns(2)
        yeni_ad       = col1.text_input("Abonelik Adı", value=secim["ad"])
        yeni_kat      = col2.selectbox(
            "Kategori", KATEGORILER,
            index=KATEGORILER.index(secim["kategori"]) if secim["kategori"] in KATEGORILER else 0,
        )
        col3, col4, col5 = st.columns([2, 1, 1])
        yeni_ucret    = col3.number_input("Ücret", value=float(secim["ucret"]), step=0.01, format="%.2f")
        yeni_pb       = col4.selectbox(
            "Para Birimi", list(DOVIZ_KURLARI.keys()),
            index=list(DOVIZ_KURLARI.keys()).index(secim["para_birimi"]),
        )
        try:
            yeni_tarih = col5.date_input("Sonraki Ödeme", value=datetime.date.fromisoformat(str(secim["sonraki_odeme"])))
        except Exception:
            yeni_tarih = col5.date_input("Sonraki Ödeme", value=datetime.date.today())

        yeni_notlar   = st.text_area("Notlar", value=secim["notlar"] or "")
        submitted2    = st.form_submit_button("💾 Güncelle", use_container_width=True)

    if submitted2:
        abonelik_guncelle(
            int(secim["id"]), yeni_ad.strip(), yeni_ucret,
            yeni_pb, yeni_kat, yeni_tarih, yeni_notlar
        )
        st.success(f"✅ **{yeni_ad}** başarıyla güncellendi!")
        st.rerun()


# ════════════════════════════════════════════════
#  SAYFA 5: RAPORLAR
# ════════════════════════════════════════════════
elif menu == "📊 Raporlar":

    st.markdown("""
    <div class="page-header">
        <div><h1>📊 Grafiksel Raporlar</h1><p>Harcamalarını görsel olarak analiz et</p></div>
    </div>""", unsafe_allow_html=True)

    df = tum_abonelikler()
    if df.empty:
        st.info("Rapor için abonelik verisi bulunamadı.")
        st.stop()

    with st.expander("🔎 Raporları filtrele", expanded=True):
        rapor_kategoriler = st.multiselect(
            "Kategori",
            options=df["kategori"].unique().tolist(),
            default=df["kategori"].unique().tolist(),
            help="Raporları seçili kategoriler üzerinden isteğe göre oluşturun.",
        )
        col_rt1, col_rt2, col_rt3 = st.columns([1.5, 1.5, 1])
        rapor_periyodu = col_rt1.selectbox(
            "Periyot",
            options=["Özel Aralık", "Bu Ay", "Bu Yıl", "Tümü"],
            help="Raporu hızlıca belirli bir periyoda göre filtreleyin.",
        )
        baslangic_tarihi = col_rt2.date_input(
            "Başlangıç tarihi",
            value=datetime.date.today() - datetime.timedelta(days=30),
            min_value=datetime.date.today() - datetime.timedelta(days=365),
            max_value=datetime.date.today() + datetime.timedelta(days=365),
        )
        bitis_tarihi = col_rt3.date_input(
            "Bitiş tarihi",
            value=datetime.date.today() + datetime.timedelta(days=90),
            min_value=baslangic_tarihi,
            max_value=datetime.date.today() + datetime.timedelta(days=730),
        )
        rapor_modu = st.radio(
            "Rapor modu",
            ["Aylık", "Yıllık"],
            horizontal=True,
            help="Grafikleri ve toplamları aylık ya da yıllık bazda gösterir.",
        )

    bugun = datetime.date.today()
    if rapor_periyodu == "Bu Ay":
        baslangic_tarihi = bugun.replace(day=1)
        bitis_tarihi = bugun.replace(day=calendar.monthrange(bugun.year, bugun.month)[1])
    elif rapor_periyodu == "Bu Yıl":
        baslangic_tarihi = datetime.date(bugun.year, 1, 1)
        bitis_tarihi = datetime.date(bugun.year, 12, 31)
    elif rapor_periyodu == "Tümü":
        baslangic_tarihi = datetime.date.today() - datetime.timedelta(days=36500)
        bitis_tarihi = datetime.date.today() + datetime.timedelta(days=36500)

    if rapor_kategoriler:
        df = df[df["kategori"].isin(rapor_kategoriler)]

    df["tarih"] = df["sonraki_odeme"].apply(lambda x: datetime.date.fromisoformat(str(x)))
    df = df[(df["tarih"] >= baslangic_tarihi) & (df["tarih"] <= bitis_tarihi)]

    df["try_ucret"] = df.apply(lambda r: try_cevir(float(r["ucret"]), r["para_birimi"]), axis=1)
    df["rapor_ucret"] = df["try_ucret"] * (12 if rapor_modu == "Yıllık" else 1)

    if df.empty:
        st.warning("Seçilen filtrelere uygun abonelik verisi bulunamadı. Tarih aralığını genişletin.")
        st.stop()

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("#### 🥧 Kategoriye Göre Dağılım")
        fig_pasta = pasta_grafigi(df, value_col="rapor_ucret")
        st.pyplot(fig_pasta, use_container_width=True)
        plt.close(fig_pasta)

    with col_g2:
        st.markdown("#### 📊 Platform Bazlı Maliyetler")
        fig_sutun = sutun_grafigi(df, value_col="rapor_ucret")
        st.pyplot(fig_sutun, use_container_width=True)
        plt.close(fig_sutun)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        "⬇️ Filtrelenmiş Raporu CSV Olarak İndir",
        csv_buffer.getvalue(),
        file_name="abonelik_raporu.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # İstatistik özeti
    st.markdown("#### 📈 İstatistiksel Özet")
    toplam_rapor = df['rapor_ucret'].sum()
    ortalama_rapor = df['rapor_ucret'].mean()
    en_dusuk_rapor = df['rapor_ucret'].min()
    en_yuksek_rapor = df['rapor_ucret'].max()
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric(f"Toplam {rapor_modu}", f"{toplam_rapor:,.2f} ₺")
    col_s2.metric("Ortalama", f"{ortalama_rapor:,.2f} ₺")
    col_s3.metric("En Düşük", f"{en_dusuk_rapor:,.2f} ₺")
    col_s4.metric("En Yüksek", f"{en_yuksek_rapor:,.2f} ₺")

    st.markdown("---")

    # Kategori bazlı özet tablo
    kat_ozet = (
        df.groupby("kategori")["rapor_ucret"]
        .agg(["sum", "count", "mean"])
        .rename(columns={"sum": "Toplam (₺)", "count": "Adet", "mean": "Ortalama (₺)"})
        .sort_values("Toplam (₺)", ascending=False)
    )
    kat_ozet["Toplam (₺)"]    = kat_ozet["Toplam (₺)"].map("{:,.2f}".format)
    kat_ozet["Ortalama (₺)"]  = kat_ozet["Ortalama (₺)"].map("{:,.2f}".format)
    st.markdown("#### 📂 Kategoriye Göre Özet Tablo")
    st.dataframe(kat_ozet, use_container_width=True)
