import traceback
from unidecode import unidecode
try:
    from logica import carregar_cultivos, listar_plantas_possiveis, transformar_intervalo_em_dias
    from tratamento_menssagem import criar_texto_plano_amigavel
except ImportError as e:
    print(f"ERRO CRÍTICO NO TRATAMENTO.PY: Não foi possível importar módulos necessários. Detalhe: {e}")
    def criar_texto_plano_amigavel(metricas, melhores_plantas, df_cultivos_cache, df_eventos_cache, preco_semente_map):
        return f"ERRO CRÍTICO NA NARRATIVA: Falha na importação do arquivo narrativa.py. Verifique se o arquivo está salvo e no mesmo diretório. Detalhe: {e}"


def parse_intervalo_data(data_str):

    try:
        partes = data_str.split(" -> ")
        if len(partes) != 2:
            raise ValueError("Formato de intervalo incompleto.")

        data_ini_str = partes[0].strip()
        data_fim_str = partes[1].strip()

        def extrair_data(data):
            estacao_parte, dia_parte = data.split(" D")
            estacao = unidecode(estacao_parte.strip().lower()).capitalize()
            dia = int(dia_parte.strip())
            return estacao, dia

        estacao_ini, dia_ini = extrair_data(data_ini_str)
        estacao_fim, dia_fim = extrair_data(data_fim_str)

        return {
            "estacao_ini": estacao_ini,
            "dia_ini": dia_ini,
            "estacao_fim": estacao_fim,
            "dia_fim": dia_fim
        }
    except Exception as e:
        raise ValueError(f"Falha ao analisar a string de data '{data_str}'. Detalhe: {e}")


def tratar_e_processar_dados(dados_entrada, df_cultivos_cache, df_eventos_cache, preco_semente_map):

    opcao = dados_entrada["opcao_estrategia"]
    quantidade_input = dados_entrada["quantidade"]
    data_str = dados_entrada["data_inicio"]

    if "Aspersor" in opcao:
        quantidade_quadrados = quantidade_input * 8
        unidade = "Aspersores"
    elif "Área Plantável" in opcao:
        quantidade_quadrados = quantidade_input
        unidade = "Quadrados"
    else:
        quantidade_quadrados = quantidade_input
        unidade = "Unidade(s)"

    metricas = parse_intervalo_data(data_str)

    metricas["quantidade_input"] = quantidade_input
    metricas["unidade"] = unidade
    metricas["opcao_estrategia"] = opcao
    metricas["data_inicio"] = data_str
    metricas["quantidade_quadrados"] = quantidade_quadrados

    try:
        metricas["dias_totais"] = transformar_intervalo_em_dias(metricas)
    except Exception as e:
        metricas["dias_totais"] = 0
        print(f"Erro ao calcular dias totais: {e}")


    try:
        melhores_plantas = listar_plantas_possiveis(metricas, df_cultivos_cache)
    except Exception as e:
        print(f"Erro na execução da lógica do modelo (Carregar Cultivos ou Plantas Possíveis): {e}")
        melhores_plantas = []

    texto_final = criar_texto_plano_amigavel(metricas, melhores_plantas, df_cultivos_cache, df_eventos_cache, preco_semente_map)

    return texto_final