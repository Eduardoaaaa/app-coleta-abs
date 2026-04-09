import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuração focada em mobile
st.set_page_config(page_title="Coleta ABS", page_icon="📱", layout="centered", initial_sidebar_state="collapsed")

# LIGAÇÃO À NUVEM: Lê a ligação secreta do ficheiro secrets.toml
@st.cache_resource
def conectar_banco():
    return create_engine(st.secrets["DATABASE_URL"])

st.title("📱 Coleta de Stock")
st.caption("Registe os itens encontrados na prateleira.")

if 'loja_atual' not in st.session_state:
    st.session_state['loja_atual'] = "ABS Clube"

loja = st.selectbox("🏬 Loja atual:", ["ABS Clube", "ABS Breu", "ABS Repartimento", "ABS Vila"], 
                    index=["ABS Clube", "ABS Breu", "ABS Repartimento", "ABS Vila"].index(st.session_state['loja_atual']))
st.session_state['loja_atual'] = loja

st.markdown("---")

with st.form("form_coleta", clear_on_submit=True):
    st.markdown("### Novo Item")
    produto = st.text_input("🔍 Nome ou Código do Produto:")
    quantidade = st.number_input("📦 Quantidade contada:", min_value=1, step=1)
    enviado = st.form_submit_button("Registar Item 💾", use_container_width=True)
    
    if enviado:
        if produto.strip() == "":
            st.error("⚠️ Digite o nome ou código do produto!")
        else:
            try:
                engine = conectar_banco()
                hoje = datetime.now().strftime('%Y-%m-%d')
                
                # Prepara os dados para o formato que o Pandas entende
                dados = pd.DataFrame([{
                    'data_entrega': hoje,
                    'cod_loja': '-',
                    'nome_loja': loja,
                    'cod_produto': 'COLETA_MOBILE',
                    'nome_produto': produto.upper().strip(),
                    'quantidade': float(quantidade)
                }])
                
                # Envia diretamente para o Postgres na nuvem
                with engine.connect() as conn:
                    dados.to_sql('movimentacoes_entrada', con=conn, if_exists='append', index=False)
                
                st.success(f"✅ {quantidade}x {produto.upper()} registado na nuvem!")
            except Exception as e:
                st.error(f"Erro ao guardar: {e}")

# Histórico Rápido (Lido da Nuvem)
st.markdown("---")
st.markdown("🕒 **Últimos itens registados hoje:**")
try:
    engine = conectar_banco()
    query = f"""
        SELECT nome_produto, quantidade 
        FROM movimentacoes_entrada 
        WHERE nome_loja = '{loja}' AND cod_produto = 'COLETA_MOBILE' AND data_entrega = '{datetime.now().strftime('%Y-%m-%d')}'
        ORDER BY id DESC LIMIT 5
    """
    with engine.connect() as conn:
        df_recentes = pd.read_sql_query(text(query), conn)
        
    if not df_recentes.empty:
        st.dataframe(df_recentes, hide_index=True, use_container_width=True)
    else:
        st.caption("Nenhum item coletado ainda.")
except Exception as e:
    st.caption("Aguardando ligação à base de dados...")