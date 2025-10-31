import tkinter as tk
import time 
import os

from utils import _hex_to_rgb, _rgb_to_hex, _interpolate_color, animate_hover_bg
from config import (
    MAIN_CURSOR, POINTER_CURSOR, FONTE_APP,
    ESTACOES, DIAS_POR_ESTACAO, DIAS_SEMANA,
    COR_CAL_FUNDO_POPUP, COR_CAL_BORDA_POPUP, COR_CAL_CABECALHO_BG,
    COR_CAL_CABECALHO_FG, COR_CAL_DIA_BG, COR_CAL_DIA_HOVER,
    COR_CAL_DIA_FG, COR_CAL_INTERVALO_INICIO_FIM, COR_CAL_INTERVALO_MEIO
)

COR_INICIO = COR_CAL_INTERVALO_INICIO_FIM
COR_FIM = COR_CAL_INTERVALO_INICIO_FIM
COR_INTERVALO = COR_CAL_INTERVALO_MEIO
COR_FUNDO_POPUP = COR_CAL_FUNDO_POPUP
COR_BORDA_POPUP = COR_CAL_BORDA_POPUP
COR_CABECALHO = COR_CAL_CABECALHO_BG
COR_TEXTO_CABECALHO = COR_CAL_CABECALHO_FG

TKCALENDAR_AVAILABLE = True


def data_para_dia_global(data):
    if not data:
        return -1
    try:
        estacao_idx = ESTACOES.index(data["estacao"])
        return (estacao_idx * DIAS_POR_ESTACAO) + data["dia"]
    except (ValueError, AttributeError):
        try:
            estacao_idx = [e.lower() for e in ESTACOES].index(data["estacao"].lower())
            return (estacao_idx * DIAS_POR_ESTACAO) + data["dia"]
        except Exception:
            return -1

def comparar_datas(a, b):
    dia_a = data_para_dia_global(a)
    dia_b = data_para_dia_global(b)
    return dia_a - dia_b

def dentro_do_intervalo(data, inicio, fim):
    if not inicio or not fim:
        return False
        
    dia_data = data_para_dia_global(data)
    dia_inicio = data_para_dia_global(inicio)
    dia_fim = data_para_dia_global(fim)
    
    if dia_inicio > dia_fim:
        dia_inicio, dia_fim = dia_fim, dia_inicio
        
    return dia_inicio <= dia_data <= dia_fim


