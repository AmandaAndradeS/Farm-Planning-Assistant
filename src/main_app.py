import os
import platform
import tkinter as tk
from tkinter import ttk, font as tkFont, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance
import random
import sys
import time
import traceback

try:
    import pygame
except ImportError:
    print("⚠️ Biblioteca Pygame não encontrada. Instale com 'pip install pygame'")
    pygame = None 

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ Biblioteca ReportLab não encontrada. A exportação de PDF será desativada.")

from config import *

from utils import (
    _hex_to_rgb, _rgb_to_hex, _interpolate_color, animate_hover_color,
    arredondar_cantos, criar_imagem_gradiente, animate_hover_bg
)
from calendario import abrir_calendario_popup, TKCALENDAR_AVAILABLE
from tratamento_dados import tratar_e_processar_dados
from logica import carregar_cultivos, carregar_eventos, get_preco_semente_map


def _carregar_lista_personagens(caminho):
    if not os.path.isdir(caminho):
        print(f"⚠️ Diretório de personagens não encontrado: {caminho}")
        return []
    try:
        return [
            os.path.join(caminho, arquivo)
            for arquivo in os.listdir(caminho)
            if arquivo.lower().endswith((".png", ".jpg", ".jpeg"))
        ]
    except Exception as e:
        print(f"⚠️ Erro ao listar imagens de personagens: {e}")
        return []

LISTA_IMAGENS_PERSONAGENS = _carregar_lista_personagens(CAMINHO_IMAGENS_PERSONAGENS)

APP_TITLE = "Farm Planning Assistant"
BOTAO_TAMANHO_SPLASH = (130, 42)
EFEITO_SOM_HOVER = None


def carregar_fonte_sistema(caminho):
    if not os.path.exists(caminho):
        print(f"⚠️ Fonte não encontrada: {caminho}")
        return False
    try:
        if platform.system() == "Windows":
            import ctypes
            if ctypes.windll.gdi32.AddFontResourceW(caminho) > 0:
                print(f"Fonte carregada (Windows): {caminho}")
                return True
        else:
            print("🔹 Carregamento de fonte customizada para sistemas não-Windows implementado no PIL.")
            return True
    except Exception as e:
        print(f"Erro ao carregar fonte: {e}")
    return False

def inicializar_audio():
    global EFEITO_SOM_HOVER, pygame
    if not pygame:
        print("❌ Pygame não está disponível. Áudio desativado.")
        return False
    try:
        pygame.mixer.init()
        print("✅ Pygame Mixer inicializado.")
        if os.path.exists(SOM_HOVER):
            EFEITO_SOM_HOVER = pygame.mixer.Sound(SOM_HOVER)
            print("✅ Efeito sonoro de hover carregado.")
        else:
            print(f"⚠️ Arquivo de efeito sonoro não encontrado: {SOM_HOVER}")
        return True
    except pygame.error as e:
        print(f"❌ Erro ao inicializar o Pygame Mixer: {e}")
        return False

def tocar_musica(caminho_musica, volume=0.5, loops=-1):
    if pygame and pygame.mixer.get_init():
        if os.path.exists(caminho_musica):
            try:
                pygame.mixer.music.load(caminho_musica)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(loops)
                print(f"🎵 Tocando música: {caminho_musica}")
            except pygame.error as e:
                print(f"❌ Erro ao carregar ou tocar a música: {e}")
        else:
            print(f"⚠️ Arquivo de música não encontrado: {caminho_musica}")

def parar_musica():
    if pygame and pygame.mixer.get_init():
        pygame.mixer.music.stop()
        print("🛑 Música parada.")

def tocar_efeito_hover(event=None, volume=0.6):
    if EFEITO_SOM_HOVER:
        try:
            EFEITO_SOM_HOVER.set_volume(volume)
            EFEITO_SOM_HOVER.play()
        except pygame.error as e:
            print(f"❌ Erro ao tocar o efeito sonoro: {e}")
            pass

def adicionar_som_hover(widget):
    if EFEITO_SOM_HOVER:
        widget.bind("<Enter>", tocar_efeito_hover, add=True)

if MAIN_CURSOR == "arrow":
    print(f"AVISO: '{os.path.basename(CAMINHO_CURSOR_MAIN_CUR)}' não encontrado. Usando 'arrow'.")
if POINTER_CURSOR == "hand2":
    print(f"AVISO: '{os.path.basename(CAMINHO_CURSOR_POINTER_CUR)}' não encontrado. Usando 'hand2'.")
if TEXT_IBEAM_CURSOR == "xterm":
    print(f"AVISO: '{os.path.basename(CAMINHO_CURSOR_IBEAM_CUR)}' não encontrado. Usando 'xterm'.")
    
if REPORTLAB_AVAILABLE:
    try:
        if os.path.exists(FONTE_ARQUIVO):
            pdfmetrics.registerFont(TTFont(FONT_NAME_PDF, FONTE_ARQUIVO))
            print(f"✅ Fonte '{FONT_NAME_PDF}' registrada com sucesso no ReportLab.")
        else:
            raise FileNotFoundError("Arquivo da fonte não encontrado.")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível registrar a fonte '{FONT_NAME_PDF}' para o PDF. Usando 'Helvetica'. Erro: {e}")
        FONT_NAME_PDF = 'Helvetica'


