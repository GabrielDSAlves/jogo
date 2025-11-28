# frontend.py
# Interface, desenho, eventos e loop principal.
# Importa estado e funções de backend.py

import sys
import pygame
from pygame import gfxdraw
import backend

# Inicialização pygame (frontend controla display/font)
pygame.init()
pygame.display.set_caption("Álgebra Tátil - Simulador")

# tela e fontes (mantive como no seu original)
WIDTH, HEIGHT = backend.WIDTH, backend.HEIGHT
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
FPS = backend.FPS

FONT = pygame.font.SysFont("Arial", 20)
BIGFONT = pygame.font.SysFont("Arial", 30, bold=True)

clock = pygame.time.Clock()

# Botões (mesmos nomes do original)
generate_btn = pygame.Rect(20, 20, 220, 32)
clear_btn = pygame.Rect(250, 20, 120, 32)
dividir_btn = pygame.Rect(380, 20, 120, 32)

# Usaremos backend.palette (já tem rects) — frontend só desenha

# ---------- Desenho de peça (copiado do seu original) ----------
def draw_piece(surface, piece, highlight=False):
    r = piece["rect"]
    ptype = piece["type"]
    sign = piece["sign"]

    # ---------- DEFINIÇÃO DE CORES ----------
    if ptype == "x":
        color_pos = (58, 120, 255)      # azul forte
        color_neg = (201, 42, 42)       # vermelho escuro
    else:
        color_pos = (52, 199, 89)       # verde forte
        color_neg = (255, 127, 0)       # laranja queimado

    color = color_pos if sign > 0 else color_neg

    # ---------- SOMBRA SUAVE ----------
    shadow_rect = pygame.Rect(r.x + 3, r.y + 3, r.w, r.h)
    shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 70), (0, 0, shadow_rect.w, shadow_rect.h), border_radius=12)
    surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))

    # ---------- PEÇA PRINCIPAL ----------
    pygame.draw.rect(surface, color, r, border_radius=12)

    # ---------- BORDA DISCRETA ----------
    pygame.draw.rect(surface, (20, 20, 20), r, 2, border_radius=12)

    # ---------- TEXTO ----------
    txt = FONT.render("x" if ptype == "x" else "1", True, (255, 255, 255))
    surface.blit(txt, txt.get_rect(center=r.center))

    # ---------- FAIXA NEGATIVA (somente se sign < 0) ----------
    if sign < 0:
        neg_band = pygame.Rect(r.x, r.y - 10, r.w, 10)
        pygame.draw.rect(surface, (30, 30, 30), neg_band, border_radius=4)
        minus = FONT.render("-", True, (255, 255, 255))
        surface.blit(minus, (neg_band.centerx - minus.get_width() // 2,
                             neg_band.y + 1))

    # ---------- REALCE QUANDO ARRASTA ----------
    if highlight or piece.get("dragging", False):
        pygame.draw.rect(surface, (255, 240, 150), r, 4, border_radius=12)


# ---------- Desenha bolha de anulação (visual) ----------
def draw_annihilation(anim):
    t = anim["t"]
    dur = anim["dur"]
    frac = min(1.0, t / dur) if dur > 0 else 1.0

    r = int(24 * (1.0 - frac) + 2)
    alpha = int(200 * (1.0 - frac))

    if alpha <= 0:
        return

    surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 200, 60, alpha), (r + 2, r + 2), r)
    SCREEN.blit(surf, (anim["pos"][0] - r - 2, anim["pos"][1] - r - 2))