def abrir_calendario_popup(janela, botao_calendario, som_hover_callback=None):
    if hasattr(janela, 'calendario_popup') and janela.calendario_popup.winfo_exists():
        janela.calendario_popup.focus_set()
        return

    top = tk.Toplevel(janela)
    janela.calendario_popup = top
    top.overrideredirect(True)
    top.config(cursor=MAIN_CURSOR)
    top.attributes('-topmost', True)
    top.config(bg=COR_FUNDO_POPUP, highlightbackground=COR_BORDA_POPUP, highlightcolor=COR_BORDA_POPUP, highlightthickness=3)

    top.focus_set()

    estacao_idx = getattr(janela, "estacao_idx", 0)
    if not hasattr(janela, "intervalo_selecionado"):
        janela.intervalo_selecionado = {"inicio": None, "fim": None}
    dias_labels = {}

    def fechar_popup():
        try:
            if janela.winfo_exists():
                janela.focus_set()
            if top.winfo_exists():
                top.destroy()
        except tk.TclError:
            pass 

    top.bind("<FocusOut>", lambda e: fechar_popup())

    def atualizar_dias():
        for d, lbl in dias_labels.items():
            if hasattr(lbl, "_animation_id"):
                try:
                    lbl.after_cancel(lbl._animation_id)
                    delattr(lbl, "_animation_id")
                except (tk.TclError, AttributeError):
                    pass
            lbl.config(bg=COR_CAL_DIA_BG, fg=COR_CAL_DIA_FG)

        inicio = janela.intervalo_selecionado["inicio"]
        fim = janela.intervalo_selecionado["fim"]

        for d, lbl in dias_labels.items():
            data_atual = {"estacao": ESTACOES[estacao_idx], "dia": d}

            if inicio and fim and dentro_do_intervalo(data_atual, inicio, fim):
                lbl.config(bg=COR_INTERVALO)

            if inicio and comparar_datas(data_atual, inicio) == 0:
                lbl.config(bg=COR_INICIO, fg=COR_TEXTO_CABECALHO)
                
            if fim and comparar_datas(data_atual, fim) == 0:
                lbl.config(bg=COR_FIM, fg=COR_TEXTO_CABECALHO)

    def selecionar_dia(dia):
        data_selecionada = {"estacao": ESTACOES[estacao_idx], "dia": dia}
        
        inicio = janela.intervalo_selecionado["inicio"]
        fim = janela.intervalo_selecionado["fim"]

        if not inicio or (inicio and fim): 
            janela.intervalo_selecionado["inicio"] = data_selecionada
            janela.intervalo_selecionado["fim"] = None
        else: 
            janela.intervalo_selecionado["fim"] = data_selecionada

        inicio = janela.intervalo_selecionado["inicio"]
        fim = janela.intervalo_selecionado["fim"]

        if inicio and fim and comparar_datas(inicio, fim) > 0:
            janela.intervalo_selecionado["inicio"], janela.intervalo_selecionado["fim"] = fim, inicio

        data_ini_str = f"{janela.intervalo_selecionado['inicio']['estacao']} D{janela.intervalo_selecionado['inicio']['dia']}"
        
        if janela.intervalo_selecionado["fim"]:
            data_fim_str = f"{janela.intervalo_selecionado['fim']['estacao']} D{janela.intervalo_selecionado['fim']['dia']}"
            janela.data_selecionada = f"{data_ini_str} -> {data_fim_str}"
        else:
            janela.data_selecionada = data_ini_str
        
        atualizar_dias()

    def mudar_estacao(delta):
        nonlocal estacao_idx
        estacao_idx = (estacao_idx + delta) % len(ESTACOES)
        janela.estacao_idx = estacao_idx
        header_label.config(text=ESTACOES[estacao_idx])
        atualizar_dias()

    def on_day_enter(event, dia):
        lbl = dias_labels[dia]
        animate_hover_bg(lbl, lbl.cget("bg"), COR_CAL_DIA_HOVER)

    def on_day_leave(event, dia):
        lbl = dias_labels[dia]
        
        inicio = janela.intervalo_selecionado["inicio"]
        fim = janela.intervalo_selecionado["fim"]
        data_atual = {"estacao": ESTACOES[estacao_idx], "dia": dia}

        cor_original = COR_CAL_DIA_BG
        cor_final = COR_CAL_DIA_FG

        if inicio and fim and dentro_do_intervalo(data_atual, inicio, fim):
            cor_original = COR_INTERVALO
        if inicio and comparar_datas(data_atual, inicio) == 0:
            cor_original = COR_INICIO
            cor_final = COR_TEXTO_CABECALHO
        if fim and comparar_datas(data_atual, fim) == 0:
            cor_original = COR_FIM
            cor_final = COR_TEXTO_CABECALHO

        animate_hover_bg(lbl, lbl.cget("bg"), cor_original)
        lbl.config(fg=cor_final)
        
    frame_header = tk.Frame(top, bg=COR_CABECALHO)
    frame_header.pack(fill="x")

    btn_prev = tk.Label(frame_header, text="<", font=(FONTE_APP, 14), bg=COR_CABECALHO, fg=COR_TEXTO_CABECALHO, cursor=POINTER_CURSOR)
    btn_prev.pack(side="left", padx=10, pady=5)
    btn_prev.bind("<Button-1>", lambda e: mudar_estacao(-1))

    header_label = tk.Label(frame_header, text=ESTACOES[estacao_idx], font=(FONTE_APP, 14), bg=COR_CABECALHO, fg=COR_TEXTO_CABECALHO)
    header_label.pack(side="left", expand=True)

    btn_next = tk.Label(frame_header, text=">", font=(FONTE_APP, 14), bg=COR_CABECALHO, fg=COR_TEXTO_CABECALHO, cursor=POINTER_CURSOR)
    btn_next.pack(side="right", padx=10, pady=5)
    btn_next.bind("<Button-1>", lambda e: mudar_estacao(1))

    if som_hover_callback:
        btn_prev.bind("<Enter>", lambda e: som_hover_callback(), add=True)
        btn_next.bind("<Enter>", lambda e: som_hover_callback(), add=True)

    frame_cal = tk.Frame(top, bg=COR_FUNDO_POPUP, padx=5, pady=5)
    frame_cal.pack(pady=(0, 5))

    for i, dia_semana in enumerate(DIAS_SEMANA):
        lbl = tk.Label(frame_cal, text=dia_semana, font=(FONTE_APP, 11), bg=COR_FUNDO_POPUP, fg=COR_BORDA_POPUP)
        lbl.grid(row=0, column=i, padx=3, pady=3)

    dia = 1
    for linha in range(1, 5):
        for coluna in range(7):
            if dia > DIAS_POR_ESTACAO:
                break
            lbl = tk.Label(frame_cal, text=str(dia), bg=COR_CAL_DIA_BG, fg=COR_CAL_DIA_FG,
                           width=4, height=2, relief="flat", font=(FONTE_APP, 11),
                           cursor=POINTER_CURSOR) 
            lbl.grid(row=linha, column=coluna, padx=3, pady=3)
            
            lbl.bind("<Button-1>", lambda e, d=dia: selecionar_dia(d))
            lbl.bind("<Enter>", lambda e, d=dia: on_day_enter(e, d))
            lbl.bind("<Leave>", lambda e, d=dia: on_day_leave(e, d))
            
            dias_labels[dia] = lbl
            dia += 1

    atualizar_dias()

    btn_ok = tk.Button(top, text="Fechar", command=fechar_popup,
                   bg=COR_CABECALHO, fg=COR_TEXTO_CABECALHO, relief="flat", width=8, font=(FONTE_APP, 11),
                   activebackground="#f3a166", cursor=POINTER_CURSOR) 
    btn_ok.pack(side="bottom", pady=(0, 8))

    if som_hover_callback:
        btn_ok.bind("<Enter>", lambda e: som_hover_callback(), add=True)

    janela.update_idletasks()
    top.update_idletasks()

    cal_x = janela.winfo_x() + botao_calendario.winfo_x() + (botao_calendario.winfo_width() // 2) - (top.winfo_width() // 2)
    cal_y = janela.winfo_y() + botao_calendario.winfo_y() + botao_calendario.winfo_height() + 9
    top.geometry(f"+{cal_x}+{cal_y}")
    top.update_idletasks()