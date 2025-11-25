import pygame
import sys
import random
import re
from pygame import gfxdraw
import math

pygame.init()
pygame.display.set_caption("Álgebra Tátil - Simulador (Protótipo)")

#Tela 
WIDTH, HEIGHT = 1100, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
FPS = 60

FONT = pygame.font.SysFont("Arial", 20)
BIGFONT = pygame.font.SysFont("Arial", 30, bold=True)

# Layout
MARGIN = 20
SIDE_W = (WIDTH - 3 * MARGIN) // 2
LEFT_X = MARGIN
RIGHT_X = LEFT_X + SIDE_W + MARGIN
AREA_Y = 180
AREA_H = HEIGHT - AREA_Y - MARGIN - 80

# Paleta de cores clean pastel
BG = (250, 247, 255)
TABLE = (240, 230, 250)
LINE = (90, 90, 120)
SQUARE_COLOR = (255, 140, 180)
CIRCLE_COLOR = (120, 160, 255)
NEG_STRIPE = (60, 60, 60)
TEXT_COLOR = (40, 40, 60)
HIGHLIGHT = (255, 220, 80)

clock = pygame.time.Clock()

# Piece sizes
PIECE_SIZE = 50
PIECE_GAP = 8

# Game objects
pieces = []
next_id = 1
message = ""
divisoes_visuais = 0   # quantas divisões visuais (1 == sem divisão)
animations = []

# Botões da paleta
PALETTE_BTN_W = 58
PALETTE_BTN_H = 58

