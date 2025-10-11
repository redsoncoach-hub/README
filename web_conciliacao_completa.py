import streamlit as st
import pandas as pd
from ofxparse import OfxParser
from fuzzywuzzy import fuzz
import matplotlib.pyplot as plt
from datetime import datetime
import os

st.set_page_config(page_title="Conciliação CISSLive", layout="wide")
st.title("Sistema de Conciliação Bancária CISSLive - Web")

# ---------- Funções ----------

def ler_ofx(file):
    ofx = OfxParser.parse(file)
    transacoes = []
    for conta in ofx.accounts:
        for t in conta.statement.transactions:
            transacoes.append({
                "data": t.date,
                "descricao": t.payee,
                "valor": float(t.amount)
            })
    df = pd.DataFrame(transacoes)
    df['data'] = pd.to_datetime(df['data'])
    return df

def ler_csv_cisslive(file):
    df = pd.read_csv(file)
    df['valor'] = df['valor'].astype(float)
    df['data'] = pd.to_datetime(df['data'])
    return df

def classificar_categoria(desc):
    d = desc.lower()
    if any(x in d for x in ['salario','funcionario','folha']):
        return 'Salário'
    elif any(x in d for x in ['fornecedor','compra','material']):
        return 'Fornecedor'
    elif any(x in d for x in ['venda','receita','servico','pix']):
        return 'Receita'
    else:
        return 'Despesa'

def conciliar(df_ofx, df_ciss, tolerancia_valor=1.0):
    df_ofx['conciliado'] = False
    df_ciss['conciliado'] = False
    resultado = []
    for i, lanc in df_ciss.iterrows():
        match = df_ofx[(~df_ofx['conciliado']) & (abs(df_ofx['valor'] - lanc['valor']) <= tolerancia_valor)]
        melhor_match = None
        maior_sim = 0
        for idx, t in match.iterrows():
            sim = fuzz.token_sort_ratio(lanc['descricao'], t['descricao'])
            if sim > maior_sim:
                maior_sim = sim
                melhor_match = idx
        categoria = classificar_categoria(lanc['descricao'])
        if melhor_match is not None and maior_sim >= 60:
            df_ofx.at[melhor_match, 'conciliado'] = True
            df_ciss.at[i, 'conciliado'] = True
            resultado.append({
                "descricao": lanc['descricao'],
                "valor": lanc['valor'],
                "data": lanc['data'],
                "status": "Conciliado",
                "categoria": categoria,
                "baixado": True
            })
        else:
            resultado.append({
                "descricao": lanc['descricao'],
                "valor": lanc['valor'],
                "data": lanc['data'],
                "status": "Pendente",
                "categoria": categoria,
                "baixado": False
            })
    return pd.DataFrame(resultado)

def gerar_dashboard(df):
    df_group = df.groupby(['categoria','status'])['valor'].sum().unstack().fillna(0)
    st.bar_chart(df_group)

def salvar_csv(df, filename="relatorio_baixa.csv"):
    df.to_csv(filename, index=False)
    st.success(f"CSV de baixa salvo: {filename}")

def salvar_historico(df):
    os.makedirs("historico_conciliacoes", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"historico_conciliacoes/historico_{timestamp}.csv"
    df.to_csv(path, index=False)
    st.info(f"Histórico salvo: {path}")

# ---------- Interface Web ----------

st.sidebar.header("Configurações")
tolerancia_valor = st.sidebar.number_input("Tolerância de valor (R$)", min_value=0.0, value=1.0, step=0.1)

extrato_file = st.file_uploader("Upload Extrato OFX", type="ofx")
lancamentos_file = st.file_uploader("Upload CSV Lançamentos CISSLive", type="csv")

if extrato_file and lancamentos_file:
    df_ofx = ler_ofx(extrato_file)
    df_ciss = ler_csv_cisslive(lancamentos_file)
    
    df_result = conciliar(df_ofx, df_ciss, tolerancia_valor)
    
    st.subheader("✅ Resultado da Conciliação")
    st.dataframe(df_result)
    
    gerar_dashboard(df_result)
    
    salvar_csv(df_result)
    salvar_historico(df_result)
