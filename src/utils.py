import time
import tkinter as tk
from PIL import Image, ImageDraw


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(rgb_tuple):
    return f'#{int(rgb_tuple[0]):02x}{int(rgb_tuple[1]):02x}{int(rgb_tuple[2]):02x}'

def _interpolate_color(start_color, end_color, fraction):
    start_rgb = _hex_to_rgb(start_color)
    end_rgb = _hex_to_rgb(end_color)
    
    new_rgb = []
    for i in range(3):
        diff = end_rgb[i] - start_rgb[i]
        new_val = int(start_rgb[i] + (diff * fraction))
        new_rgb.append(new_val)
        
    return _rgb_to_hex(tuple(new_rgb))


def animate_hover_color(widget, start_color, end_color, duration_ms=150):
    if hasattr(widget, "_animation_id"):
        try:
            widget.after_cancel(widget._animation_id)
        except tk.TclError:
            pass

    start_time = time.time()

    def animation_step():
        elapsed_time = (time.time() - start_time) * 1000
        fraction = elapsed_time / duration_ms

        if fraction >= 1.0:
            if widget.winfo_exists():
                widget.config(fg=end_color)
            if hasattr(widget, "_animation_id"):
                delattr(widget, "_animation_id")
            return
            
        current_color = _interpolate_color(start_color, end_color, fraction)
        
        try:
            if widget.winfo_exists():
                widget.config(fg=current_color)
                widget._animation_id = widget.after(16, animation_step)
            else:
                if hasattr(widget, "_animation_id"):
                    delattr(widget, "_animation_id")
        except tk.TclError:
            if hasattr(widget, "_animation_id"):
                delattr(widget, "_animation_id")

    animation_step()

def animate_hover_bg(widget, start_color, end_color, duration_ms=150):
    if hasattr(widget, "_animation_id"):
        try:
            widget.after_cancel(widget._animation_id)
        except tk.TclError:
            pass

    start_time = time.time()
    
    def animation_step():
        elapsed_time = (time.time() - start_time) * 1000
        fraction = elapsed_time / duration_ms
        
        if fraction >= 1.0:
            if widget.winfo_exists():
                widget.config(bg=end_color)
            if hasattr(widget, "_animation_id"):
                delattr(widget, "_animation_id")
            return
            
        current_color = _interpolate_color(start_color, end_color, fraction)
        
        try:
            if widget.winfo_exists():
                widget.config(bg=current_color)
                widget._animation_id = widget.after(16, animation_step)
            else:
                if hasattr(widget, "_animation_id"):
                    delattr(widget, "_animation_id")
        except tk.TclError:
            if hasattr(widget, "_animation_id"):
                delattr(widget, "_animation_id")

    animation_step()


def arredondar_cantos(imagem_pil, raio):
    mascara = Image.new('L', imagem_pil.size, 0)
    draw = ImageDraw.Draw(mascara)
    draw.rounded_rectangle((0, 0) + imagem_pil.size, raio, fill=255)
    imagem_arredondada = imagem_pil.copy()
    imagem_arredondada.putalpha(mascara)
    return imagem_arredondada

def criar_imagem_gradiente(width, height, color_start_hex, color_end_hex):
    start_r, start_g, start_b = int(color_start_hex[1:3], 16), int(color_start_hex[3:5], 16), int(color_start_hex[5:7], 16)
    end_r, end_g, end_b = int(color_end_hex[1:3], 16), int(color_end_hex[3:5], 16), int(color_end_hex[5:7], 16)
    image = Image.new("RGB", (width, height))
    for y in range(height):
        r = int(start_r + (end_r - start_r) * (y / height))
        g = int(start_g + (end_g - start_g) * (y / height))
        b = int(start_b + (end_b - start_b) * (y / height))
        for x in range(width):
            image.putpixel((x, y), (r, g, b))
    return image