import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuração focada em mobile
st.set_page_config(page_title="Coleta ABS", page_icon="📱", layout="centered", initial_sidebar_state="collapsed")

@st.cache_resource
def conectar_banco():
    return create_engine(st.secrets["DATABASE_URL"])

# --- NOVA FUNÇÃO: Busca o padrão de produtos ---
# O cache de 60 segundos garante que o app fique rápido, mas atualize a lista se você importar produtos novos no painel
@st.cache_data(ttl=60)
def buscar_produtos_cadastrados():
    try:
        engine = conectar_banco()
        # Busca apenas os nomes únicos que já deram entrada no sistema alguma vez
        query = "SELECT DISTINCT nome_produto FROM movimentacoes_entrada WHERE nome_produto IS NOT NULL AND nome_produto != '' ORDER BY nome_produto"
        with engine.connect() as conn:
            df_prods = pd.read_sql_query(text(query), conn)
            return df_prods['nome_produto'].tolist()
    except Exception:
        return []

st.title("📱 Coleta de Estoque")
st.caption("Registre os itens encontrados na prateleira.")

if 'loja_atual' not in st.session_state:
    st.session_state['loja_atual'] = "ABS Clube"

loja = st.selectbox("🏬 Loja atual:", ["ABS Clube", "ABS Breu", "ABS Repartimento", "ABS Vila"], 
                    index=["ABS Clube", "ABS Breu", "ABS Repartimento", "ABS Vila"].index(st.session_state['loja_atual']))
st.session_state['loja_atual'] = loja

st.markdown("---")

# Carrega a lista de produtos padronizados do banco
lista_produtos = buscar_produtos_cadastrados()

with st.form("form_coleta", clear_on_submit=True):
    st.markdown("### Novo Item")
    
    # --- NOVA CAIXA DE BUSCA INTELIGENTE ---
    if lista_produtos:
        # Cria um selectbox que aceita digitação. A primeira opção é vazia para forçar o usuário a escolher.
        produto = st.selectbox("🔍 Busque o Produto:", [""] + lista_produtos)
    else:
        # Fallback: Se o banco estiver zerado, permite digitar para não travar a operação
        produto = st.text_input("🔍 Digite o Nome do Produto (Nenhum cadastrado ainda):")
        
    quantidade = st.number_input("📦 Quantidade contada:", min_value=1, step=1)
    enviado = st.form_submit_button("Registrar Item 💾", use_container_width=True)
    
    if enviado:
        if produto == "" or produto.strip() == "":
            st.error("⚠️ Por favor, selecione um produto na lista!")
        else:
            try:
                engine = conectar_banco()
                hoje = datetime.now().strftime('%Y-%m-%d')
                
                dados = pd.DataFrame([{
                    'data_entrega': hoje,
                    'cod_loja': '-',
                    'nome_loja': loja,
                    'cod_produto': 'COLETA_MOBILE',
                    'nome_produto': produto.upper().strip(),
                    'quantidade': float(quantidade)
                }])
                
                with engine.connect() as conn:
                    dados.to_sql('movimentacoes_entrada', con=conn, if_exists='append', index=False)
                
                st.success(f"✅ {quantidade}x {produto.upper()} registrado na nuvem!")
            except Exception as e:
                st.error(f"Erro ao guardar: {e}")

# Histórico Rápido (Lido da Nuvem)
st.markdown("---")
st.markdown("🕒 **Últimos itens registrados hoje:**")
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