palette = [
    {"label": "+1", "type": "n", "sign": 1, "rect": pygame.Rect(500, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
    {"label": "-1", "type": "n", "sign": -1, "rect": pygame.Rect(580, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
    {"label": "+x", "type": "x", "sign": 1, "rect": pygame.Rect(660, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
    {"label": "-x", "type": "x", "sign": -1, "rect": pygame.Rect(740, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
]

generate_btn = pygame.Rect(20, 20, 220, 32)
clear_btn = pygame.Rect(250, 20, 120, 32)
dividir_btn = pygame.Rect(380, 20, 120, 32)   # <-- Novo botão

# -----------------------------
# Funções utilitárias
# -----------------------------

def parse_linear_side(side_text):
    text = side_text.replace(" ", "")
    if text == "":
        return 0, 0
    if text[0] not in "+-":
        text = "+" + text
    tokens = re.findall(r'([+-])(\d*)(x?)', text)
    coef = 0
    const = 0
    for sign, num, hasx in tokens:
        s = 1 if sign == "+" else -1
        if hasx:
            val = int(num) if num != "" else 1
            coef += s * val
        else:
            if num != "":
                const += s * int(num)
    return coef, const


def parse_equation(eq_text):
    parts = eq_text.split("=")
    if len(parts) != 2:
        raise ValueError("Equação deve ter exatamente um '='")
    left = parts[0].strip()
    right = parts[1].strip()
    aL, bL = parse_linear_side(left)
    aR, bR = parse_linear_side(right)
    return aL, bL, aR, bR


def clear_pieces():
    global pieces, next_id
    pieces = []
    next_id = 1


def add_piece(ptype, sign, side, index=None, x=None, y=None, sub=0):
    """
    Adiciona peça. sub é o índice da subdivisão (default 0).
    """
    global next_id

    if x is None or y is None:
        col = index % 6 if index is not None else 0
        row = (index // 6) if index is not None else 0
        if side == "left":
            x = LEFT_X + 20 + col * (PIECE_SIZE + PIECE_GAP)
            y = AREA_Y + 20 + row * (PIECE_SIZE + PIECE_GAP)
        else:
            x = RIGHT_X + 20 + col * (PIECE_SIZE + PIECE_GAP)
            y = AREA_Y + 20 + row * (PIECE_SIZE + PIECE_GAP)

    rect = pygame.Rect(x, y, PIECE_SIZE, PIECE_SIZE)

    pieces.append({
        "id": next_id,
        "type": ptype,
        "sign": sign,
        "side": side,
        "sub": sub,                # subdivisão onde está a peça
        "rect": rect,
        "offset": (0, 0),
        "dragging": False
    })
    next_id += 1


def generate_pieces_from_equation_values(aL, bL, aR, bR):
    clear_pieces()

    idxL = 0
    for _ in range(abs(aL)):
        sign = 1 if aL >= 0 else -1
        add_piece('x', sign, 'left', idxL, sub=0)
        idxL += 1
    for _ in range(abs(bL)):
        sign = 1 if bL >= 0 else -1
        add_piece('n', sign, 'left', idxL, sub=0)
        idxL += 1

    idxR = 0
    for _ in range(abs(aR)):
        sign = 1 if aR >= 0 else -1
        add_piece('x', sign, 'right', idxR, sub=0)
        idxR += 1
    for _ in range(abs(bR)):
        sign = 1 if bR >= 0 else -1
        add_piece('n', sign, 'right', idxR, sub=0)
        idxR += 1


def draw_piece(surface, piece, highlight=False):
    r = piece["rect"]

    # Se houver text_override (peça fracionária / texto), desenha retângulo com texto
    if piece.get("text_override") is not None:
        pygame.draw.rect(surface, (220, 220, 220), r, border_radius=8)
        pygame.draw.rect(surface, LINE, r, 2, border_radius=8)
        txt = FONT.render(piece["text_override"], True, TEXT_COLOR)
        surface.blit(txt, txt.get_rect(center=r.center))
        return

    ptype = piece["type"]
    sign = piece["sign"]

    # sombra
    if ptype == 'x':
        shadow_rect = pygame.Rect(r.x + 6, r.y + 8, r.w, r.h)
        pygame.draw.ellipse(surface, (30, 30, 30, 80), shadow_rect)
    else:
        shadow_rect = pygame.Rect(r.x + 6, r.y + 8, r.w, r.h)
        s = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (30, 30, 30, 80), (0, 0, shadow_rect.w, shadow_rect.h), border_radius=8)
        surface.blit(s, (shadow_rect.x, shadow_rect.y))

    # corpo
    if ptype == 'n':
        base = SQUARE_COLOR
        pygame.draw.rect(surface, base, r, border_radius=8)
        hl = (min(base[0] + 50, 255), min(base[1] + 50, 255), min(base[2] + 50, 255))
        pygame.draw.rect(surface, hl, (r.x + 4, r.y + 4, r.w - 8, r.h // 3), border_radius=6)
        pygame.draw.rect(surface, LINE, r, 2, border_radius=8)
        txt = FONT.render("1", True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=r.center))

    else:
        center = (r.x + r.w // 2, r.y + r.h // 2)
        radius = r.w // 2
        pygame.gfxdraw.filled_circle(surface, center[0], center[1], radius, CIRCLE_COLOR)
        pygame.gfxdraw.filled_circle(surface, center[0] - 8, center[1] - 10, radius // 3,
                                     (min(CIRCLE_COLOR[0] + 40, 255),
                                      min(CIRCLE_COLOR[1] + 40, 255),
                                      min(CIRCLE_COLOR[2] + 40, 255)))
        pygame.draw.circle(surface, LINE, center, radius, 2)
        txt = FONT.render("x", True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=center))

    if sign < 0:
        stripe_h = 10
        stripe_rect = pygame.Rect(r.x, r.y - 10, r.w, stripe_h)
        pygame.draw.rect(surface, NEG_STRIPE, stripe_rect)
        s = FONT.render("-", True, (255, 255, 255))
        surface.blit(s, (stripe_rect.centerx - s.get_width() // 2,
                         stripe_rect.y - s.get_height() // 2 + 2))

    if highlight or piece.get("dragging", False):
        pygame.draw.rect(surface, HIGHLIGHT, r, 3, border_radius=8)


def compute_equation_from_pieces():
    aL = bL = aR = bR = 0
    for p in pieces:
        side = p["side"]
        if p["type"] == 'x':
            if side == 'left':
                aL += p["sign"]
            else:
                aR += p["sign"]
        else:
            if side == 'left':
                bL += p["sign"]
            else:
                bR += p["sign"]
    return aL, bL, aR, bR


def format_side(a, b):
    parts = []
    if a != 0:
        if abs(a) == 1:
            parts.append(("-" if a == -1 else "") + "x")
        else:
            parts.append(f"{a}x")
    if b != 0:
        parts.append(("+" if b > 0 and len(parts) > 0 else "") + str(b))
    if len(parts) == 0:
        return "0"
    return " ".join(parts)


def check_solved_and_return_solution():
    aL, bL, aR, bR = compute_equation_from_pieces()
    coef = aL - aR
    rhs = bR - bL

    if coef == 0:
        return None
    if rhs % coef != 0:
        return None

    xval = rhs // coef

    count_left_x = sum(1 for p in pieces if p["type"] == 'x' and p["side"] == 'left')
    count_right_x = sum(1 for p in pieces if p["type"] == 'x' and p["side"] == 'right')

    if (count_left_x == 1 and count_right_x == 0) or (count_right_x == 1 and count_left_x == 0):
        return xval

    return None


def pack_pieces():
    """
    Empacota as peças dentro da área do lado esquerdo/direito.
    Se houver divisões visuais (>1), cada subdivisão recebe sua própria grade.
    """
    # quantas divisões usar para posicionamento (pelo menos 1)
    subs = max(1, divisoes_visuais)
    # passo de altura por subdivisão
    step_h = AREA_H / subs

    # organizar por side e sub
    groups = {"left": {}, "right": {}}
    for side in ("left", "right"):
        for s in range(subs):
            groups[side][s] = []

    for p in pieces:
        side = p.get("side", "left")
        sub = int(p.get("sub", 0))
        if sub < 0: sub = 0
        if sub >= subs: sub = subs - 1
        p["sub"] = sub
        groups[side][sub].append(p)

    # posicionar cada grupo (cada subdivisão) em grade (6 colunas)
    for side in ("left", "right"):
        for s in range(subs):
            lst = groups[side][s]
            col = 0
            row = 0
            for idx, p in enumerate(lst):
                # coords base
                if side == "left":
                    base_x = LEFT_X + 20
                else:
                    base_x = RIGHT_X + 20
                base_y = AREA_Y + 10 + s * step_h

                # 6 colunas
                col = idx % 6
                row = idx // 6
                p["rect"].x = int(base_x + col * (PIECE_SIZE + PIECE_GAP))
                p["rect"].y = int(base_y + row * (PIECE_SIZE + PIECE_GAP))
                # keep side and sub
                p["side"] = side
                p["sub"] = s


def find_and_annihilate_pairs():
    removed_any = False

    for side in ("left", "right"):
        for ptype in ("x", "n"):
            positives = [p for p in pieces if p["side"] == side and p["type"] == ptype and p["sign"] == 1]
            negatives = [p for p in pieces if p["side"] == side and p["type"] == ptype and p["sign"] == -1]

            pairs = min(len(positives), len(negatives))

            for i in range(pairs):
                p_pos = positives[i]
                p_neg = negatives[i]

                cx = (p_pos["rect"].centerx + p_neg["rect"].centerx) // 2
                cy = (p_pos["rect"].centery + p_neg["rect"].centery) // 2

                animations.append({"pos": (cx, cy), "t": 0.0, "dur": 0.5})

                id1 = p_pos["id"]
                id2 = p_neg["id"]

                for rem in (id1, id2):
                    for idx, pp in enumerate(list(pieces)):
                        if pp["id"] == rem:
                            pieces.remove(pp)
                removed_any = True

    if removed_any:
        message_update("Peças anuladas!")
    return removed_any


def message_update(text):
    global message
    message = text


def generate_random_equation_and_pieces():
    attempts = 0

    while True:
        attempts += 1

        x0 = random.randint(-5, 5)
        coefL = random.randint(-3, 3)
        coefR = random.randint(-3, 3)
        coef = coefL - coefR

        if coef == 0:
            continue

        bL = random.randint(-5, 5)
        bR = bL + coef * x0

        if abs(coefL) <= 6 and abs(coefR) <= 6 and abs(bL) <= 6 and abs(bR) <= 6:
            total = abs(coefL) + abs(bL) + abs(coefR) + abs(bR)
            if total <= 24:
                generate_pieces_from_equation_values(coefL, bL, coefR, bR)
                message_update(f"Equação gerada com solução x = {x0}")
                return

        if attempts > 500:
            generate_pieces_from_equation_values(2, 1, 1, 3)
            message_update("Equação padrão gerada (fallback).")
            return


def draw_ui():
    SCREEN.fill(BG)

    title = BIGFONT.render("Simulador Tátil de Álgebra", True, TEXT_COLOR)
    SCREEN.blit(title, (MARGIN, 60))

    pygame.draw.rect(SCREEN, (200, 200, 200), generate_btn, border_radius=6)
    SCREEN.blit(FONT.render("    Nova Equação", True, TEXT_COLOR),
                (generate_btn.x + 10, generate_btn.y + 6))

    pygame.draw.rect(SCREEN, (200, 200, 200), clear_btn, border_radius=6)
    SCREEN.blit(FONT.render("  Limpar", True, TEXT_COLOR),
                (clear_btn.x + 20, clear_btn.y + 6))

    pygame.draw.rect(SCREEN, (200, 200, 200), dividir_btn, border_radius=6)
    SCREEN.blit(FONT.render("  Dividir", True, TEXT_COLOR),
                (dividir_btn.x + 25, dividir_btn.y + 6))


    for p in palette:
        pygame.draw.rect(SCREEN, (240, 240, 240), p["rect"], border_radius=6)
        pygame.draw.rect(SCREEN, LINE, p["rect"], 2, border_radius=6)
        lab = FONT.render(p["label"], True, TEXT_COLOR)
        SCREEN.blit(lab, (p["rect"].x + (p["rect"].w - lab.get_width()) // 2,
                          p["rect"].y + (p["rect"].h - lab.get_height()) // 2))

    msg = FONT.render(message, True, TEXT_COLOR)
    SCREEN.blit(msg, (MARGIN, 160))

    left_area = pygame.Rect(LEFT_X, AREA_Y, SIDE_W, AREA_H)
    right_area = pygame.Rect(RIGHT_X, AREA_Y, SIDE_W, AREA_H)
    pygame.draw.rect(SCREEN, TABLE, left_area, border_radius=8)
    pygame.draw.rect(SCREEN, TABLE, right_area, border_radius=8)

    # -----------------------------------------------------
    # DESENHA AS DIVISÕES VISUAIS NOS DOIS LADOS
    # -----------------------------------------------------
    subs = max(1, divisoes_visuais)
    if subs > 1:
        total_h = AREA_H
        step_h = total_h / subs

        # Lado esquerdo
        for i in range(1, subs):
            y = AREA_Y + i * step_h
            pygame.draw.line(SCREEN, (100, 100, 100), 
                            (LEFT_X + 10, y), 
                            (LEFT_X + SIDE_W - 10, y), 2)

        # Lado direito
        for i in range(1, subs):
            y = AREA_Y + i * step_h
            pygame.draw.line(SCREEN, (100, 100, 100), 
                            (RIGHT_X + 10, y), 
                            (RIGHT_X + SIDE_W - 10, y), 2)


    eq_x = LEFT_X + SIDE_W + MARGIN // 2
    pygame.draw.line(SCREEN, LINE, (eq_x, AREA_Y + 20), (eq_x, AREA_Y + AREA_H - 20), 2)

    eqtxt = BIGFONT.render("=", True, TEXT_COLOR)
    SCREEN.blit(eqtxt, (eq_x - eqtxt.get_width() // 2 - 4, AREA_Y + AREA_H // 2 - 20))

    aL, bL, aR, bR = compute_equation_from_pieces()
    eq_full = BIGFONT.render(f"{format_side(aL, bL)} = {format_side(aR, bR)}", True, TEXT_COLOR)
    SCREEN.blit(eq_full, (MARGIN, AREA_Y - 60))

    for p in pieces:
        draw_piece(SCREEN, p)

    for anim in animations:
        draw_annihilation(anim)

    inst = FONT.render(
        "Use a paleta para criar novas peças. Somente somando com o oposto anula.",
        True, TEXT_COLOR)
    SCREEN.blit(inst, (MARGIN, HEIGHT - 50))

    # sol = check_solved_and_return_solution()
    # if sol is not None:
    #     sol_txt = BIGFONT.render(f"Equação resolvida: x = {sol}", True, (30, 150, 30))
    #     SCREEN.blit(sol_txt, (RIGHT_X - 20, HEIGHT - 90))


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


def update_animations(dt):
    to_remove = []
    for anim in animations:
        anim["t"] += dt
        if anim["t"] >= anim["dur"]:
            to_remove.append(anim)
    for a in to_remove:
        animations.remove(a)

def popup_divisor():
    width, height = 260, 140
    x = (WIDTH - width) // 2
    y = (HEIGHT - height) // 2
    input_text = ""
    active = True

    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try:
                        return int(float(input_text))
                    except:
                        return None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    # aceitar só dígitos
                    if event.unicode.isdigit():
                        input_text += event.unicode

        # desenha popup simples
        pygame.draw.rect(SCREEN, (245, 245, 245), (x, y, width, height), border_radius=8)
        pygame.draw.rect(SCREEN, (50, 50, 50), (x, y, width, height), 2, border_radius=8)

        label = FONT.render("Dividir por (inteiro):", True, (40, 40, 40))
        SCREEN.blit(label, (x + 20, y + 20))

        txt = BIGFONT.render(input_text, True, (20, 20, 20))
        SCREEN.blit(txt, (x + 20, y + 70))

        pygame.display.update()
        clock.tick(30)


def mainloop():
    global message, divisoes_visuais
    dragging_piece = None
    running = True

    generate_random_equation_and_pieces()
    pack_pieces()

    while running:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # -------------------------------------------------------
            # MOUSE DOWN
            # -------------------------------------------------------
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    # Botão Nova Equação
                    if generate_btn.collidepoint(event.pos):
                        generate_random_equation_and_pieces()
                        pack_pieces()

                    # Botão Limpar
                    elif clear_btn.collidepoint(event.pos):
                        clear_pieces()
                        divisoes_visuais = 0
                        message_update("Limpo.")
                        pack_pieces()

                    # Botão DIVIDIR (SÓ visual)
                    elif dividir_btn.collidepoint(event.pos):
                        divisor = popup_divisor()
                        if divisor is not None and divisor >= 1:
                            divisoes_visuais = int(divisor)
                            message_update(f"Tela dividida em {divisoes_visuais}. Agora arraste as peças manualmente.")
                            # só redesenha as divisões — não faz operações automáticas
                            pack_pieces()
                        else:
                            message_update("Divisão cancelada ou inválida.")
                        continue

                    # Paleta
                    added_from_palette = False
                    for pbtn in palette:
                        if pbtn["rect"].collidepoint(event.pos):
                            left_count  = sum(1 for p in pieces if p["side"] == "left")
                            right_count = sum(1 for p in pieces if p["side"] == "right")
                            add_piece(pbtn["type"], pbtn["sign"], "left", left_count, sub=0)
                            add_piece(pbtn["type"], pbtn["sign"], "right", right_count, sub=0)
                            pack_pieces()
                            message_update("Peça adicionada em ambos os lados.")
                            added_from_palette = True
                            break
                    if added_from_palette:
                        continue

                    # Início do arrasto de peça
                    for p in reversed(pieces):
                        if p["rect"].collidepoint(event.pos):
                            dragging_piece = p
                            p["dragging"] = True
                            ox = event.pos[0] - p["rect"].x
                            oy = event.pos[1] - p["rect"].y
                            p["offset"] = (ox, oy)
                            break

            # -------------------------------------------------------
            # MOUSE UP
            # -------------------------------------------------------
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # Segurança: evita erro quando peça já foi anulada
                    if dragging_piece is None:
                        pack_pieces()
                        continue

                    cx = dragging_piece["rect"].centerx
                    cy = dragging_piece["rect"].centery

                    # Decide lado baseado na posição
                    if cx < LEFT_X + SIDE_W:
                        dragging_piece["side"] = "left"
                    elif cx > RIGHT_X:
                        dragging_piece["side"] = "right"
                    else:
                        left_dist  = abs(cx - (LEFT_X + SIDE_W // 2))
                        right_dist = abs(cx - (RIGHT_X + SIDE_W // 2))
                        dragging_piece["side"] = "left" if left_dist < right_dist else "right"

                    # Decide subdivisão (se houver)
                    subs = max(1, divisoes_visuais)
                    if subs > 1 and (AREA_Y <= cy <= AREA_Y + AREA_H):
                        step_h = AREA_H / subs
                        sub_index = int((cy - AREA_Y) // step_h)
                        if sub_index < 0: sub_index = 0
                        if sub_index >= subs: sub_index = subs - 1
                        dragging_piece["sub"] = sub_index
                    else:
                        dragging_piece["sub"] = 0

                    dragging_piece["dragging"] = False
                    dragging_piece = None

                    pack_pieces()

                    # Anulação — pode remover a peça durante o drop
                    while find_and_annihilate_pairs():
                        pack_pieces()

            # -------------------------------------------------------
            # MOUSE MOVE
            # -------------------------------------------------------
            elif event.type == pygame.MOUSEMOTION:
                if dragging_piece:
                    ox, oy = dragging_piece["offset"]
                    dragging_piece["rect"].x = event.pos[0] - ox
                    dragging_piece["rect"].y = event.pos[1] - oy

            # -------------------------------------------------------
            # KEYBOARD
            # -------------------------------------------------------
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    generate_random_equation_and_pieces()
                    pack_pieces()

        update_animations(dt)

        draw_ui()
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    mainloop()
