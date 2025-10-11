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
    for i,lanc in df_ciss.iterrows():
        match = df_ofx[(~df_ofx['conciliado']) & (abs(df_ofx['valor']-lanc['valor'])<=tolerancia_valor)]
        melhor_match = None
        maior_sim = 0
        for idx,t in match.iterrows():
            sim = fuzz.token_sort_ratio(lanc['descricao'], t['descricao'])
            if sim > maior_sim:
                maior_sim = sim
                melhor_match = idx
        categoria = classificar_categoria(lanc['descricao'])
        if melhor_match is not None and maior_sim >= 60:
            df_ofx.at[melhor_match,'conciliado']=True
            df_ciss.at[i,'conciliado']=True
            resultado.append({
                "descricao":lanc['descricao'],
                "valor":lanc['valor'],
                "data":lanc['data'],
                "statu
