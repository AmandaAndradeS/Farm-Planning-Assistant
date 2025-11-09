import os
import sys
import tempfile
import shutil

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    PROJECT_ROOT = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(BASE_DIR)

ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def get_cursor_spec(filename):
  
    cursor_file = os.path.join(ASSETS_DIR, filename)

    if not os.path.exists(cursor_file):
        return "arrow"

    if getattr(sys, 'frozen', False):
        try:
            temp_path = os.path.join(tempfile.gettempdir(), filename)

            shutil.copyfile(cursor_file, temp_path)

            return f"@{temp_path.replace(os.sep, '/')}"

        except Exception as e:
            print(f"Erro ao copiar cursor '{filename}' para tempfile: {e}")
            return "arrow"
    else:
        return f"@assets/{filename}"


CAMINHO_IMAGENS = os.path.join(ASSETS_DIR, "images")
CAMINHO_IMAGENS_PERSONAGENS = os.path.join(CAMINHO_IMAGENS, "images personagens")
CAMINHO_CULTIVOS_CSV = os.path.join(DATA_DIR, "Cultivos.csv")
CAMINHO_EVENTOS_CSV = os.path.join(DATA_DIR, "Estações e Festivais.csv")

FONTE_APP = "Londrina Solid"
FONTE_ARQUIVO = os.path.join(ASSETS_DIR, "LondrinaSolid-Regular.ttf")
FONT_NAME_PDF = 'LondrinaSolid'


MAIN_CURSOR = get_cursor_spec("NormalSelects.cur")
POINTER_CURSOR = get_cursor_spec("PrecisionSelect.cur")
TEXT_IBEAM_CURSOR = get_cursor_spec("TextSelect.cur")

IMAGEM_FUNDO_SPLASH = os.path.join(CAMINHO_IMAGENS, "img_projeto.png")
IMAGEM_FUNDO_MAIN = os.path.join(CAMINHO_IMAGENS, "img_tela_2.png")
ICONE_FRUTA = os.path.join(CAMINHO_IMAGENS, "fruta_icone.png")

MUSICA_TEMA_SPLASH = os.path.join(ASSETS_DIR, "01. Stardew Valley Overture (mp3cut.net).mp3")
MUSICA_TEMA_SISTEMA = os.path.join(ASSETS_DIR, "11. Distant Banjo (mp3cut.net).mp3")
SOM_HOVER = os.path.join(ASSETS_DIR, "Voicy_List selection.mp3")

ESTACOES = ["Primavera", "Verão", "Outono", "Inverno"]
DIAS_POR_ESTACAO = 28
DIAS_SEMANA = ["S", "T", "Q", "Q", "S", "S", "D"]

COR_TRANSPARENTE = "#abcdef"
COR_FUNDO_CAMPO = '#f3b874'
COR_TEXTO_CAMPO_INATIVO = '#be8053'
COR_TEXTO_CAMPO_ATIVO = 'black'
COR_FUNDO_SETA_COMBO = '#f3b874'
COR_SETA_COMBO = 'black'
COR_SETA_COMBO_HOVER = 'white'
COR_FUNDO_SETA_COMBO_HOVER = '#f3b874'
COR_COMBO_SELECAO_BG = '#be8053'

COR_SCROLL_TROUGH = '#f3b874'
COR_SCROLL_THUMB = '#be8053'
COR_SCROLL_THUMB_ACTIVE = '#8a5737'
COR_SCROLL_BORDER = '#6B3710'
COR_SCROLL_ARROW = '#6B3710'

COR_CAL_FUNDO_POPUP = "#f3b874"
COR_CAL_BORDA_POPUP = "#6B3710"
COR_CAL_CABECALHO_BG = "#be8053"
COR_CAL_CABECALHO_FG = "#fdf5e6"
COR_CAL_DIA_BG = "#fdf5e6"
COR_CAL_DIA_HOVER = "#f0e6d2"
COR_CAL_DIA_FG = "#6B3710"
COR_CAL_INTERVALO_INICIO_FIM = "#4a934a"
COR_CAL_INTERVALO_MEIO = "#a9e3b3"

COR_PDF_TITULO = "#6B3710"
COR_PDF_SUBTITULO = "#8a5737"
COR_PDF_TEXTO = "#222222"