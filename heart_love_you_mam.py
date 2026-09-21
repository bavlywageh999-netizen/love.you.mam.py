"""
Glowing particle heart made of tiny "Love You Mam" words.

Run:   pip install pygame
       python heart_love_you_mam.py

ESC or closing the window quits. The animation loops.

Change the text here:
"""
import math
import random

# ----------------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------------
TEXT_VARIANTS = ["Love You Mam", "LOVE YOU MAM", "love you mam", "Love you mam"]
BIG_TEXT = "Love You Mam"          # the big white text that fades in at the end

WIDTH, HEIGHT = 576, 1024          # portrait (phone) size
FPS = 60
HEART_CENTER = (WIDTH // 2, 360)   # where the heart's origin sits
HEART_SCALE = 13.5                 # bigger number = bigger heart

N_OUTLINE = 150                    # particles on the heart edge
N_FILL = 190                       # particles filling the inside

COLORS = [(25, 110, 230), (10, 130, 220), (45, 95, 225), (70, 140, 235), (20, 85, 200)]

# timeline (in frames @ 60 fps)
BIG_TEXT_START = 800
BIG_TEXT_RAMP = 110
FADE_START = 1010
TOTAL_FRAMES = 1140


# ----------------------------------------------------------------------------
# SIMULATION  (no pygame needed for this part)
# ----------------------------------------------------------------------------
class Particle:
    __slots__ = ("word", "color", "x", "y", "alpha", "delay",
                 "flicker", "size_mult", "phase")

    def __init__(self, word, color, x, y, delay, size_mult):
        self.word = word
        self.color = color
        self.x = x
        self.y = y
        self.alpha = 0
        self.delay = delay
        self.flicker = random.uniform(0, math.tau)
        self.size_mult = size_mult
        self.phase = random.uniform(0, math.tau)


def heart_point(t):
    """Classic parametric heart curve."""
    x = 16 * math.sin(t) ** 3
    y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
    return x, y


def make_particles(seed=None):
    rnd = random.Random(seed)
    cx, cy = HEART_CENTER
    particles = []

    # outline: draws itself around the heart, starting at the top dip -> right lobe.
    # Points are spaced evenly by ARC LENGTH so nothing bunches up at the dip / tip.
    fine = [heart_point(i / 4000 * math.tau) for i in range(4001)]
    cum = [0.0]
    for i in range(1, len(fine)):
        cum.append(cum[-1] + math.hypot(fine[i][0] - fine[i - 1][0], fine[i][1] - fine[i - 1][1]))
    total_len = cum[-1]

    def point_at(length):
        lo, hi = 0, len(cum) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < length:
                lo = mid + 1
            else:
                hi = mid
        return fine[lo]

    for i in range(N_OUTLINE):
        hx, hy = point_at((i + rnd.uniform(-0.3, 0.3)) / N_OUTLINE * total_len % total_len)
        k = rnd.uniform(0.95, 1.0)
        x = cx + hx * HEART_SCALE * k + rnd.uniform(-4, 4)
        y = cy + hy * HEART_SCALE * k + rnd.uniform(-4, 4)
        delay = 20 + (i / N_OUTLINE) * 170 + rnd.randint(0, 10)
        particles.append(Particle(rnd.choice(TEXT_VARIANTS), rnd.choice(COLORS),
                                  x, y, delay, rnd.uniform(0.75, 1.5)))

    # fill: sample uniformly INSIDE the heart; the edge fades in first, the middle last
    poly = [heart_point(i / 240 * math.tau) for i in range(240)]

    def inside(px, py):
        hit = False
        j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                hit = not hit
            j = i
        return hit

    fill = []
    while len(fill) < N_FILL:
        px, py = rnd.uniform(-16, 16), rnd.uniform(-13, 17)
        if not inside(px, py):
            continue
        depth = min(math.hypot(px - qx, py - qy) for qx, qy in poly)   # distance to the edge
        fill.append((px, py, depth))
    max_depth = max(d for _, _, d in fill) or 1.0

    for px, py, depth in fill:
        x = cx + px * HEART_SCALE + rnd.uniform(-4, 4)
        y = cy + py * HEART_SCALE + rnd.uniform(-4, 4)
        delay = 180 + (depth / max_depth) * 480 + rnd.randint(0, 120)
        particles.append(Particle(rnd.choice(TEXT_VARIANTS), rnd.choice(COLORS),
                                  x, y, delay, rnd.uniform(0.7, 1.5)))
    return particles


def step_particle(p, frame):
    """Advance one particle. Returns (alpha_0_to_255, dx, dy)."""
    if frame > p.delay and p.alpha < 255:
        p.alpha = min(255, p.alpha + 14 + random.randint(0, 4))

    if p.alpha >= 255:
        flick = 0.75 + 0.25 * math.sin(frame * 0.04 + p.flicker)
    else:
        flick = 1.0

    fade = 1.0
    if frame > FADE_START:
        fade = max(0.0, 1.0 - (frame - FADE_START) / (TOTAL_FRAMES - FADE_START))

    alpha = int(p.alpha * flick * fade)
    dx = math.sin(frame * 0.02 + p.phase) * 2.0
    dy = math.cos(frame * 0.017 + p.phase) * 2.0
    return alpha, dx, dy


def big_text_strength(frame):
    """0..1 for the big centre text (also fades out with everything else)."""
    s = min(1.0, max(0.0, (frame - BIG_TEXT_START) / BIG_TEXT_RAMP))
    if frame > FADE_START:
        s *= max(0.0, 1.0 - (frame - FADE_START) / (TOTAL_FRAMES - FADE_START))
    return s


# ----------------------------------------------------------------------------
# PYGAME DRAWING
# ----------------------------------------------------------------------------
def main():
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Love You Mam")
    clock = pygame.time.Clock()

    # dark background with a soft vignette
    background = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        v = int(6 + 8 * (1 - abs(y - HEIGHT * 0.4) / (HEIGHT * 0.6)))
        pygame.draw.line(background, (2, 3, max(6, v + 4)), (0, y), (WIDTH, y))

    small_fonts = {}
    def get_font(size):
        size = max(6, int(size))
        if size not in small_fonts:
            small_fonts[size] = pygame.font.SysFont("arial,segoeui,dejavusans,sans", size, bold=True)
        return small_fonts[size]

    big_font = pygame.font.SysFont("georgia,timesnewroman,times,dejavuserif,serif", 64, bold=True)
    ghost_font = pygame.font.SysFont("georgia,timesnewroman,times,dejavuserif,serif", 84, bold=True)

    sprite_cache = {}
    def get_sprite(word, color, size, level):
        """Text pre-rendered on black and dimmed to `level` (0..15)."""
        key = (word, color, size, level)
        s = sprite_cache.get(key)
        if s is None:
            txt = get_font(size).render(word, True, color)
            s = pygame.Surface(txt.get_size())
            s.blit(txt, (0, 0))
            m = (level + 1) * 16 - 1
            s.fill((m, m, m), special_flags=pygame.BLEND_RGB_MULT)
            sprite_cache[key] = s
        return s

    big_sprite = big_font.render(BIG_TEXT, True, (255, 255, 255))
    ghost_sprite = ghost_font.render(BIG_TEXT, True, (150, 155, 170))

    glow_layer = pygame.Surface((WIDTH, HEIGHT))
    text_layer = pygame.Surface((WIDTH, HEIGHT))

    particles = make_particles()
    frame = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        screen.blit(background, (0, 0))
        glow_layer.fill((0, 0, 0))
        text_layer.fill((0, 0, 0))
        frame += 1

        for p in particles:
            alpha, dx, dy = step_particle(p, frame)
            if alpha <= 0:
                continue
            size = int(12 * p.size_mult)
            sprite = get_sprite(p.word, p.color, size, min(15, alpha // 16))
            pos = (int(p.x + dx - sprite.get_width() / 2), int(p.y + dy - sprite.get_height() / 2))
            text_layer.blit(sprite, pos, special_flags=pygame.BLEND_RGB_ADD)
            glow_layer.blit(sprite, pos, special_flags=pygame.BLEND_RGB_ADD)

        # big centre text + blurry ghost behind it
        s = big_text_strength(frame)
        if s > 0:
            cx, cy = WIDTH // 2, HEART_CENTER[1] - 30
            g = ghost_sprite.copy()
            gm = int(150 * s)
            g.fill((gm, gm, gm), special_flags=pygame.BLEND_RGB_MULT)
            glow_layer.blit(g, g.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)
            b = big_sprite.copy()
            bm = int(255 * s)
            b.fill((bm, bm, bm), special_flags=pygame.BLEND_RGB_MULT)
            text_layer.blit(b, b.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)

        # cheap bloom: shrink then enlarge the glow layer, add it a few times
        small = pygame.transform.smoothscale(glow_layer, (WIDTH // 5, HEIGHT // 5))
        glow = pygame.transform.smoothscale(small, (WIDTH, HEIGHT))
        for _ in range(1):
            screen.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(text_layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        pygame.display.flip()
        clock.tick(FPS)

        if frame > TOTAL_FRAMES + 60:      # loop
            particles = make_particles()
            frame = 0

    pygame.quit()


if __name__ == "__main__":
    main()
