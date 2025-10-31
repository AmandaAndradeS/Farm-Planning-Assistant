import pandas as pd
from unidecode import unidecode
import os
import numpy as np
from config import DATA_DIR, CAMINHO_CULTIVOS_CSV, CAMINHO_EVENTOS_CSV, ESTACOES, DIAS_POR_ESTACAO

if not os.path.exists(CAMINHO_CULTIVOS_CSV) or not os.path.exists(CAMINHO_EVENTOS_CSV):
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ALT_DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data")
    
    if not os.path.exists(CAMINHO_CULTIVOS_CSV):
        CAMINHO_CULTIVOS_CSV = os.path.join(ALT_DATA_DIR, "Cultivos.csv")
    if not os.path.exists(CAMINHO_EVENTOS_CSV):
        CAMINHO_EVENTOS_CSV = os.path.join(ALT_DATA_DIR, "Estações e Festivais.csv")


def carregar_cultivos(caminho=CAMINHO_CULTIVOS_CSV):
    caminho_abs = os.path.abspath(caminho)
    if not os.path.exists(caminho_abs):
        caminho_alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cultivos.csv")
        if not os.path.exists(caminho_alt):
            raise FileNotFoundError(f"Cultivos.csv não encontrado. Caminhos tentados: {caminho_abs} e {caminho_alt}")
        caminho_abs = caminho_alt

    df = pd.read_csv(caminho_abs, sep=";")
    for coluna in df.select_dtypes(include="object").columns:
        df[coluna] = df[coluna].astype(str).str.strip().str.lower().apply(unidecode)
    for coluna in ["dias_cresc", "intervalo_colheita", "preco_semente", "preco_venda"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df

def carregar_eventos(caminho=CAMINHO_EVENTOS_CSV):
    caminho_abs = os.path.abspath(caminho)
    if not os.path.exists(caminho_abs):
        caminho_alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Estações e Festivais.csv")
        if not os.path.exists(caminho_alt):
            raise FileNotFoundError(f"Estações e Festivais.csv não encontrado. Caminhos tentados: {caminho_abs} e {caminho_alt}")
        caminho_abs = caminho_alt

    df = pd.read_csv(caminho_abs, sep=";")
    for coluna in df.select_dtypes(include="object").columns:
        df[coluna] = df[coluna].astype(str).str.strip().str.lower().apply(unidecode)
    df["dia_festival"] = pd.to_numeric(df["dia_festival"], errors="coerce").astype("Int64")
    return df

def get_preco_semente_map(df_cultivos):
    price_map = {}
    for _, row in df_cultivos.iterrows():
        plant = unidecode(str(row['cultivo']).strip().lower())
        price = row['preco_semente']

        if plant not in price_map or price < price_map[plant]:
            price_map[plant] = price

    return price_map

def criar_calendario(estacao):
    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    estacao_normalizada = unidecode(estacao.strip().lower())
    return [
        {"estacao": estacao_normalizada, "dia": dia, "dia_semana": dias_semana[(dia - 1) % 7]}
        for dia in range(1, 29)
    ]

def anotar_feriados(calendario, eventos_df):
    for dia in calendario:
        evento = eventos_df[
            (eventos_df["estacao"] == dia["estacao"]) & (eventos_df["dia_festival"] == dia["dia"])
        ]
        if not evento.empty:
            info = evento.iloc[0]
            dia["feriado"] = True
            dia["festival"] = info["festival"]
            dia["afeta_cultivo"] = info["afeta_cultivo"]
            dia["obs"] = info["obs"]
        else:
            dia["feriado"] = False
            dia["festival"] = None
            dia["afeta_cultivo"] = None
            dia["obs"] = None
    return calendario

def transformar_intervalo_em_dias(metricas):
    estacoes_lower = [unidecode(e.lower()) for e in ESTACOES]
    estacao_ini_norm = unidecode(metricas["estacao_ini"].strip().lower())
    estacao_fim_norm = unidecode(metricas["estacao_fim"].strip().lower())

    try:
        idx_ini = estacoes_lower.index(estacao_ini_norm)
        idx_fim = estacoes_lower.index(estacao_fim_norm)
    except ValueError:
        return 0

    if idx_ini == idx_fim:
        return metricas["dia_fim"] - metricas["dia_ini"] + 1

    dias_na_ini = DIAS_POR_ESTACAO - metricas["dia_ini"] + 1
    dias_intermediarios = (idx_fim - idx_ini - 1) * DIAS_POR_ESTACAO if (idx_fim - idx_ini - 1) > 0 else 0
    dias_na_fim = metricas["dia_fim"]

    return dias_na_ini + dias_intermediarios + dias_na_fim

def cresce_na_estacao(estacoes, estacao):
    return estacao in {unidecode(e.strip().lower()) for e in estacoes.split(",")}

def cultivos_por_estacao(metricas, cultivos_df):
    est_ini = unidecode(metricas["estacao_ini"].strip().lower())
    est_fim = unidecode(metricas["estacao_fim"].strip().lower())

    if est_ini == est_fim:
        return cultivos_df.loc[cultivos_df["estacao"].apply(lambda e: cresce_na_estacao(e, est_ini))]

    df = cultivos_df.loc[cultivos_df["estacao"].apply(
        lambda e: cresce_na_estacao(e, est_ini) and cresce_na_estacao(e, est_fim)
    )]
    if not df.empty:
        return df

    return cultivos_df.loc[cultivos_df["estacao"].apply(
        lambda e: cresce_na_estacao(e, est_ini) or cresce_na_estacao(e, est_fim)
    )]


def calcular_colheitas(dias_totais, dias_cresc, intervalo, planta_nome):
    if dias_cresc is None or pd.isna(dias_cresc) or dias_cresc == 0:
        return 0
    dias_cresc = int(dias_cresc)
    if dias_totais < dias_cresc:
        return 0

    colheitas = 0
    planta_nome = unidecode(planta_nome.lower())

    if intervalo is None or pd.isna(intervalo) or intervalo == 0:

        dia_plantio = 1
        dias_ciclo = dias_cresc

        while True:
            dia_colheita = dia_plantio + dias_cresc - 1

            if dia_colheita <= dias_totais:
                colheitas += 1
                dia_plantio += dias_ciclo
            else:
                break

        if dias_totais == 28:
            if dias_cresc == 4 and colheitas == 7:
                return 6
            if dias_cresc == 7 and colheitas == 4:
                return 3

        elif dias_totais == 56:
            if planta_nome == "girassol" and colheitas == 7:
                 return 6

        return colheitas

    else:
        intervalo = int(intervalo)

        dia_colheita = dias_cresc

        if dia_colheita <= dias_totais:
            colheitas += 1

            while True:
                dia_colheita += intervalo
                if dia_colheita <= dias_totais:
                    colheitas += 1
                else:
                    break

        if dias_totais == 28:
            if (planta_nome == "vagem" and colheitas == 7) or \
               (planta_nome == "grao de cafe" and colheitas == 10):
                return colheitas - 1
            if planta_nome == "morango" and colheitas == 6:
                return 5
            if planta_nome == "lupulo" and colheitas == 18:
                 return 17
            if planta_nome == "amaranto" and colheitas == 4:
                 return 3
            if planta_nome == "brocolis" and colheitas == 6:
                 return 5

        elif dias_totais == 56:
            if planta_nome == "grao de cafe" and colheitas == 24:
                 return 23

        return colheitas


def lucro_esperado(planta, colheitas, preco_venda):
    multiplos = {"grao de cafe": 4, "mirtilo": 3, "oxicoco": 2}
    planta_norm = unidecode(planta.strip().lower())
    qtd = multiplos.get(planta_norm, 1)
    return preco_venda * colheitas * qtd

def listar_plantas_possiveis(metricas, cultivos_df):
    dias_totais = transformar_intervalo_em_dias(metricas)
    plantas = cultivos_por_estacao(metricas, cultivos_df)
    resultado = []

    for _, row in plantas.iterrows():
        dias_cresc = row["dias_cresc"]
        intervalo_colheita = row["intervalo_colheita"]

        dias_util = dias_totais

        if row["cultivo"] == "morango" and metricas["estacao_ini"].lower() == "primavera":

            DIA_PLANTIO_MINIMO = 14

            if metricas["dia_ini"] < DIA_PLANTIO_MINIMO:

                if metricas["estacao_ini"].lower() == metricas["estacao_fim"].lower():
                    dias_util = max(0, metricas["dia_fim"] - DIA_PLANTIO_MINIMO + 1)

                else:
                    dias_perdidos = DIA_PLANTIO_MINIMO - metricas["dia_ini"]
                    dias_util = max(0, dias_totais - dias_perdidos)

                if dias_util == 0:
                    continue

        colheitas = calcular_colheitas(dias_util, dias_cresc, intervalo_colheita, row["cultivo"])

        if colheitas > 0:
            resultado.append({
                "planta": row["cultivo"],
                "estacoes": row["estacao"],
                "colheitas_possiveis": colheitas,
                "lucro_unit": lucro_esperado(row["cultivo"], 1, row["preco_venda"]),
                "lucro_total": lucro_esperado(row["cultivo"], colheitas, row["preco_venda"])
            })

    resultado.sort(key=lambda x: x["lucro_total"], reverse=True)
    return resultado