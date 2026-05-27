import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestione IVA Forfettaria", layout="wide", page_icon="💰")

# --- DEFINIZIONE COLONNE ---
# Definiamo le colonne una volta sola per evitare errori di mismatch
COLONNE = ["Data", "Descrizione", "Categoria", "Importo", "Fatturato"]
DB_FILE = "database_entrate.csv"

# --- FUNZIONI DATI ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Assicuriamoci che le colonne siano quelle giuste
            if list(df.columns) != COLONNE:
                return pd.DataFrame(columns=COLONNE)
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        except:
            return pd.DataFrame(columns=COLONNE)
    else:
        return pd.DataFrame(columns=COLONNE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Inizializzazione Session State
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- PARAMETRI FISCALI ---
COEFF_REDDITIVITA = 0.78
INPS_ALIQUOTA = 0.2607

st.title("💰 Gestione Forfettario Fitness")

# --- SIDEBAR PER INSERIMENTO ---
st.sidebar.header("➕ Registra Incasso")
with st.sidebar.form("input_form", clear_on_submit=True):
    data_incasso = st.date_input("Data", datetime.now())
    descrizione = st.text_input("Cliente / Descrizione")
    categoria = st.selectbox("Servizio", ["Personal Training", "Abbonamenti", "Coaching online", "Docente", "Altri servizi"])
    importo = st.number_input("Importo Lordo (€)", min_value=0.0, step=10.0)
    fatturato = st.checkbox("Fattura Emessa?", value=True)
    submit = st.form_submit_button("Salva Pagamento")

if submit:
    # Creiamo la nuova riga come dizionario (metodo più sicuro)
    nuova_entry = {
        "Data": [pd.to_datetime(data_incasso)],
        "Descrizione": [descrizione],
        "Categoria": [categoria],
        "Importo": [importo],
        "Fatturato": [fatturato]
    }
    nuovo_df = pd.DataFrame(nuova_entry)
    
    # Uniamo i dati
    st.session_state.data = pd.concat([st.session_state.data, nuovo_df], ignore_index=True)
    save_data(st.session_state.data)
    st.rerun()

# --- ANALISI E VISUALIZZAZIONE ---
df = st.session_state.data

if not df.empty:
    # Pulizia e preparazione dati
    df['Data'] = pd.to_datetime(df['Data'])
    df['Mese'] = df['Data'].dt.strftime('%Y-%m')
    
    # --- CALCOLO TASSE ---
    lordo_totale = df['Importo'].sum()
    # Calcolo solo su quanto fatturato
    lordo_fatturato = df[df['Fatturato'] == True]['Importo'].sum()
    
    # Sidebar tasse
    st.sidebar.divider()
    scelta_tassa = st.sidebar.radio("Aliquota Imposta Sostitutiva", ["5%", "15%"])
    aliquota_sost = 0.05 if "5" in scelta_tassa else 0.15
    
    imponibile = lordo_fatturato * COEFF_REDDITIVITA
    tasse_inps = imponibile * INPS_ALIQUOTA
    tasse_sostitutiva = (imponibile - tasse_inps) * aliquota_sost
    totale_tasse = tasse_inps + tasse_sostitutiva
    netto_stimato = lordo_totale - totale_tasse

    # --- DASHBOARD ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Incasso Totale", f"€ {lordo_totale:,.2f}")
    c2.metric("Tasse Stimate", f"€ {totale_tasse:,.2f}", delta="- stimato", delta_color="inverse")
    c3.metric("Netto Reale", f"€ {netto_stimato:,.2f}")

    # --- GRAFICO MENSILE ---
    st.subheader("📈 Andamento Mensile (Lordo)")
    # Ordiniamo per data per il grafico
    df_sorted = df.sort_values('Data')
    mensile = df_sorted.groupby('Mese')['Importo'].sum()
    st.bar_chart(mensile)

    # --- RIASSUNTO ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📂 Per Servizio")
        per_cat = df.groupby('Categoria')['Importo'].sum()
        st.table(per_cat)
    
    with col_b:
        st.subheader("🧾 Stato Fatturazione")
        per_fattura = df.groupby('Fatturato')['Importo'].sum()
        st.table(per_fattura)

    # --- REGISTRO ---
    st.subheader("📝 Registro Operazioni")
    st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
    
    # Bottone Reset
    if st.sidebar.button("🗑️ Cancella tutto il database"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.session_state.data = pd.DataFrame(columns=COLONNE)
            st.rerun()
else:
    st.info("Benvenuto! Registra il tuo primo incasso dalla barra laterale per vedere le statistiche.")
