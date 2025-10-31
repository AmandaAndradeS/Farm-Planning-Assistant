from unidecode import unidecode
import pandas as pd
import traceback
import os
from config import ESTACOES

try:
    from logica import carregar_eventos, criar_calendario, anotar_feriados, carregar_cultivos
except ImportError as e:
    raise ImportError(f"Falha ao importar funções de modelo.py para narrativa.py. Garanta que 'carregar_cultivos' está no modelo. Detalhe: {e}")

def _criar_calendario_completo(eventos_df):
    todas_estacoes = [unidecode(e.lower()) for e in ESTACOES]
    calendario_completo = []
    for est in todas_estacoes:
        calendario_completo.extend(criar_calendario(est))

    return anotar_feriados(calendario_completo, eventos_df)


def _filtrar_feriados_por_intervalo(metricas, calendario_completo):

    estacoes_lower = [unidecode(e.lower()) for e in ESTACOES]
    est_ini = unidecode(metricas["estacao_ini"].strip().lower())
    est_fim = unidecode(metricas["estacao_fim"].strip().lower())

    try:
        idx_ini = estacoes_lower.index(est_ini)
        idx_fim = estacoes_lower.index(est_fim)
    except ValueError as e:
        print(f"Erro ao encontrar índice da estação: {e}")
        return []

    feriados_encontrados = []
    for dia in calendario_completo:
        if not dia.get("feriado"):
            continue

        est_atual_norm = dia["estacao"]

        try:
            idx_atual = estacoes_lower.index(est_atual_norm)
        except ValueError:
            continue

        dentro_do_intervalo = False

        if idx_ini == idx_fim:
            if idx_atual == idx_ini and metricas["dia_ini"] <= dia["dia"] <= metricas["dia_fim"]:
                dentro_do_intervalo = True
        elif idx_ini < idx_fim:
            if idx_ini < idx_atual < idx_fim:
                dentro_do_intervalo = True
            elif idx_atual == idx_ini and dia["dia"] >= metricas["dia_ini"]:
                dentro_do_intervalo = True
            elif idx_atual == idx_fim and dia["dia"] <= metricas["dia_fim"]:
                dentro_do_intervalo = True

        if dentro_do_intervalo:
            feriados_encontrados.append(dia)

    return feriados_encontrados


def criar_texto_plano_amigavel(metricas, melhores_plantas, df_cultivos_cache, df_eventos_cache, preco_semente_map):


    quantidade_input = metricas["quantidade_input"]
    unidade = metricas["unidade"]
    data_str = metricas["data_inicio"]
    quantidade_quadrados = metricas["quantidade_quadrados"]
    dias_totais = metricas["dias_totais"]
    opcao = metricas["opcao_estrategia"]

    texto_final = (f"--- 📑 Plano de Cultivo Otimizado | {opcao} ---\n"
                   f"Área de Plantio: {quantidade_quadrados} Quadrado(s)\n"
                   f"Período de Análise: {data_str}\n"
                   f"Dias Úteis no Período: {dias_totais}\n")

    if not melhores_plantas:
        texto_final += "\nCultivos\n🌿 Nenhuma planta pode ser colhida neste período. Tente aumentar o intervalo ou rever as sementes disponíveis!"
    else:
        texto_final += f"\n--- 🌿Cultivos Otimizados - Ordenado por Lucro🌿 ---\n"

        for i, p in enumerate(melhores_plantas):
            planta_norm = unidecode(p['planta'].strip().lower())

            preco_semente_unit = preco_semente_map.get(planta_norm, 0)
            custo_semente_total = preco_semente_unit * quantidade_quadrados

            lucro_campo_total = p["lucro_total"] * quantidade_quadrados
            lucro_formatado = f"{lucro_campo_total:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")
            custo_formatado = f"{custo_semente_total:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")

            texto_final += (f"\n{i+1}. {p['planta'].title()}\n"
                            f"   ▪️ Colheitas Possíveis: {p['colheitas_possiveis']} vezes\n"
                            f"   ▪️ Custo Total de Sementes: {custo_formatado} G\n"
                            f"   ▪️ Lucro Total Projetado: {lucro_formatado} G")

    try:
        calendario_completo = _criar_calendario_completo(df_eventos_cache)
        feriados = _filtrar_feriados_por_intervalo(metricas, calendario_completo)

        if feriados:
            texto_final += "\n\n--- 🎉Eventos e Festivais no Período🎉 ---\n\n"

            feriados_unicos = pd.DataFrame(feriados).drop_duplicates(subset=['estacao', 'dia']).to_dict('records')

            for f in feriados_unicos:
                afeta = f.get("afeta_cultivo", "nao")

                if afeta == 'sim':
                    status_icon = '✖️'
                    status_text = 'Afeta Lojas/Área'
                elif afeta == 'parcial':
                    status_icon = '❗'
                    status_text = 'Afeta Parcialmente'
                else:
                    status_icon = '✔️'
                    status_text = 'Sem Impacto'

                obs = f['obs'].capitalize().replace("nan", "N/A")

                texto_final += (f"\n  - {f['estacao'].capitalize()} D.{f['dia']} - {f['festival'].capitalize()}\n"
                                f"   > Impacto: {status_icon} {status_text}\n"
                                f"({obs})\n")

        else:
            texto_final += "✅ Nenhuma interrupção por festival no período."

    except Exception as e:
        texto_final += f"[AVISO: Falha ao carregar Eventos/Festivais. Garanta que 'Estações e Festivais.csv' está acessível. Erro: {e}]"
        pass
    return texto_final