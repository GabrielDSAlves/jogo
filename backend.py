# backend.py
# Lógica, estado e manipulação das peças / equações.
# Mantive suas funções e variáveis quase exatamente como estavam.
# OBS: este módulo usa pygame apenas para Rects (não inicializa display).

import random
import re
import pygame
import math

# Configurações (valores usados pelo frontend também)
WIDTH, HEIGHT = 1100, 700
FPS = 60

# Layout
MARGIN = 20
SIDE_W = (WIDTH - 3 * MARGIN) // 2
LEFT_X = MARGIN
RIGHT_X = LEFT_X + SIDE_W + MARGIN
AREA_Y = 180
AREA_H = HEIGHT - AREA_Y - MARGIN - 80

# Piece sizes
PIECE_SIZE = 50
PIECE_GAP = 8

# Estado global
pieces = []
next_id = 1
message = ""
divisoes_visuais = 0   # quantas divisões visuais (1 == sem divisão)
animations = []

# Botões da paleta (rects criados aqui — frontend desenha)
PALETTE_BTN_W = 58
PALETTE_BTN_H = 58

palette = [
    {"label": "+1", "type": "n", "sign": 1, "rect": pygame.Rect(500, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
    {"label": "-1", "type": "n", "sign": -1, "rect": pygame.Rect(580, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
    {"label": "+x", "type": "x", "sign": 1, "rect": pygame.Rect(660, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
    {"label": "-x", "type": "x", "sign": -1, "rect": pygame.Rect(740, 100, PALETTE_BTN_W, PALETTE_BTN_H)},
]

# -----------------------------
# Funções utilitárias (parsing e equações)
# -----------------------------
def parse_linear_side(side_text):
    text = side_text.replace(" ", "")
    if text == "":
        return 0, 0
    if text[0] not in "+-":
        text = "+" + text
    tokens = re.findall(r'([+-])(\\d*)(x?)', text)
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

# -----------------------------
# Estado de peças e utilitários
# -----------------------------
def message_update(text):
    global message
    message = text

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

    rect = pygame.Rect(int(x), int(y), PIECE_SIZE, PIECE_SIZE)

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

# -----------------------------
# Empacotamento e posicionamento
# -----------------------------
def pack_pieces():
    """
    Empacota as peças dentro da área do lado esquerdo/direito.
    Se houver divisões visuais (>1), cada subdivisão recebe sua própria grade.
    """
    subs = max(1, divisoes_visuais)
    step_h = AREA_H / subs

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

    for side in ("left", "right"):
        for s in range(subs):
            lst = groups[side][s]
            for idx, p in enumerate(lst):
                if side == "left":
                    base_x = LEFT_X + 20
                else:
                    base_x = RIGHT_X + 20
                base_y = AREA_Y + 10 + s * step_h

                col = idx % 6
                row = idx // 6
                p["rect"].x = int(base_x + col * (PIECE_SIZE + PIECE_GAP))
                p["rect"].y = int(base_y + row * (PIECE_SIZE + PIECE_GAP))
                p["side"] = side
                p["sub"] = s

# -----------------------------
# Anulação (encontra pares + e - do mesmo tipo no mesmo lado)
# -----------------------------
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

# Because the original function generate_pieces_from_equation_values had the same name, define it:
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

# -----------------------------
# Animações (apenas atualização de tempo)
# -----------------------------
def update_animations(dt):
    to_remove = []
    for anim in animations:
        anim["t"] += dt
        if anim["t"] >= anim["dur"]:
            to_remove.append(anim)
    for a in to_remove:
        animations.remove(a)

# Expose API
__all__ = [
    'WIDTH','HEIGHT','FPS',
    'MARGIN','SIDE_W','LEFT_X','RIGHT_X','AREA_Y','AREA_H',
    'PIECE_SIZE','PIECE_GAP',
    'pieces','next_id','message','divisoes_visuais','animations',
    'PALETTE_BTN_W','PALETTE_BTN_H','palette',
    'parse_linear_side','parse_equation','clear_pieces','add_piece',
    'generate_pieces_from_equation_values','generate_random_equation_and_pieces',
    'compute_equation_from_pieces','format_side','check_solved_and_return_solution',
    'pack_pieces','find_and_annihilate_pairs','message_update','update_animations'
]