# ---------- Botões estilizados (copiados) ----------
def draw_button(surface, rect, text, color_idle, color_hover, text_color, mouse_pos):
    hovered = rect.collidepoint(mouse_pos)

    # sombra
    shadow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), (4, 4, rect.w, rect.h), border_radius=10)
    surface.blit(shadow, (rect.x, rect.y))

    base_color = color_hover if hovered else color_idle
    pygame.draw.rect(surface, base_color, rect, border_radius=10)
    pygame.draw.rect(surface, (60, 60, 90), rect, 2, border_radius=10)

    label = FONT.render(text, True, text_color)
    surface.blit(label, (
        rect.x + rect.w//2 - label.get_width()//2,
        rect.y + rect.h//2 - label.get_height()//2))


# ---------- Popup divisor (modal) ----------
def popup_divisor():
    width, height = 320, 200
    x = (WIDTH - width) // 2
    y = (HEIGHT - height) // 2

    input_text = ""

    ok_rect = pygame.Rect(x + 40, y + 130, 100, 40)
    cancel_rect = pygame.Rect(x + 180, y + 130, 100, 40)

    active = True
    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    try:
                        return int(input_text)
                    except:
                        return None
                else:
                    if event.unicode.isdigit():
                        input_text += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                if ok_rect.collidepoint(event.pos):
                    try:
                        return int(input_text)
                    except:
                        return None
                if cancel_rect.collidepoint(event.pos):
                    return None

        # desenhos do popup
        shadow_rect = pygame.Rect(x - 4, y - 4, width + 8, height + 8)
        pygame.draw.rect(SCREEN, (0, 0, 0, 120), shadow_rect, border_radius=10)
        pygame.draw.rect(SCREEN, (240, 240, 240), (x, y, width, height), border_radius=12)
        pygame.draw.rect(SCREEN, (180, 180, 180), (x, y, width, height), 3, border_radius=12)

        title = BIGFONT.render("Dividir por:", True, (20, 20, 20))
        SCREEN.blit(title, (x + width // 2 - title.get_width() // 2, y + 20))

        input_box = pygame.Rect(x + 40, y + 70, width - 80, 40)
        pygame.draw.rect(SCREEN, (255, 255, 255), input_box, border_radius=8)
        pygame.draw.rect(SCREEN, (120, 120, 120), input_box, 2, border_radius=8)

        text_surf = BIGFONT.render(input_text, True, (0, 0, 0))
        SCREEN.blit(text_surf, (input_box.x + 10, input_box.y + 6))

        pygame.draw.rect(SCREEN, (120, 200, 120), ok_rect, border_radius=10)
        ok_text = FONT.render("OK", True, (0, 0, 0))
        SCREEN.blit(ok_text, (ok_rect.centerx - ok_text.get_width() // 2,
                              ok_rect.centery - ok_text.get_height() // 2))

        pygame.draw.rect(SCREEN, (220, 120, 120), cancel_rect, border_radius=10)
        cancel_text = FONT.render("Cancelar", True, (0, 0, 0))
        SCREEN.blit(cancel_text, (cancel_rect.centerx - cancel_text.get_width() // 2,
                                  cancel_rect.centery - cancel_text.get_height() // 2))

        pygame.display.update()


# ---------- Desenha toda a UI (usa backend para estado) ----------
def draw_ui():
    SCREEN.fill((245, 240, 255))
    mx, my = pygame.mouse.get_pos()

    title = BIGFONT.render("Simulador Tátil de Álgebra", True, (50, 40, 70))
    SCREEN.blit(title, (backend.MARGIN, 55))

    # botões
    draw_button(SCREEN, generate_btn, "Nova Equação",
                (180, 210, 255), (160, 190, 245), (20, 20, 40), (mx, my))
    draw_button(SCREEN, clear_btn, "Limpar",
                (255, 190, 190), (245, 160, 160), (40, 20, 20), (mx, my))
    draw_button(SCREEN, dividir_btn, "Dividir",
                (200, 240, 200), (180, 220, 180), (20, 40, 20), (mx, my))

    # paleta (backend.palette contém rects)
    for p in backend.palette:
        r = p["rect"]
        if p["type"] == "x":
            color_pos = (58, 120, 255)
            color_neg = (201, 42, 42)
        else:
            color_pos = (52, 199, 89)
            color_neg = (255, 127, 0)
        base_color = color_pos if p["sign"] > 0 else color_neg

        shadow = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), (4, 4, r.w, r.h), border_radius=14)
        SCREEN.blit(shadow, (r.x, r.y))

        pygame.draw.rect(SCREEN, base_color, r, border_radius=14)
        pygame.draw.rect(SCREEN, (20, 20, 20), r, 3, border_radius=14)

        lab = BIGFONT.render(p["label"], True, (255, 255, 255))
        SCREEN.blit(lab, (
            r.x + r.w//2 - lab.get_width()//2,
            r.y + r.h//2 - lab.get_height()//2
        ))

    # mensagem
    msg = FONT.render(backend.message, True, (50, 40, 70))
    SCREEN.blit(msg, (backend.MARGIN, 150))

    # áreas esquerda e direita
    for area_x in (backend.LEFT_X, backend.RIGHT_X):
        shadow = pygame.Surface((backend.SIDE_W, backend.AREA_H), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), (6, 6, backend.SIDE_W, backend.AREA_H), border_radius=12)
        SCREEN.blit(shadow, (area_x, backend.AREA_Y))

        pygame.draw.rect(SCREEN, (250, 245, 255),
                         pygame.Rect(area_x, backend.AREA_Y, backend.SIDE_W, backend.AREA_H),
                         border_radius=12)
        pygame.draw.rect(SCREEN, (150, 140, 180),
                         pygame.Rect(area_x, backend.AREA_Y, backend.SIDE_W, backend.AREA_H),
                         2, border_radius=12)

    # divisões visuais
    subs = max(1, backend.divisoes_visuais)
    if subs > 1:
        step_h = backend.AREA_H / subs
        for i in range(1, subs):
            y = backend.AREA_Y + step_h * i
            pygame.draw.line(SCREEN, (120, 120, 160), (backend.LEFT_X + 20, y), (backend.LEFT_X + backend.SIDE_W - 20, y), 2)
            pygame.draw.line(SCREEN, (120, 120, 160), (backend.RIGHT_X + 20, y), (backend.RIGHT_X + backend.SIDE_W - 20, y), 2)

    # barra do '='
    eq_x = backend.LEFT_X + backend.SIDE_W + backend.MARGIN // 2
    pygame.draw.line(SCREEN, (80, 80, 120),
                     (eq_x, backend.AREA_Y + 20),
                     (eq_x, backend.AREA_Y + backend.AREA_H - 20), 3)

    eqtxt = BIGFONT.render("=", True, (70, 60, 90))
    SCREEN.blit(eqtxt, (eq_x - eqtxt.get_width()//2 - 4,
                        backend.AREA_Y + backend.AREA_H//2 - 20))

    # equação
    aL, bL, aR, bR = backend.compute_equation_from_pieces()
    eq_full = BIGFONT.render(f"{backend.format_side(aL, bL)} = {backend.format_side(aR, bR)}", True, (80, 70, 100))
    SCREEN.blit(eq_full, (backend.MARGIN, backend.AREA_Y - 55))

    # peças (estado do backend)
    for p in backend.pieces:
        draw_piece(SCREEN, p)

    # animações
    for anim in backend.animations:
        draw_annihilation(anim)

    inst = FONT.render("Use a paleta para criar peças. Somente somando com o oposto anula.", True, (60, 50, 70))
    SCREEN.blit(inst, (backend.MARGIN, backend.HEIGHT - 45))


# ---------- Loop principal (frontend controla eventos e chama backend) ----------
def mainloop():
    global SCREEN
    dragging_piece = None
    running = True

    backend.generate_random_equation_and_pieces()
    backend.pack_pieces()

    while running:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # MOUSE DOWN
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Botão Nova Equação
                    if generate_btn.collidepoint(event.pos):
                        backend.generate_random_equation_and_pieces()
                        backend.pack_pieces()

                    # Botão Limpar
                    elif clear_btn.collidepoint(event.pos):
                        backend.clear_pieces()
                        backend.divisoes_visuais = 0
                        backend.message_update("Limpo.")
                        backend.pack_pieces()

                    # Botão DIVIDIR (SÓ visual)
                    elif dividir_btn.collidepoint(event.pos):
                        divisor = popup_divisor()
                        if divisor is not None and divisor >= 1:
                            backend.divisoes_visuais = int(divisor)
                            backend.message_update(f"Tela dividida em {backend.divisoes_visuais}. Agora arraste as peças manualmente.")
                            backend.pack_pieces()
                        else:
                            backend.message_update("Divisão cancelada ou inválida.")
                        continue

                    # Paleta
                    added_from_palette = False
                    for pbtn in backend.palette:
                        if pbtn["rect"].collidepoint(event.pos):
                            left_count  = sum(1 for p in backend.pieces if p["side"] == "left")
                            right_count = sum(1 for p in backend.pieces if p["side"] == "right")
                            backend.add_piece(pbtn["type"], pbtn["sign"], "left", left_count, sub=0)
                            backend.add_piece(pbtn["type"], pbtn["sign"], "right", right_count, sub=0)
                            backend.pack_pieces()
                            backend.message_update("Peça adicionada em ambos os lados.")
                            added_from_palette = True
                            break
                    if added_from_palette:
                        continue

                    # Início do arrasto de peça
                    for p in reversed(backend.pieces):
                        if p["rect"].collidepoint(event.pos):
                            dragging_piece = p
                            p["dragging"] = True
                            ox = event.pos[0] - p["rect"].x
                            oy = event.pos[1] - p["rect"].y
                            p["offset"] = (ox, oy)
                            break

            # MOUSE UP
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if dragging_piece is None:
                        backend.pack_pieces()
                        continue

                    cx = dragging_piece["rect"].centerx
                    cy = dragging_piece["rect"].centery

                    if cx < backend.LEFT_X + backend.SIDE_W:
                        dragging_piece["side"] = "left"
                    elif cx > backend.RIGHT_X:
                        dragging_piece["side"] = "right"
                    else:
                        left_dist  = abs(cx - (backend.LEFT_X + backend.SIDE_W // 2))
                        right_dist = abs(cx - (backend.RIGHT_X + backend.SIDE_W // 2))
                        dragging_piece["side"] = "left" if left_dist < right_dist else "right"

                    # subdivisão
                    subs = max(1, backend.divisoes_visuais)
                    if subs > 1 and (backend.AREA_Y <= cy <= backend.AREA_Y + backend.AREA_H):
                        step_h = backend.AREA_H / subs
                        sub_index = int((cy - backend.AREA_Y) // step_h)
                        if sub_index < 0: sub_index = 0
                        if sub_index >= subs: sub_index = subs - 1
                        dragging_piece["sub"] = sub_index
                    else:
                        dragging_piece["sub"] = 0

                    dragging_piece["dragging"] = False
                    dragging_piece = None

                    backend.pack_pieces()

                    while backend.find_and_annihilate_pairs():
                        backend.pack_pieces()

            # MOUSE MOVE
            elif event.type == pygame.MOUSEMOTION:
                if dragging_piece:
                    ox, oy = dragging_piece["offset"]
                    dragging_piece["rect"].x = event.pos[0] - ox
                    dragging_piece["rect"].y = event.pos[1] - oy

            # KEYBOARD
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    backend.generate_random_equation_and_pieces()
                    backend.pack_pieces()

        backend.update_animations(dt)

        draw_ui()
        pygame.display.flip()

    pygame.quit()
    sys.exit()
