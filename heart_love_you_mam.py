"""
Glowing particle heart made of tiny "Love You Mam" words.

Run:
    python -m pip install pygame
    python heart_love_you_mam.py

ESC or closing the window quits. The animation loops.
"""
import math
import random

# ----------------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------------
TEXT_VARIANTS = ["Love You Mam", "LOVE YOU MAM", "love you mam", "Love you mam"]
BIG_TEXT = "Love You Mam"

WIDTH, HEIGHT = 576, 1024
FPS = 60
HEART_CENTER = (WIDTH // 2, 360)
HEART_SCALE = 13.5

N_OUTLINE = 150
N_FILL = 190
COLORS = [(25, 110, 230), (10, 130, 220), (45, 95, 225), (70, 140, 235), (20, 85, 200)]

BIG_TEXT_START = 800
BIG_TEXT_RAMP = 110
FADE_START = 1010
TOTAL_FRAMES = 1140


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
    """Return a point on the classic parametric heart curve."""
    x = 16 * math.sin(t) ** 3
    y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
          - 2 * math.cos(3 * t) - math.cos(4 * t))
    return x, y


def make_particles(seed=None):
    rnd = random.Random(seed)
    cx, cy = HEART_CENTER
    particles = []

    # Build a lookup table so outline particles are evenly spaced by arc length.
    fine = [heart_point(i / 4000 * math.tau) for i in range(4001)]
    cumulative = [0.0]
    for i in range(1, len(fine)):
        cumulative.append(
            cumulative[-1] + math.hypot(
                fine[i][0] - fine[i - 1][0], fine[i][1] - fine[i - 1][1]
            )
        )
    total_length = cumulative[-1]

    def point_at(length):
        lo, hi = 0, len(cumulative) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cumulative[mid] < length:
                lo = mid + 1
            else:
                hi = mid
        return fine[lo]

    for i in range(N_OUTLINE):
        distance = ((i + rnd.uniform(-0.3, 0.3)) / N_OUTLINE * total_length) % total_length
        hx, hy = point_at(distance)
        scale = rnd.uniform(0.95, 1.0)
        x = cx + hx * HEART_SCALE * scale + rnd.uniform(-4, 4)
        y = cy + hy * HEART_SCALE * scale + rnd.uniform(-4, 4)
        delay = 20 + (i / N_OUTLINE) * 170 + rnd.randint(0, 10)
        particles.append(Particle(
            rnd.choice(TEXT_VARIANTS), rnd.choice(COLORS), x, y, delay,
            rnd.uniform(0.75, 1.5)
        ))

    # Sample points inside a polygonal approximation of the heart.
    polygon = [heart_point(i / 240 * math.tau) for i in range(240)]

    def inside(px, py):
        hit = False
        j = len(polygon) - 1
        for i, (xi, yi) in enumerate(polygon):
            xj, yj = polygon[j]
            if (yi > py) != (yj > py):
                crossing_x = (xj - xi) * (py - yi) / (yj - yi) + xi
                if px < crossing_x:
                    hit = not hit
            j = i
        return hit

    fill = []
    while len(fill) < N_FILL:
        px = rnd.uniform(-16, 16)
        py = rnd.uniform(-13, 17)
        if inside(px, py):
            # This is sufficient for the visual effect and avoids extra pygame
            # dependencies in the particle-generation part.
            depth = min(math.hypot(px - qx, py - qy) for qx, qy in polygon)
            fill.append((px, py, depth))

    max_depth = max((depth for _, _, depth in fill), default=1.0)
    for px, py, depth in fill:
        x = cx + px * HEART_SCALE + rnd.uniform(-4, 4)
        y = cy + py * HEART_SCALE + rnd.uniform(-4, 4)
        delay = 180 + (depth / max_depth) * 480 + rnd.randint(0, 120)
        particles.append(Particle(
            rnd.choice(TEXT_VARIANTS), rnd.choice(COLORS), x, y, delay,
            rnd.uniform(0.7, 1.5)
        ))
    return particles