class SplashScreen(tk.Frame):
    def __init__(self, master, on_start_callback, on_quit_callback):
        super().__init__(master, bg=COR_TRANSPARENTE)
        self.master = master
        self.on_start_callback = on_start_callback
        self.on_quit_callback = on_quit_callback
        
        self._x = 0
        self._y = 0
        
        try:
            imagem_pil = arredondar_cantos(Image.open(IMAGEM_FUNDO_SPLASH).convert("RGBA"), 24)
            self.imagem_tk = ImageTk.PhotoImage(imagem_pil)
            self.width = self.imagem_tk.width()
            self.height = self.imagem_tk.height()
        except FileNotFoundError:
            print(f"❌ Imagem não encontrada: {IMAGEM_FUNDO_SPLASH}")
            self.master.destroy()
            return
            
        self.configurar_janela()

        self.bg_label = tk.Label(self, image=self.imagem_tk, bg=COR_TRANSPARENTE)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.permitir_mover_janela(self.bg_label)

        imagem_botao_tk = self.criar_imagem_botao()
        self.imagem_botao_tk = imagem_botao_tk

        self.botao_iniciar = self.criar_botao("Carregando...", self.iniciar_app, self.imagem_botao_tk, (136, 172))
        self.criar_botao("Sair", self.on_quit_callback, self.imagem_botao_tk, (136, 266))
        
        self.botao_iniciar.config(state="disabled", fg="#AAA")

        tocar_musica(MUSICA_TEMA_SPLASH, volume=0.5)

    def configurar_janela(self):
        tela_w, tela_h = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        pos_x, pos_y = (tela_w - self.width) // 2, (tela_h - self.height) // 2

        self.master.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")
        self.master.overrideredirect(True)
        self.master.attributes("-topmost", True)
        self.master.attributes("-transparentcolor", COR_TRANSPARENTE)
        self.master.config(bg=COR_TRANSPARENTE, cursor=MAIN_CURSOR)
        self.master.resizable(False, False)

    def permitir_mover_janela(self, widget):
        def iniciar_mov(e):
            self._x, self._y = e.x, e.y
        def mover(e):
            self.master.geometry(f"+{self.master.winfo_pointerx() - self._x}+{self.master.winfo_pointery() - self._y}")
        widget.bind("<Button-1>", iniciar_mov)
        widget.bind("<B1-Motion>", mover)

    def criar_imagem_botao(self):
        w, h = BOTAO_TAMANHO_SPLASH
        img_grad = criar_imagem_gradiente(w, h, "#f3b874", "#be8053")
        return ImageTk.PhotoImage(img_grad)

    def criar_botao(self, texto, comando, imagem_tk, pos):
        botao = tk.Label(
            self, text=texto, font=(FONTE_APP, 14),
            image=imagem_tk, compound="center", fg="black",
            bg=COR_TRANSPARENTE,
            borderwidth=0, 
            cursor=POINTER_CURSOR
        )
        botao.image = imagem_tk

        def on_release(event):
            if botao['state'] == 'normal':
                x, y = event.x_root, event.y_root
                widget_atual = event.widget.winfo_containing(x, y)
                if widget_atual == botao:
                    comando()
        
        def on_enter(e):
            if botao['state'] == 'normal':
                animate_hover_color(e.widget, "#000000", "#FFFFFF", 150)
                tocar_efeito_hover(volume=0.6)
        
        def on_leave(e):
             if botao['state'] == 'normal':
                animate_hover_color(e.widget, "#FFFFFF", "#000000", 150)

        botao.bind("<Enter>", on_enter)
        botao.bind("<Leave>", on_leave)
        botao.bind("<ButtonRelease-1>", on_release)
        botao.place(x=pos[0], y=pos[1], width=BOTAO_TAMANHO_SPLASH[0], height=BOTAO_TAMANHO_SPLASH[1])
        adicionar_som_hover(botao)
        return botao
        
    def habilitar_inicio(self):
        self.botao_iniciar.config(text="Iniciar", state="normal", fg="black")

    def iniciar_app(self):
        parar_musica()
        print("✅ Iniciando o aplicativo principal...")
        self.on_start_callback()


