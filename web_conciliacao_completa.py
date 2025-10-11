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