def step_particle(particle, frame):
    """Advance one particle and return (alpha, dx, dy)."""
    if frame > particle.delay and particle.alpha < 255:
        particle.alpha = min(255, particle.alpha + 14 + random.randint(0, 4))

    flicker = 1.0
    if particle.alpha >= 255:
        flicker = 0.75 + 0.25 * math.sin(frame * 0.04 + particle.flicker)

    fade = 1.0
    if frame > FADE_START:
        fade = max(0.0, 1.0 - (frame - FADE_START) / (TOTAL_FRAMES - FADE_START))

    alpha = int(particle.alpha * flicker * fade)
    dx = math.sin(frame * 0.02 + particle.phase) * 2.0
    dy = math.cos(frame * 0.017 + particle.phase) * 2.0
    return alpha, dx, dy


def big_text_strength(frame):
    strength = min(1.0, max(0.0, (frame - BIG_TEXT_START) / BIG_TEXT_RAMP))
    if frame > FADE_START:
        strength *= max(0.0, 1.0 - (frame - FADE_START) / (TOTAL_FRAMES - FADE_START))
    return strength


def main():
    try:
        import pygame
    except ImportError:
        raise SystemExit("pygame is not installed. Run: python -m pip install pygame")

    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Love You Mam")
        clock = pygame.time.Clock()

        background = pygame.Surface((WIDTH, HEIGHT)).convert()
        for y in range(HEIGHT):
            value = int(6 + 8 * (1 - abs(y - HEIGHT * 0.4) / (HEIGHT * 0.6)))
            pygame.draw.line(background, (2, 3, max(6, value + 4)), (0, y), (WIDTH, y))

        small_fonts = {}

        def get_font(size):
            size = max(6, int(size))
            if size not in small_fonts:
                small_fonts[size] = pygame.font.SysFont(
                    "arial,segoeui,dejavusans,sans", size, bold=True
                )
            return small_fonts[size]

        big_font = pygame.font.SysFont(
            "georgia,timesnewroman,times,dejavuserif,serif", 64, bold=True
        )
        ghost_font = pygame.font.SysFont(
            "georgia,timesnewroman,times,dejavuserif,serif", 84, bold=True
        )

        sprite_cache = {}

        def get_sprite(word, color, size, level):
            """Render text on a transparent surface with a safe alpha value."""
            key = (word, color, size, level)
            if key not in sprite_cache:
                text = get_font(size).render(word, True, color)
                sprite = pygame.Surface(text.get_size(), pygame.SRCALPHA)
                sprite.blit(text, (0, 0))
                sprite.set_alpha(int(255 * (level + 1) / 16))
                sprite_cache[key] = sprite
            return sprite_cache[key]

        big_sprite = big_font.render(BIG_TEXT, True, (255, 255, 255)).convert_alpha()
        ghost_sprite = ghost_font.render(BIG_TEXT, True, (150, 155, 170)).convert_alpha()
        glow_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        text_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        particles = make_particles()
        frame = 0
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False

            screen.blit(background, (0, 0))
            glow_layer.fill((0, 0, 0, 0))
            text_layer.fill((0, 0, 0, 0))
            frame += 1

            for particle in particles:
                alpha, dx, dy = step_particle(particle, frame)
                if alpha <= 0:
                    continue
                size = int(12 * particle.size_mult)
                sprite = get_sprite(
                    particle.word, particle.color, size, min(15, alpha // 16)
                )
                pos = (
                    int(particle.x + dx - sprite.get_width() / 2),
                    int(particle.y + dy - sprite.get_height() / 2),
                )
                text_layer.blit(sprite, pos)
                glow_layer.blit(sprite, pos)

            strength = big_text_strength(frame)
            if strength > 0:
                center = (WIDTH // 2, HEART_CENTER[1] - 30)
                ghost = ghost_sprite.copy()
                ghost.set_alpha(int(150 * strength))
                glow_layer.blit(ghost, ghost.get_rect(center=center))
                big = big_sprite.copy()
                big.set_alpha(int(255 * strength))
                text_layer.blit(big, big.get_rect(center=center))

            # Use alpha surfaces for the bloom; this works consistently across
            # pygame versions and does not turn transparent pixels black.
            small = pygame.transform.smoothscale(glow_layer, (WIDTH // 5, HEIGHT // 5))
            glow = pygame.transform.smoothscale(small, (WIDTH, HEIGHT))
            screen.blit(glow, (0, 0))
            screen.blit(text_layer, (0, 0))
            pygame.display.flip()
            clock.tick(FPS)

            if frame > TOTAL_FRAMES + 60:
                particles = make_particles()
                frame = 0
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