class FarmApp(tk.Frame):
    def __init__(self, master, df_cultivos, df_eventos, preco_semente_map):
        super().__init__(master, bg=COR_TRANSPARENTE)
        self.master = master

        self.df_cultivos_cache = df_cultivos
        self.df_eventos_cache = df_eventos
        self.preco_semente_map = preco_semente_map

        self.data_selecionada = "Nenhuma data selecionada"
        self._x = 0
        self._y = 0
        self.mouse_over_fechar = False

        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(family=FONTE_APP, size=12)
        self.option_add("*Font", default_font)
        self.option_add('*TCombobox*Listbox.selectBackground', COR_COMBO_SELECAO_BG)

        self.option_add('*TCombobox*Listbox.background', COR_FUNDO_CAMPO)
        self.option_add('*TCombobox*Listbox.foreground', COR_TEXTO_CAMPO_ATIVO)
        self.option_add('*TCombobox*Listbox.selectForeground', COR_CAL_CABECALHO_FG)

        if TEXT_IBEAM_CURSOR != "xterm":
            self.option_add("*Entry.cursor", TEXT_IBEAM_CURSOR)
            self.option_add("*Text.cursor", TEXT_IBEAM_CURSOR)

        try:
            imagem_pil_original = Image.open(IMAGEM_FUNDO_MAIN).convert("RGBA")

            try:
                if LISTA_IMAGENS_PERSONAGENS:
                    imagem_escolhida = random.choice(LISTA_IMAGENS_PERSONAGENS)
                    imagem_personagem_pil = Image.open(imagem_escolhida).convert("RGBA")
                    imagem_personagem_pil = imagem_personagem_pil.resize((125, 125), Image.Resampling.LANCZOS)
                    imagem_pil_original.paste(imagem_personagem_pil, (8, 455), imagem_personagem_pil)
                else:
                    print("⚠️ Nenhuma imagem encontrada em 'images personagens'.")

            except Exception as e:
                print(f"⚠️ Erro ao carregar personagem: {e}")

            imagem_pil_arredondada = arredondar_cantos(imagem_pil_original, 24)
            self.imagem_base_pil = imagem_pil_arredondada.copy()
            self.imagem_tk = ImageTk.PhotoImage(self.imagem_base_pil)

            self.width = self.imagem_tk.width()
            self.height = self.imagem_tk.height()

        except FileNotFoundError:
            self.mostrar_popup_customizado(self, "Erro", f"Imagem base não encontrada em {IMAGEM_FUNDO_MAIN}.", tipo='erro')
            self.master.destroy()
            sys.exit()

        try:
            self.fonte_para_desenho = ImageFont.truetype(FONTE_ARQUIVO, 14)
        except IOError:
            self.fonte_para_desenho = ImageFont.load_default()

        self.icone_disponivel = False
        try:
            icone_fruta_pil = Image.open(ICONE_FRUTA).convert("RGBA")
            icone_fruta_pil = icone_fruta_pil.resize((32, 32), Image.Resampling.LANCZOS)
            enhancer = ImageEnhance.Brightness(icone_fruta_pil)
            icone_fruta_pressed_pil = enhancer.enhance(0.7)
            self.icone_fruta_tk = ImageTk.PhotoImage(icone_fruta_pil)
            self.icone_fruta_pressed_tk = ImageTk.PhotoImage(icone_fruta_pressed_pil)
            self.icone_disponivel = True
        except FileNotFoundError:
            print(f"Erro de Imagem: O arquivo 'fruta_icone.png' não foi encontrado em {CAMINHO_IMAGENS}.")

        style = ttk.Style(self)
        style.theme_use('clam')

        style.configure('TCombobox',
                        fieldbackground=COR_FUNDO_CAMPO, background=COR_FUNDO_SETA_COMBO,
                        foreground=COR_TEXTO_CAMPO_ATIVO, arrowcolor=COR_SETA_COMBO, borderwidth=0,
                        highlightthickness=0, padding=0, selectbackground=COR_FUNDO_CAMPO,
                        selectforeground=COR_TEXTO_CAMPO_ATIVO, justify='center')
        style.configure('TCombobox.field', background=COR_FUNDO_CAMPO, borderwidth=0,
                        relief='flat', highlightthickness=0)
        style.map('TCombobox',
                  fieldbackground=[('readonly', COR_FUNDO_CAMPO)],
                  foreground=[('readonly', COR_TEXTO_CAMPO_ATIVO)],
                  background=[('readonly', COR_FUNDO_SETA_COMBO), ('active', COR_FUNDO_SETA_COMBO_HOVER)],
                  arrowcolor=[('readonly', COR_SETA_COMBO), ('active', COR_SETA_COMBO_HOVER)],
                  selectbackground=[('readonly', COR_FUNDO_CAMPO), ('focus', COR_FUNDO_CAMPO)],
                  selectforeground=[('readonly', COR_TEXTO_CAMPO_ATIVO), ('focus', COR_TEXTO_CAMPO_ATIVO)])
        style.map('TCombobox.field', background=[('readonly', COR_FUNDO_CAMPO)])
        style.layout('TCombobox', [
            ('Combobox.field', {'sticky': 'nswe', 'children': [
                ('Combobox.padding', {'expand': '1', 'sticky': 'nswe', 'children': [
                    ('Combobox.textarea', {'sticky': 'nswe'})
                ]})
            ]}),
            ('Combobox.arrow', {'sticky': 'ns', 'side': 'right'})
        ])

        style.configure('Custom.Vertical.TScrollbar',
                        gripcount=0, background=COR_SCROLL_THUMB, darkcolor=COR_SCROLL_THUMB,
                        lightcolor=COR_SCROLL_THUMB, troughcolor=COR_SCROLL_TROUGH,
                        bordercolor=COR_SCROLL_BORDER, arrowcolor=COR_SCROLL_ARROW,
                        relief='flat', arrowsize=14)
        style.map('Custom.Vertical.TScrollbar',
                  background=[('active', COR_SCROLL_THUMB_ACTIVE), ('!active', COR_SCROLL_THUMB)],
                  arrowcolor=[('pressed', 'white'), ('!pressed', COR_SCROLL_ARROW)])

        self.background_label = tk.Label(self, image=self.imagem_tk, bg=COR_TRANSPARENTE, borderwidth=0)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.background_label.image = self.imagem_tk

        frame_plano = tk.Frame(self, bg=COR_FUNDO_CAMPO, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(frame_plano, orient="vertical",
                                       style='Custom.Vertical.TScrollbar',
                                       cursor=POINTER_CURSOR)
        self.texto_plano = tk.Text(frame_plano, wrap="word", bg=COR_FUNDO_CAMPO, fg=COR_TEXTO_CAMPO_ATIVO,
                                   font=(FONTE_APP, 12), borderwidth=0,
                                   highlightthickness=0, padx=5, pady=5,
                                   yscrollcommand=self.scrollbar.set)
        self.texto_plano.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.texto_plano.yview)
        frame_plano.place(x=378, y=85, width=400, height=450)
        self.texto_plano.config(state="disabled")

        self.vcmd = (self.register(self.validate_input), '%P')

        self.combobox = ttk.Combobox(self,
                                     values=["Aspersor - Nível 2", "Área Plantável"],
                                     state="readonly", cursor=POINTER_CURSOR,
                                     justify='center') 
        self.combobox.set("Selecione uma opção")
        self.combobox.place(x=28, y=122, width=182, height=33)
        self.option_add('*TCombobox*Listbox.cursor', POINTER_CURSOR)
        adicionar_som_hover(self.combobox)

        self.entrada_quantidade = tk.Entry(self, borderwidth=0, bg=COR_FUNDO_CAMPO, fg=COR_TEXTO_CAMPO_INATIVO, justify='center')
        self.entrada_quantidade.insert(0, "Digite a quantidade")
        self.entrada_quantidade.bind('<FocusIn>', self.on_focus_in)
        self.entrada_quantidade.bind('<FocusOut>', self.on_focus_out)
        self.entrada_quantidade.place(x=22, y=174, width=182, height=37)

        self.botao_calendario = tk.Label(self, text="📅", font=("Arial", 16), bg=COR_FUNDO_CAMPO, cursor=POINTER_CURSOR)
        self.botao_calendario.place(x=250, y=123)
        self.botao_calendario.bind("<Button-1>", lambda e: self.call_abrir_calendario())
        adicionar_som_hover(self.botao_calendario)

        largura_botao, altura_botao = 80, 32
        padding_botoes = 37
        img_grad = criar_imagem_gradiente(largura_botao, altura_botao, "#f3b8874", "#be8053")
        self.img_grad_tk = ImageTk.PhotoImage(img_grad) 

        pos_x_gerar = 20
        pos_y_linha1 = 235
        self.botao_GerarPlano = tk.Label(self, text="Gerar Plano", font=(FONTE_APP, 12),
                                    image=self.img_grad_tk, compound="center", fg="black",
                                    bg=COR_TRANSPARENTE, borderwidth=0, cursor=POINTER_CURSOR)
        self.botao_GerarPlano.image = self.img_grad_tk
        self.botao_GerarPlano.place(x=pos_x_gerar, y=pos_y_linha1, width=largura_botao, height=altura_botao)
        self.botao_GerarPlano.bind("<ButtonRelease-1>", self.on_release_gerar)
        self.botao_GerarPlano.bind("<Enter>", lambda e: animate_hover_color(e.widget, "#000000", "#FFFFFF", 150))
        self.botao_GerarPlano.bind("<Leave>", lambda e: animate_hover_color(e.widget, "#FFFFFF", "#000000", 150))
        adicionar_som_hover(self.botao_GerarPlano)

        pos_x_resetar = pos_x_gerar + largura_botao + padding_botoes
        self.botao_Resetar = tk.Label(self, text="Resetar", font=(FONTE_APP, 12),
                                 image=self.img_grad_tk, compound="center", fg="black",
                                 bg=COR_TRANSPARENTE, borderwidth=0, cursor=POINTER_CURSOR)
        self.botao_Resetar.image = self.img_grad_tk
        self.botao_Resetar.place(x=pos_x_resetar, y=pos_y_linha1, width=largura_botao, height=altura_botao)
        self.botao_Resetar.bind("<ButtonRelease-1>", self.on_release_reset)
        self.botao_Resetar.bind("<Enter>", lambda e: animate_hover_color(e.widget, "#000000", "#FFFFFF", 150))
        self.botao_Resetar.bind("<Leave>", lambda e: animate_hover_color(e.widget, "#FFFFFF", "#000000", 150))
        adicionar_som_hover(self.botao_Resetar)

        pos_y_linha2 = pos_y_linha1 + altura_botao + 24
        pos_x_download = (pos_x_gerar + pos_x_resetar) // 2
        self.botao_Download = tk.Label(self, text="Download", font=(FONTE_APP, 12),
                                  image=self.img_grad_tk, compound="center", fg="black",
                                  bg=COR_TRANSPARENTE, borderwidth=0, cursor=POINTER_CURSOR)
        self.botao_Download.image = self.img_grad_tk
        self.botao_Download.place(x=pos_x_download, y=pos_y_linha2, width=largura_botao, height=altura_botao)
        self.botao_Download.bind("<ButtonRelease-1>", self.on_release_download)
        self.botao_Download.bind("<Enter>", lambda e: animate_hover_color(e.widget, "#000000", "#FFFFFF", 150))
        self.botao_Download.bind("<Leave>", lambda e: animate_hover_color(e.widget, "#FFFFFF", "#000000", 150))
        adicionar_som_hover(self.botao_Download)

        if self.icone_disponivel:
            self.botao_ajuda = tk.Label(self, image=self.icone_fruta_tk, borderwidth=0, cursor=POINTER_CURSOR)
            self.botao_ajuda.config(bg="#e4a96a")
            self.botao_ajuda.image = self.icone_fruta_tk
            self.botao_ajuda.place(x=248, y=177)
            self.botao_ajuda.bind("<ButtonPress-1>", self.on_press_ajuda)
            self.botao_ajuda.bind("<ButtonRelease-1>", self.on_release_ajuda)
            adicionar_som_hover(self.botao_ajuda)

        self.background_label.bind("<Button-1>", self.verificar_clique)
        self.background_label.bind("<B1-Motion>", self.mover_janela)
        self.background_label.bind("<Motion>", self.gerenciar_cursor)
        
        tocar_musica(MUSICA_TEMA_SISTEMA, volume=0.1)

    def fechar_janela(self, event=None):
        parar_musica()
        self.master.destroy()

    def iniciar_movimento(self, event):
        self._x = event.x
        self._y = event.y

    def mover_janela(self, event):
        deltax = event.x - self._x
        deltay = event.y - self._y
        x = self.master.winfo_x() + deltax
        y = self.master.winfo_y() + deltay
        self.master.geometry(f"+{x}+{y}")

        if hasattr(self, 'calendario_popup') and self.calendario_popup.winfo_exists():
            cal_x = self.master.winfo_x() + self.botao_calendario.winfo_x() - (self.calendario_popup.winfo_width() // 2) + (self.botao_calendario.winfo_width() // 2)
            cal_y = self.master.winfo_y() + self.botao_calendario.winfo_y() + self.botao_calendario.winfo_height() + 9
            self.calendario_popup.geometry(f"+{cal_x}+{cal_y}")
            
    def verificar_clique(self, event):
        self.master.focus_set()
        area_fechar = (self.width - 36, 6, self.width - 16, 26)
        if area_fechar[0] <= event.x <= area_fechar[2] and area_fechar[1] <= event.y <= area_fechar[3]:
            self.fechar_janela()
        else:
            if event.widget == self.background_label:
                self.iniciar_movimento(event)

    def gerenciar_cursor(self, event):
        area_fechar = (self.width - 36, 6, self.width - 16, 26)
        is_over = area_fechar[0] <= event.x <= area_fechar[2] and area_fechar[1] <= event.y <= area_fechar[3]

        if is_over and not self.mouse_over_fechar:
            self.background_label.config(cursor=POINTER_CURSOR)
            tocar_efeito_hover()
            self.mouse_over_fechar = True
        elif not is_over and self.mouse_over_fechar:
            self.background_label.config(cursor="")
            self.mouse_over_fechar = False

    def on_focus_in(self, event):
        if self.entrada_quantidade.get() == "Digite a quantidade":
            self.entrada_quantidade.delete(0, "end")
            self.entrada_quantidade.config(fg=COR_TEXTO_CAMPO_ATIVO)
            self.entrada_quantidade.config(validate='key', validatecommand=self.vcmd)

    def on_focus_out(self, event):
        if not self.entrada_quantidade.get():
            self.entrada_quantidade.config(validate='none')
            self.entrada_quantidade.config(fg=COR_TEXTO_CAMPO_INATIVO)
            self.entrada_quantidade.insert(0, "Digite a quantidade")

    def validate_input(self, P):
        if P == "": return True
        if P.isdigit() and len(P) <= 3: return True
        return False

    def call_abrir_calendario(self):
        abrir_calendario_popup(self.master, self.botao_calendario, tocar_efeito_hover)

    def on_release_gerar(self, event):
        x, y = event.x_root, event.y_root
        widget_atual = event.widget.winfo_containing(x, y)
        if widget_atual == self.botao_GerarPlano:
            self.mostrar_plano()

    def on_release_reset(self, event):
        x, y = event.x_root, event.y_root
        widget_atual = event.widget.winfo_containing(x, y)
        if widget_atual == self.botao_Resetar:
            self.resetar_plano()
    
    def on_press_ajuda(self, event):
        try:
            self.botao_ajuda.config(image=self.icone_fruta_pressed_tk)
        except AttributeError:
            pass

    def on_release_ajuda(self, event):
        try:
            self.botao_ajuda.config(image=self.icone_fruta_tk)
            self.mostrar_ajuda_popup()
        except AttributeError:
            pass

    def on_release_download(self, event):
        x, y = event.x_root, event.y_root
        widget_atual = event.widget.winfo_containing(x, y)
        if widget_atual == self.botao_Download:
            self.salvar_como_pdf()

    def criar_dados_entrada(self, opcao, quantidade, data):
        return {
            "opcao_estrategia": opcao,
            "quantidade": quantidade,
            "data_inicio": data
        }

    def resetar_plano(self, event=None):
        try:
            self.texto_plano.config(state="normal")
            self.texto_plano.delete(1.0, "end")
            self.texto_plano.config(state="disabled")

            self.scrollbar.pack_forget()
            self.texto_plano.pack_forget()
            self.texto_plano.pack(side="left", fill="both", expand=True)

            self.combobox.set("Selecione uma opção")

            self.entrada_quantidade.config(validate='none')
            self.entrada_quantidade.delete(0, "end")
            self.entrada_quantidade.insert(0, "Digite a quantidade")
            self.entrada_quantidade.config(fg=COR_TEXTO_CAMPO_INATIVO)
            self.master.focus_set()

            self.data_selecionada = "Nenhuma data selecionada"
            if hasattr(self.master, "intervalo_selecionado"):
                self.master.intervalo_selecionado = {"inicio": None, "fim": None}

            if hasattr(self, 'calendario_popup') and self.calendario_popup.winfo_exists():
                self.calendario_popup.destroy()
            if hasattr(self.master, 'calendario_popup') and self.master.calendario_popup.winfo_exists():
                self.master.calendario_popup.destroy()

        except Exception as e:
            print(f"Erro ao resetar: {e}")

    def mostrar_plano(self):
        opcao = self.combobox.get()
        quantidade = self.entrada_quantidade.get()
        data = getattr(self.master, 'data_selecionada', 'Nenhuma data selecionada')

        if opcao == "Selecione uma opção":
            self.mostrar_popup_customizado(self.master, "Aviso", "Por favor, selecione uma opção antes de continuar.", tipo='aviso')
            return
        if not quantidade or quantidade.strip() == "" or quantidade == "Digite a quantidade":
            self.mostrar_popup_customizado(self.master, "Aviso", "Por favor, digite uma quantidade válida.", tipo='aviso')
            return
        try:
            quantidade_valor = int(quantidade)
            if quantidade_valor <= 0:
                self.mostrar_popup_customizado(self.master, "Aviso", "A quantidade deve ser um número positivo.", tipo='aviso')
                return
        except ValueError:
            self.mostrar_popup_customizado(self.master, "Aviso", "A quantidade deve ser um número inteiro.", tipo='aviso')
            return
        if not data or "->" not in data:
            self.mostrar_popup_customizado(self.master, "Aviso", "Por favor, selecione um INTERVALO completo no calendário (clique em 2 dias).", tipo='aviso')
            return

        dados_entrada = self.criar_dados_entrada(opcao, quantidade_valor, data)
        texto_final = ""

        try:
            texto_final = tratar_e_processar_dados(
                dados_entrada, 
                self.df_cultivos_cache, 
                self.df_eventos_cache, 
                self.preco_semente_map
            )
        except Exception as e:
            print("--- ERRO NO PROCESSAMENTO DE DADOS/NARRATIVA ---")
            traceback.print_exc()
            print("-------------------------------------------------")
            self.mostrar_popup_customizado(self.master, "Erro de Processamento", f"Ocorreu um erro interno na lógica: {e}. Verifique o terminal para detalhes.", tipo='erro')
            texto_final = f"📋 Plano de Colheita\nOpção: {opcao}\nQuantidade: {quantidade}\nData: {data}\n\n[ERRO: Falha ao processar dados.]"

        if not isinstance(texto_final, str):
            texto_final = "ERRO CRÍTICO: O resultado final não foi formatado como texto."
            self.mostrar_popup_customizado(self.master, "Erro Crítico", "Falha interna ao gerar o texto do plano.", tipo='erro')

        try:
            img_limpa_tk = ImageTk.PhotoImage(self.imagem_base_pil)
            self.background_label.config(image=img_limpa_tk)
            self.background_label.image = img_limpa_tk

            self.texto_plano.config(state="normal")
            self.texto_plano.delete(1.0, "end")
            self.texto_plano.insert("end", texto_final)
            self.update_idletasks()

            top, bottom = self.texto_plano.yview()
            if bottom < 1.0:
                self.texto_plano.pack_forget()
                self.scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
                self.texto_plano.pack(side="left", fill="both", expand=True)
            else:
                self.scrollbar.pack_forget()
                self.texto_plano.pack_forget()
                self.texto_plano.pack(side="left", fill="both", expand=True)
            self.texto_plano.config(state="disabled")
        except Exception as e:
            self.mostrar_popup_customizado(self.master, "Erro de UI", f"Não foi possível exibir o plano: {e}", tipo='erro')

    def mostrar_ajuda_popup(self):
        if hasattr(self, 'ajuda_popup') and self.ajuda_popup.winfo_exists():
            self.ajuda_popup.destroy()
            return

        ajuda_popup = tk.Toplevel(self.master)
        self.ajuda_popup = ajuda_popup
        ajuda_popup.overrideredirect(True)
        ajuda_popup.attributes('-topmost', True)
        ajuda_popup.config(bg=COR_CAL_FUNDO_POPUP, highlightbackground=COR_CAL_BORDA_POPUP, highlightcolor=COR_CAL_BORDA_POPUP, highlightthickness=3)

        texto_ajuda = """
Olá! Seja bem-vindo(a) ao
✨🌱 Farm Planning Assistant 🌱✨
========================================
    Pronto(a) para a colheita perfeita?
    É simples assim:
1. Selecione sua opção de plantio (área/aspersor) e a quantidade.
2. Clique em '📅' para definir o período no calendário.
3. Aperte 'Gerar' e veja a mágica acontecer!
4. Quer guardar o plano? Use 'Download'.
5. Para recomeçar, clique em 'Resetar'.
========================================
🎉 Divirta-se planejando! 🌿 Boa sorte e ótimas plantações! 💖
"""
        label_ajuda = tk.Label(ajuda_popup, text=texto_ajuda, font=(FONTE_APP, 11),
                               bg=COR_CAL_FUNDO_POPUP, justify=tk.LEFT, wraplength=280, padx=10, pady=10)
        label_ajuda.pack()

        self.update_idletasks()
        ajuda_popup.update_idletasks()
        largura_popup = ajuda_popup.winfo_reqwidth()
        pos_x = self.master.winfo_x() + self.botao_ajuda.winfo_x() + (self.botao_ajuda.winfo_width() // 2) - (largura_popup // 2)
        pos_y = self.master.winfo_y() + self.botao_ajuda.winfo_y() + self.botao_ajuda.winfo_height() + 8
        ajuda_popup.geometry(f"+{pos_x}+{pos_y}")
        ajuda_popup.bind("<FocusOut>", lambda e: ajuda_popup.destroy())
        ajuda_popup.focus_set()

    def mostrar_popup_customizado(self, janela_pai, titulo, mensagem, tipo='aviso'):
        popup = tk.Toplevel(janela_pai)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        popup.config(bg=COR_CAL_FUNDO_POPUP, highlightbackground=COR_CAL_BORDA_POPUP,
                     highlightcolor=COR_CAL_BORDA_POPUP, highlightthickness=3)
        if tipo == 'aviso': icone = "⚠️"
        elif tipo == 'erro': icone = "❌"
        else: icone = "✅"
        frame_titulo = tk.Frame(popup, bg=COR_CAL_CABECALHO_BG)
        label_titulo = tk.Label(frame_titulo, text=f" {icone} {titulo} ", font=(FONTE_APP, 14, "bold"),
                                bg=COR_CAL_CABECALHO_BG, fg=COR_CAL_CABECALHO_FG)
        label_titulo.pack(pady=4)
        frame_titulo.pack(fill="x", padx=0, pady=0)
        label_msg = tk.Label(popup, text=mensagem, font=(FONTE_APP, 12),
                             bg=COR_CAL_FUNDO_POPUP, fg=COR_CAL_BORDA_POPUP,
                             wraplength=300, justify=tk.LEFT, padx=20, pady=15)
        label_msg.pack(fill="x")
        btn_ok = tk.Button(popup, text="OK", command=popup.destroy, bg=COR_CAL_CABECALHO_BG,
                         fg=COR_CAL_CABECALHO_FG, activebackground="#f3a166",
                         activeforeground=COR_CAL_CABECALHO_FG, relief="flat",
                         font=(FONTE_APP, 11, "bold"), width=8, cursor=POINTER_CURSOR)
        btn_ok.pack(pady=(5, 15))
        janela_pai.update_idletasks()
        popup.update_idletasks()
        popup_width, popup_height = popup.winfo_reqwidth(), popup.winfo_reqheight()
        pai_x, pai_y = janela_pai.winfo_x(), janela_pai.winfo_y()
        pai_width, pai_height = janela_pai.winfo_width(), janela_pai.winfo_height()
        pos_x = pai_x + (pai_width // 2) - (popup_width // 2)
        pos_y = pai_y + (pai_height // 2) - (popup_height // 2)
        popup.geometry(f"+{pos_x}+{pos_y}")
        popup.grab_set()
        popup.focus_set()
        janela_pai.wait_window(popup)

    def _add_footer_pdf(self, canvas, doc):
        canvas.saveState()
        try:
            canvas.setFont(FONT_NAME_PDF, 9)
        except:
            canvas.setFont('Helvetica', 9)
        page_text = f"Página {canvas.getPageNumber()}"
        canvas.drawRightString(doc.width + doc.leftMargin - (0.5*inch),
                               doc.bottomMargin / 2, page_text)
        canvas.restoreState()

    def salvar_como_pdf(self):
        if not REPORTLAB_AVAILABLE:
            self.mostrar_popup_customizado(self.master, "Erro de Dependência",
                                      "A biblioteca 'reportlab' é necessária para exportar PDF.\n\n"
                                      "Feche o app, instale-a com:\n"
                                      "py -m pip install reportlab\n\n"
                                      "E tente novamente.",
                                      tipo='erro')
            return

        plano_texto = self.texto_plano.get(1.0, "end").strip()
        if not plano_texto:
            self.mostrar_popup_customizado(self.master, "Aviso", "Não há plano gerado para salvar.", tipo='aviso')
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            title="Salvar Plano de Colheita como PDF",
            initialfile="Plano_de_Colheita.pdf"
        )
        if not filepath:
            return

        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4,
                                    rightMargin=0.75*inch, leftMargin=0.75*inch,
                                    topMargin=0.75*inch, bottomMargin=0.75*inch)
            story = []
            
            style_title = ParagraphStyle(name='TitleStyle', fontName=FONT_NAME_PDF, fontSize=20,
                                         textColor=HexColor(COR_PDF_TITULO), alignment=1, spaceAfter=12)
            style_heading = ParagraphStyle(name='HeadingStyle', fontName=FONT_NAME_PDF, fontSize=14,
                                           textColor=HexColor(COR_PDF_SUBTITULO), spaceBefore=10, spaceAfter=6, alignment=0)
            style_body = ParagraphStyle(name='BodyStyle', fontName=FONT_NAME_PDF, fontSize=10,
                                        textColor=HexColor(COR_PDF_TEXTO), leading=14, alignment=0)
            style_body_indent = ParagraphStyle(name='BodyIndentStyle', parent=style_body,
                                               leftIndent=0.25 * inch, firstLineIndent=0)

            story.append(Paragraph("Plano de Colheita", style_title))
            linhas = plano_texto.split('\n')
            for linha in linhas:
                linha_strip = linha.strip()
                if not linha_strip:
                    story.append(Spacer(1, 0.1 * inch))
                    continue
                if linha_strip.startswith('---'):
                    texto_limpo = linha_strip.replace('---', '').strip()
                    story.append(Paragraph(texto_limpo, style_heading))
                elif (linha_strip.startswith('▪️') or linha_strip.startswith('>') or
                      linha_strip.startswith('(') or linha_strip.startswith('✅') or
                      linha_strip.startswith('[AVISO:')):
                    story.append(Paragraph(linha, style_body_indent))
                else:
                    story.append(Paragraph(linha, style_body))
            doc.build(story, onFirstPage=self._add_footer_pdf, onLaterPages=self._add_footer_pdf)
            self.mostrar_popup_customizado(self.master, "Sucesso", f"Plano customizado salvo com sucesso em:\n{filepath}", tipo='info')
        except PermissionError:
              self.mostrar_popup_customizado(self.master, "Erro de Permissão",
                                        "Não foi possível salvar o arquivo.\n\n"
                                        "Verifique se você tem permissão para salvar neste local "
                                        "ou se o arquivo já está aberto em outro programa.",
                                        tipo='erro')
        except Exception as e:
            self.mostrar_popup_customizado(self.master, "Erro ao Salvar PDF", f"Não foi possível salvar o arquivo PDF.\n\nDetalhe: {e}\n\n(Verifique se a fonte '{FONT_NAME_PDF}' está acessível)", tipo='erro')


class AppController(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title(APP_TITLE)
        self.withdraw()

        carregar_fonte_sistema(FONTE_ARQUIVO)

        fonte_padrao = tkFont.nametofont("TkDefaultFont")
        fonte_padrao.configure(family=FONTE_APP, size=12)
        self.option_add("*Font", fonte_padrao)

        if pygame:
            inicializar_audio()

        self.df_cultivos = None
        self.df_eventos = None
        self.preco_semente_map = None
        
        self.splash_frame = None
        self.main_frame = None

        self.show_splash_screen()
        
        self.after(100, self.load_data)

    def show_splash_screen(self):
        self.splash_frame = SplashScreen(
            master=self,
            on_start_callback=self.show_main_app,
            on_quit_callback=self.quit_app
        )
        self.splash_frame.configurar_janela() 
        self.splash_frame.pack(fill="both", expand=True)
        self.deiconify()

    def load_data(self):
        print("Carregando dados (Cultivos.csv)...")
        try:
            self.df_cultivos = carregar_cultivos()
            print("Carregando dados (Estações e Festivais.csv)...")
            self.df_eventos = carregar_eventos()
            
            print("Pré-calculando mapa de preços...")
            self.preco_semente_map = get_preco_semente_map(self.df_cultivos)

            print("✅ Dados carregados com sucesso em cache.")
            self.splash_frame.habilitar_inicio()
        except Exception as e:
            print(f"❌ ERRO CRÍTICO: Falha ao carregar dados em cache. {e}")
            traceback.print_exc()
            self.splash_frame.habilitar_inicio()
            self.mostrar_popup_customizado(self, "Erro de Dados", 
                f"Não foi possível carregar os arquivos CSV.\n\nVerifique se 'Cultivos.csv' e 'Estações e Festivais.csv' estão na pasta 'data'.\n\nDetalhe: {e}",
                tipo='erro')

    def show_main_app(self):
        self.splash_frame.destroy()

        if self.df_cultivos is None or self.df_eventos is None or self.preco_semente_map is None:
            self.mostrar_popup_customizado(self, "Erro", "Os dados não puderam ser carregados. Saindo.", tipo='erro')
            self.quit_app()
            return

        self.main_frame = FarmApp(
            master=self,
            df_cultivos=self.df_cultivos,
            df_eventos=self.df_eventos,
            preco_semente_map=self.preco_semente_map
        )

        w, h = self.main_frame.width, self.main_frame.height
        tela_w, tela_h = self.winfo_screenwidth(), self.winfo_screenheight()
        pos_x, pos_y = (tela_w - w) // 2, (tela_h - h) // 2
        self.geometry(f"{w}x{h}+{pos_x}+{pos_y}")

        self.main_frame.pack(fill="both", expand=True)

    def quit_app(self):
        parar_musica()
        if pygame:
            pygame.mixer.quit()
        self.destroy()

    def mostrar_popup_customizado(self, janela_pai, titulo, mensagem, tipo='aviso'):
        popup = tk.Toplevel(janela_pai)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        popup.config(bg=COR_CAL_FUNDO_POPUP, highlightbackground=COR_CAL_BORDA_POPUP,
                     highlightcolor=COR_CAL_BORDA_POPUP, highlightthickness=3)
        if tipo == 'aviso': icone = "⚠️"
        elif tipo == 'erro': icone = "❌"
        else: icone = "✅"
        frame_titulo = tk.Frame(popup, bg=COR_CAL_CABECALHO_BG)
        label_titulo = tk.Label(frame_titulo, text=f" {icone} {titulo} ", font=(FONTE_APP, 14, "bold"),
                                bg=COR_CAL_CABECALHO_BG, fg=COR_CAL_CABECALHO_FG)
        label_titulo.pack(pady=4)
        frame_titulo.pack(fill="x", padx=0, pady=0)
        label_msg = tk.Label(popup, text=mensagem, font=(FONTE_APP, 12),
                             bg=COR_CAL_FUNDO_POPUP, fg=COR_CAL_BORDA_POPUP,
                             wraplength=300, justify=tk.LEFT, padx=20, pady=15)
        label_msg.pack(fill="x")
        btn_ok = tk.Button(popup, text="OK", command=popup.destroy, bg=COR_CAL_CABECALHO_BG,
                         fg=COR_CAL_CABECALHO_FG, activebackground="#f3a166",
                         activeforeground=COR_CAL_CABECALHO_FG, relief="flat",
                         font=(FONTE_APP, 11, "bold"), width=8, cursor=POINTER_CURSOR)
        btn_ok.pack(pady=(5, 15))
        janela_pai.update_idletasks()
        popup.update_idletasks()
        popup_width, popup_height = popup.winfo_reqwidth(), popup.winfo_reqheight()
        pai_x, pai_y = janela_pai.winfo_x(), janela_pai.winfo_y()
        pai_width, pai_height = janela_pai.winfo_width(), janela_pai.winfo_height()
        pos_x = pai_x + (pai_width // 2) - (popup_width // 2)
        pos_y = pai_y + (pai_height // 2) - (popup_height // 2)
        popup.geometry(f"+{pos_x}+{pos_y}")
        popup.grab_set()
        popup.focus_set()
        janela_pai.wait_window(popup)


if __name__ == "__main__":
    app = AppController()
    app.mainloop()