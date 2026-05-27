import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestione IVA Forfettaria", layout="wide", page_icon="💰")

# --- FILE DI DATABASE ---
DB_FILE = "database_entrate.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    else:
        return pd.DataFrame(columns=["Data", "Descrizione", "Categoria", "Importo", "Fatturato"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Caricamento iniziale dei dati
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- PARAMETRI FISCALI (Coefficiente 78%) ---
COEFF_REDDITIVITA = 0.78
INPS_ALIQUOTA = 0.2607 # Gestione Separata INPS

# --- INTERFACCIA ---
st.title("💰 Gestione Entrate Partita IVA")
st.markdown("Monitoraggio incassi, tasse e netto mensile.")

# --- SIDEBAR PER INSERIMENTO ---
st.sidebar.header("➕ Registra Incasso")
with st.sidebar.form("input_form", clear_on_submit=True):
    data_incasso = st.date_input("Data", datetime.now())
    descrizione = st.text_input("Cliente / Descrizione")
    categoria = st.selectbox("Servizio", ["Personal Training", "Abbonamenti", "Coaching online", "Docente", "Altri servizi"])
    importo = st.number_input("Importo Lordo (€)", min_value=0.0, step=50.0)
    fatturato = st.checkbox("Fattura Emessa?", value=True)
    
    submit = st.form_submit_button("Salva Pagamento")

if submit:
    nuova_riga = pd.DataFrame([[data_incasso, descrizione, categoria, importo, fatturato]], 
                             columns=st.session_state.data.columns)
    st.session_state.data = pd.concat([st.session_state.data, nuova_riga], ignore_index=True)
    save_data(st.session_state.data)
    st.sidebar.success("Salvato con successo!")

# --- CALCOLI FISCALI ---
df = st.session_state.data
if not df.empty:
    # Preparazione date
    df['Data'] = pd.to_datetime(df['Data'])
    df['Mese'] = df['Data'].dt.strftime('%Y-%m')
    
    # Calcolo Tasse
    incasso_totale = df['Importo'].sum()
    incasso_fatturato = df[df['fatturato'] == True]['Importo'].sum() if 'fatturato' in df.columns else df[df['Fatturato'] == True]['Importo'].sum()
    
    # Logica Forfettario: Tasse solo sul fatturato
    imponibile = incasso_fatturato * COEFF_REDDITIVITA
    tasse_inps = imponibile * INPS_ALIQUOTA
    
    st.sidebar.divider()
    tipo_tassa = st.sidebar.radio("Aliquota Imposta Sostitutiva", ["5% (Start-up)", "15% (Standard)"])
    aliquota_sostitutiva = 0.05 if "5%" in tipo_tassa else 0.15
    
    tasse_sostitutiva = (imponibile - tasse_inps) * aliquota_sostitutiva
    totale_tasse = tasse_inps + tasse_sostitutiva
    netto_reale = incasso_totale - totale_tasse

    # --- DASHBOARD METRICHE ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Totale Incassato", f"€ {incasso_totale:,.2f}")
    col2.metric("Tasse Stimate (INPS + Sostitutiva)", f"€ {totale_tasse:,.2f}", delta_color="inverse")
    col3.metric("Netto Disponibile", f"€ {netto_reale:,.2f}")

    # --- GRAFICO MENSILE ---
    st.subheader("📈 Andamento Mensile (Lordo)")
    mensile_df = df.groupby('Mese')['Importo'].sum().reset_index()
    fig = px.bar(mensile_df, x='Mese', y='Importo', text_auto='.2s', color_discrete_sequence=['#2ecc71'])
    st.plotly_chart(fig, use_container_width=True)

    # --- RIASSUNTO PER CATEGORIA ---
    st.subheader("📂 Analisi per Servizio")
    cat_df = df.groupby('Categoria')['Importo'].sum().reset_index()
    fig_pie = px.pie(cat_df, values='Importo', names='Categoria', hole=0.4)
    st.plotly_chart(fig_pie)

    # --- TABELLA DATI ---
    st.subheader("📝 Registro Transazioni")
    st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
    
    # Bottone elimina ultimo inserimento (per errori)
    if st.button("Elimina ultima riga inserita"):
        st.session_state.data = st.session_state.data[:-1]
        save_data(st.session_state.data)
        st.rerun()

else:
    st.info("Nessun dato registrato. Usa la barra laterale per inserire il tuo primo incasso!")
