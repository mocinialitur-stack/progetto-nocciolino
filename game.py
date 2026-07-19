import json
import math
from array import array
from pathlib import Path
import random
import sys

import pygame


WIDTH, HEIGHT = 1280, 720
ROAD_TOP = 145
GROUND_Y = HEIGHT - 58
FPS = 60

SKY = (138, 204, 238)
LAKE = (76, 156, 202)
HILL = (76, 143, 91)
HILL_DARK = (50, 108, 76)
GRASS = (76, 166, 83)
ROAD = (63, 67, 72)
ROAD_EDGE = (232, 202, 93)
WHITE = (248, 246, 239)
DARK = (36, 39, 48)
CAMAPARI_RED = (202, 49, 54)
SAVE_FILE = "fuga_nocciolina_records.json"
MICHELE_IMMUNITY_SECONDS = 10.0
MICHELONE_BIKE_SECONDS = 9.0
MICHELONE_SHIRTS = {
    "bike": ((246, 194, 57), "BICI TURBO", (255, 223, 88)),
    "brawl": ((222, 79, 74), "BOTTE TOTALI", (255, 112, 103)),
    "bus": ((242, 242, 238), "EPF TOURS x10", (255, 255, 255)),
    "giuseppe": ((112, 164, 218), "GIUSEPPE x5", (255, 128, 174)),
    "andrea": ((127, 194, 92), "ANDREA: -50%", (173, 235, 124)),
}


def clamp(value, low, high):
    return max(low, min(high, value))


def save_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().with_name(SAVE_FILE)
    return Path(__file__).resolve().with_name(SAVE_FILE)


def load_records():
    try:
        data = json.loads(save_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    records = []
    for item in data if isinstance(data, list) else []:
        name = str(item.get("name", "AAA")).upper()[:3].ljust(3, "A")
        try:
            score = int(item.get("score", 0))
        except (TypeError, ValueError):
            score = 0
        records.append({"name": name, "score": max(0, score)})
    return sorted(records, key=lambda row: row["score"], reverse=True)[:5]


def save_records(records):
    try:
        save_path().write_text(json.dumps(records[:5], indent=2), encoding="utf-8")
    except OSError:
        pass


def add_record(records, name, score):
    records.append({"name": name.upper()[:3].ljust(3, "A"), "score": int(score)})
    records = sorted(records, key=lambda row: row["score"], reverse=True)[:5]
    save_records(records)
    return records


def make_arcade_music():
    """Create a small looping synth track so the executable needs no audio files."""
    mixer = pygame.mixer.get_init()
    if not mixer:
        return None
    sample_rate, sample_format, channels = mixer
    if sample_format != -16:
        return None

    beat_seconds = 0.26
    melody = [659, 784, 880, 784, 659, 587, 523, 587, 659, 784, 988, 784, 659, 587, 523, 494]
    bass = [131, 131, 147, 147, 165, 165, 147, 147]
    total_beats = 64
    frame_count = int(sample_rate * beat_seconds * total_beats)
    samples = array("h")
    for frame in range(frame_count):
        time = frame / sample_rate
        beat = int(time / beat_seconds)
        in_beat = (time % beat_seconds) / beat_seconds
        note = melody[beat % len(melody)]
        low_note = bass[(beat // 2) % len(bass)]
        lead_envelope = max(0, 1 - in_beat * 1.8)
        lead = math.sin(math.tau * note * time) * 0.24 * lead_envelope
        low = math.sin(math.tau * low_note * time) * 0.18
        pulse = 0.10 if (beat % 2 == 0 and in_beat < 0.08) else 0.0
        value = int(clamp(lead + low + pulse, -0.92, 0.92) * 32767)
        for _ in range(channels):
            samples.append(value)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def make_horn_sound():
    mixer = pygame.mixer.get_init()
    if not mixer or mixer[1] != -16:
        return None
    sample_rate, _, channels = mixer
    samples = array("h")
    for frame in range(int(sample_rate * 0.42)):
        time = frame / sample_rate
        volume = 0.36 if time < 0.17 or 0.24 < time < 0.40 else 0.0
        value = int((math.sin(math.tau * 320 * time) + math.sin(math.tau * 405 * time)) * 0.5 * volume * 32767)
        for _ in range(channels):
            samples.append(value)
    return pygame.mixer.Sound(buffer=samples.tobytes())


class Peanut:
    def __init__(self):
        self.pos = pygame.Vector2()
        self.velocity = pygame.Vector2()
        self.score = 0
        self.bob = 0.0
        self.flash = 0.0
        self.facing = pygame.Vector2(1, 0)
        self.protuberance_multiplier = 1.0

    @property
    def drag_percent(self):
        return 0

    @property
    def protuberance_length(self):
        # Keep the growing effect visible without dwarfing the smaller character.
        return max(5, int(min(10 + self.score * 9, 96) * self.protuberance_multiplier))

    def shorten_protuberance(self):
        self.protuberance_multiplier *= 0.5

    @property
    def hitbox(self):
        width = 28 + self.protuberance_length
        return pygame.Rect(int(self.pos.x - 14), int(self.pos.y - 25), int(width), 50)

    def update(self, dt, keys, speed_multiplier=1.0):
        movement = pygame.Vector2(
            (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0)
            - (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0),
            (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0)
            - (1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0),
        )
        if movement.length_squared() > 0:
            movement = movement.normalize()
            if movement.x != 0:
                self.facing = pygame.Vector2(1 if movement.x > 0 else -1, 0)

        top_speed = 355 * speed_multiplier
        acceleration = 1700 * speed_multiplier
        desired = movement * top_speed
        self.velocity = self.velocity.move_towards(desired, acceleration * dt)
        if movement.length_squared() == 0:
            self.velocity = self.velocity.move_towards(pygame.Vector2(), 1100 * dt)

        self.pos += self.velocity * dt
        self.bob += dt * (7 + self.velocity.length() / 90)
        self.flash = max(0, self.flash - dt)

    def draw(self, surface, camera, on_bike=False):
        screen_x = int(self.pos.x - camera.x)
        screen_y = int(self.pos.y - camera.y + math.sin(self.bob) * 3)
        target_surface = surface
        surface = pygame.Surface((320, 200), pygame.SRCALPHA)
        x, y = 150, 100
        # Same visual scale as the chasing women, with a recognisable silhouette.
        s = 0.40
        shell = (222, 154, 91)
        shell_dark = (123, 71, 34)
        shell_line = (245, 197, 128)

        def p(px, py):
            return (int(x + px * s), int(y + py * s))

        def scaled_rect(px, py, w, h):
            return pygame.Rect(int(x + px * s), int(y + py * s), int(w * s), int(h * s))

        if on_bike:
            tire = (25, 28, 32)
            frame = (246, 194, 57)
            pygame.draw.circle(surface, tire, p(-27, 38), 10, 3)
            pygame.draw.circle(surface, tire, p(27, 38), 10, 3)
            pygame.draw.line(surface, frame, p(-27, 38), p(-4, 18), 3)
            pygame.draw.line(surface, frame, p(27, 38), p(-4, 18), 3)
            pygame.draw.line(surface, frame, p(-9, 38), p(-4, 18), 3)
            pygame.draw.line(surface, frame, p(-9, 38), p(27, 38), 3)
            pygame.draw.line(surface, frame, p(-4, 18), p(11, 11), 3)
            pygame.draw.line(surface, frame, p(11, 11), p(28, 13), 2)

        # Lower, compact arms keep the sprite readable at its smaller scale.
        pygame.draw.line(surface, shell_dark, p(-23, -8), p(-48, -18), 4)
        pygame.draw.line(surface, shell_dark, p(23, -8), p(48, -18), 4)
        pygame.draw.circle(surface, WHITE, p(-55, -19), 7)
        pygame.draw.circle(surface, WHITE, p(55, -19), 7)
        for offset in (-12, 0, 12):
            pygame.draw.line(surface, WHITE, p(-55, -19), p(-65 + offset * 0.32, -29 - abs(offset) * 0.14), 3)
            pygame.draw.line(surface, WHITE, p(55, -19), p(65 - offset * 0.32, -29 - abs(offset) * 0.14), 3)

        # Legs and shoes
        pygame.draw.line(surface, DARK, p(-13, 47), p(-19, 61), 5)
        pygame.draw.line(surface, DARK, p(13, 47), p(19, 61), 5)
        pygame.draw.ellipse(surface, WHITE, scaled_rect(-31, 58, 22, 9))
        pygame.draw.ellipse(surface, WHITE, scaled_rect(9, 58, 22, 9))

        # Peanut shell body, with lattice lines and a small top stem.
        body = scaled_rect(-33, -67, 66, 126)
        pygame.draw.ellipse(surface, shell, body)
        pygame.draw.ellipse(surface, shell_dark, body, 4)
        pygame.draw.arc(surface, shell_dark, scaled_rect(-15, -79, 30, 34), math.pi, math.tau, 5)
        for dx in (-20, 0, 20):
            pygame.draw.arc(surface, shell_line, scaled_rect(dx - 26, -61, 52, 116), math.radians(76), math.radians(284), 3)
        for yy in range(y - 48, y + 46, 24):
            pygame.draw.arc(surface, shell_line, pygame.Rect(int(x - 34 * s), int(y + (yy - y - 11) * s), int(68 * s), int(25 * s)), math.radians(8), math.radians(172), 3)

        length = self.protuberance_length
        protuberance = pygame.Rect(int(x + 20 * s), int(y + 7 * s), int(length), 11)
        skin_outline = (183, 105, 103)
        skin_pink = (238, 171, 162)
        skin_highlight = (255, 211, 202)
        pygame.draw.rect(surface, skin_outline, protuberance.inflate(2, 2), border_radius=7)
        pygame.draw.circle(surface, skin_outline, (protuberance.right, protuberance.centery), 7)
        pygame.draw.rect(surface, skin_pink, protuberance, border_radius=6)
        pygame.draw.circle(surface, skin_pink, (protuberance.right, protuberance.centery), 6)
        pygame.draw.line(surface, skin_highlight, (protuberance.left + 5, protuberance.centery - 3), (protuberance.right - 5, protuberance.centery - 3), 2)

        # Big eyes, eyebrows, smile, and open mouth.
        pygame.draw.ellipse(surface, WHITE, scaled_rect(-28, -55, 29, 44))
        pygame.draw.ellipse(surface, WHITE, scaled_rect(1, -55, 29, 44))
        pygame.draw.ellipse(surface, DARK, scaled_rect(-28, -55, 29, 44), 2)
        pygame.draw.ellipse(surface, DARK, scaled_rect(1, -55, 29, 44), 2)
        for eye_x in (-12, 15):
            pygame.draw.circle(surface, (112, 71, 8), p(eye_x, -31), 5)
            pygame.draw.circle(surface, (235, 196, 45), p(eye_x - 2, -32), 3)
            pygame.draw.circle(surface, DARK, p(eye_x + 1, -28), 2)
            pygame.draw.circle(surface, WHITE, p(eye_x - 3, -35), 2)
        pygame.draw.arc(surface, shell_dark, scaled_rect(-22, -66, 22, 12), math.pi, math.tau, 2)
        pygame.draw.arc(surface, shell_dark, scaled_rect(2, -66, 22, 12), math.pi, math.tau, 2)
        pygame.draw.arc(surface, DARK, scaled_rect(-22, -22, 44, 30), 0, math.pi, 3)
        pygame.draw.ellipse(surface, (116, 33, 49), scaled_rect(8, -4, 15, 28))
        pygame.draw.rect(surface, WHITE, scaled_rect(-20, -18, 40, 9), border_radius=4)
        if self.flash > 0:
            pygame.draw.circle(surface, WHITE, (x, y - 5), 38, 3)

        mirrored = pygame.transform.flip(surface, self.facing.x < 0, False)
        target_surface.blit(mirrored, mirrored.get_rect(center=(screen_x, screen_y)))


class Chaser:
    def __init__(self, level, origin):
        direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.pos = pygame.Vector2(origin) + direction.normalize() * random.randint(510, 760)
        self.speed = random.randint(102, 132) + level * 13
        self.phase = random.random() * math.tau
        self.scale = 0.68
        self.hair = random.choice([(65, 37, 29), (129, 73, 39), (37, 29, 31), (206, 166, 77)])
        self.dress = random.choice([(233, 91, 112), (119, 88, 206), (47, 154, 142), (239, 137, 54)])

    @property
    def hitbox(self):
        return pygame.Rect(int(self.pos.x - 15), int(self.pos.y - 27), 30, 54)

    def update(self, dt, target):
        direction = target.pos - self.pos
        if direction.length_squared() > 0:
            self.pos += direction.normalize() * self.speed * dt
        self.phase += dt * 9

    def draw(self, surface, camera):
        x = int(self.pos.x - camera.x)
        y = int(self.pos.y - camera.y + math.sin(self.phase) * 2)
        s = self.scale

        def p(px, py):
            return (int(x + px * s), int(y + py * s))

        pygame.draw.line(surface, DARK, p(-8, 24), p(-12, 39), max(3, int(5 * s)))
        pygame.draw.line(surface, DARK, p(8, 24), p(12, 39), max(3, int(5 * s)))
        pygame.draw.polygon(surface, self.dress, [p(-18, -4), p(18, -4), p(24, 27), p(-24, 27)])
        pygame.draw.circle(surface, (241, 193, 157), p(0, -19), int(16 * s))
        pygame.draw.arc(surface, self.hair, pygame.Rect(p(-18, -37), (int(36 * s), int(33 * s))), math.pi, math.tau, max(4, int(8 * s)))
        pygame.draw.line(surface, (241, 193, 157), p(-15, 1), p(-29, 13), max(3, int(5 * s)))
        pygame.draw.line(surface, (241, 193, 157), p(15, 1), p(29, 13), max(3, int(5 * s)))


class SpecialEffect:
    def __init__(self, pos, label, color, ttl=1.0):
        self.pos = pygame.Vector2(pos)
        self.label = label
        self.color = color
        self.ttl = ttl
        self.max_ttl = ttl

    def update(self, dt):
        self.ttl -= dt
        self.pos.y -= 32 * dt

    def draw(self, surface, font, camera):
        progress = 1 - max(0, self.ttl) / self.max_ttl
        radius = int(12 + progress * 28)
        alpha = int(255 * min(1, self.ttl * 2))
        burst = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        center = radius + 4
        for angle in range(0, 360, 45):
            vector = pygame.Vector2(1, 0).rotate(angle)
            pygame.draw.line(burst, (*self.color, alpha), (center, center), (center + vector.x * radius, center + vector.y * radius), 3)
        x, y = int(self.pos.x - camera.x), int(self.pos.y - camera.y)
        surface.blit(burst, (x - center, y - center))
        label = font.render(self.label, True, self.color)
        surface.blit(label, label.get_rect(center=(x, y - radius - 13)))


class BloodStain:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.ttl = 14.0

    def update(self, dt):
        self.ttl -= dt

    def draw(self, surface, camera):
        if self.ttl <= 0:
            return
        x, y = int(self.pos.x - camera.x), int(self.pos.y - camera.y)
        pygame.draw.line(surface, (114, 23, 28), (x - 29, y + 12), (x + 35, y - 10), 8)
        pygame.draw.line(surface, (181, 37, 40), (x - 24, y + 14), (x + 28, y - 5), 4)
        pygame.draw.circle(surface, (155, 30, 35), (x + 39, y - 12), 5)


class EPFToursBus:
    def __init__(self, origin, quota):
        spawn_direction = pygame.Vector2(random.choice((-1, 1)), random.uniform(-0.35, 0.35))
        self.pos = pygame.Vector2(origin) + spawn_direction.normalize() * 820
        self.origin = pygame.Vector2(origin)
        self.facing = -spawn_direction.normalize()
        self.target = None
        self.quota = quota
        self.kills = 0
        self.leaving = False

    @property
    def done(self):
        return self.leaving and self.pos.distance_to(self.origin) > 1450

    def update(self, dt, chasers):
        casualties = []
        if not self.leaving:
            if self.kills >= self.quota or not chasers:
                self.leaving = True
            else:
                if self.target not in chasers:
                    self.target = min(chasers, key=lambda chaser: chaser.pos.distance_squared_to(self.pos))
                direction = self.target.pos - self.pos
                if direction.length_squared() > 0:
                    self.facing = direction.normalize()
                    self.pos += self.facing * 720 * dt
                if self.pos.distance_to(self.target.pos) < 58:
                    casualties.append(self.target.pos.copy())
                    chasers.remove(self.target)
                    self.target = None
                    self.kills += 1
        else:
            self.pos += self.facing * 720 * dt
        return casualties

    def draw(self, surface, camera, font):
        bus = pygame.Surface((150, 70), pygame.SRCALPHA)
        pygame.draw.rect(bus, (247, 247, 243), (8, 12, 132, 46), border_radius=8)
        pygame.draw.rect(bus, (57, 104, 162), (12, 16, 128, 14), border_radius=4)
        pygame.draw.rect(bus, (45, 50, 57), (14, 46, 20, 11), border_radius=3)
        pygame.draw.rect(bus, (45, 50, 57), (112, 46, 20, 11), border_radius=3)
        label = font.render("EPF TOURS", True, (35, 74, 122))
        bus.blit(label, label.get_rect(center=(76, 39)))
        angle = -pygame.Vector2(1, 0).angle_to(self.facing)
        rotated = pygame.transform.rotate(bus, angle)
        x, y = int(self.pos.x - camera.x), int(self.pos.y - camera.y)
        surface.blit(rotated, rotated.get_rect(center=(x, y)))


class Giuseppe:
    def __init__(self, origin):
        self.origin = pygame.Vector2(origin)
        self.pos = self.origin + pygame.Vector2(-780, random.randint(-260, 260))
        self.home = self.origin + pygame.Vector2(820, -480)
        self.target = None
        self.rescued = 0
        self.state = "arriving"

    @property
    def done(self):
        return self.state == "home" and self.pos.distance_to(self.home) < 20

    def update(self, dt, chasers):
        loves = []
        if self.state == "arriving":
            if self.rescued >= 5 or not chasers:
                self.state = "home"
            else:
                if self.target not in chasers:
                    self.target = min(chasers, key=lambda chaser: chaser.pos.distance_squared_to(self.pos))
                direction = self.target.pos - self.pos
                if direction.length_squared() > 0:
                    self.pos += direction.normalize() * 440 * dt
                if self.pos.distance_to(self.target.pos) < 40:
                    loves.append(self.target.pos.copy())
                    chasers.remove(self.target)
                    self.target = None
                    self.rescued += 1
        else:
            direction = self.home - self.pos
            if direction.length_squared() > 0:
                self.pos += direction.normalize() * 440 * dt
        return loves

    def draw(self, surface, camera, font):
        home_x, home_y = int(self.home.x - camera.x), int(self.home.y - camera.y)
        if -100 < home_x < WIDTH + 100 and -100 < home_y < HEIGHT + 100:
            pygame.draw.rect(surface, (216, 178, 127), (home_x - 30, home_y - 4, 60, 42))
            pygame.draw.polygon(surface, (130, 64, 44), [(home_x - 38, home_y - 4), (home_x, home_y - 28), (home_x + 38, home_y - 4)])
            text(surface, font, "CASA DI GIUSEPPE", (home_x, home_y + 52), (255, 182, 211), "center")
        x, y = int(self.pos.x - camera.x), int(self.pos.y - camera.y)
        pygame.draw.circle(surface, (231, 177, 135), (x, y - 22), 14)
        pygame.draw.arc(surface, (63, 40, 30), (x - 16, y - 39, 32, 25), math.pi, math.tau, 5)
        pygame.draw.rect(surface, (88, 124, 214), (x - 17, y - 8, 34, 34), border_radius=6)
        pygame.draw.line(surface, (231, 177, 135), (x - 15, y + 2), (x - 31, y + 14), 4)
        pygame.draw.line(surface, (231, 177, 135), (x + 15, y + 2), (x + 31, y + 14), 4)
        text(surface, font, "GIUSEPPE", (x, y - 50), (255, 182, 211), "center")


class FabioCamicia:
    def __init__(self, origin):
        direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.pos = pygame.Vector2(origin) + direction.normalize() * random.randint(300, 500)
        self.phase = random.random() * math.tau
        self.ttl = 10.0

    @property
    def hitbox(self):
        return pygame.Rect(int(self.pos.x - 28), int(self.pos.y - 44), 56, 88)

    def update(self, dt):
        self.phase += dt * 5
        self.ttl -= dt

    def draw(self, surface, camera, font):
        x = int(self.pos.x - camera.x)
        y = int(self.pos.y - camera.y + math.sin(self.phase) * 2)
        glow = pygame.Surface((112, 112), pygame.SRCALPHA)
        pygame.draw.circle(glow, (82, 217, 255, 62), (56, 56), 46)
        surface.blit(glow, (x - 56, y - 56))
        pygame.draw.circle(surface, (238, 185, 145), (x, y - 26), 15)
        pygame.draw.arc(surface, (65, 43, 29), (x - 16, y - 43, 32, 24), math.pi, math.tau, 5)
        pygame.draw.rect(surface, (245, 248, 242), (x - 21, y - 10, 42, 41), border_radius=7)
        pygame.draw.line(surface, (78, 170, 205), (x, y - 7), (x, y + 28), 3)
        pygame.draw.line(surface, (238, 185, 145), (x - 18, y), (x - 36, y + 15), 4)
        pygame.draw.line(surface, (238, 185, 145), (x + 18, y), (x + 36, y + 15), 4)
        text(surface, font, "FABIO CAMICIA", (x, y - 61), (100, 222, 255), "center")


class Spritz:
    def __init__(self, origin):
        direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.pos = pygame.Vector2(origin) + direction.normalize() * random.randint(170, 430)
        self.phase = random.random() * math.tau

    @property
    def hitbox(self):
        return pygame.Rect(int(self.pos.x - 20), int(self.pos.y - 29), 40, 58)

    def update(self, dt):
        self.phase += dt * 4

    def draw(self, surface, camera):
        x = int(self.pos.x - camera.x)
        y = int(self.pos.y - camera.y + math.sin(self.phase) * 5)
        glow = pygame.Surface((70, 85), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 225, 89, 80), (35, 39), 32)
        surface.blit(glow, (x - 35, y - 42))
        pygame.draw.polygon(surface, WHITE, [(x - 14, y - 27), (x + 14, y - 27), (x + 8, y + 12), (x - 8, y + 12)])
        pygame.draw.polygon(surface, CAMAPARI_RED, [(x - 11, y - 9), (x + 11, y - 9), (x + 7, y + 9), (x - 7, y + 9)])
        pygame.draw.line(surface, WHITE, (x, y + 12), (x, y + 28), 3)
        pygame.draw.line(surface, WHITE, (x - 11, y + 28), (x + 11, y + 28), 3)
        pygame.draw.circle(surface, (255, 169, 66), (x + 5, y - 16), 4)


class Michelone:
    def __init__(self, origin):
        direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.pos = pygame.Vector2(origin) + direction.normalize() * random.randint(320, 520)
        self.phase = random.random() * math.tau
        self.ttl = 9.0
        self.power = random.choice(tuple(MICHELONE_SHIRTS))
        self.state = "available"
        self.kills = 0
        self.target = None
        self.brawl_timer = 0.0
        self.cries = False
        self.exit_direction = -1 if random.random() < 0.5 else 1

    @property
    def hitbox(self):
        return pygame.Rect(int(self.pos.x - 46), int(self.pos.y - 42), 92, 84)

    def update(self, dt, chasers):
        self.phase += dt * 5
        impacts = []
        if self.state == "available":
            self.ttl -= dt
        elif self.state == "brawl":
            self.brawl_timer -= dt
            if self.brawl_timer <= 0 or not chasers:
                self.start_crying()
            else:
                if self.target not in chasers:
                    self.target = min(chasers, key=lambda chaser: chaser.pos.distance_squared_to(self.pos))
                direction = self.target.pos - self.pos
                if direction.length_squared() > 0:
                    self.pos += direction.normalize() * 460 * dt
                if self.pos.distance_to(self.target.pos) < 32:
                    impacts.append(self.target.pos.copy())
                    chasers.remove(self.target)
                    self.target = None
                    self.kills += 1
        elif self.state == "crying":
            self.pos.x += self.exit_direction * 290 * dt
        return impacts

    def start_brawl(self):
        self.state = "brawl"
        self.ttl = 0
        self.brawl_timer = 9.0

    def start_crying(self, cries=False):
        self.state = "crying"
        self.target = None
        self.cries = cries

    def draw(self, surface, font, camera):
        x = int(self.pos.x - camera.x)
        y = int(self.pos.y - camera.y + math.sin(self.phase) * 2)
        glow = pygame.Surface((132, 116), pygame.SRCALPHA)
        pygame.draw.circle(glow, (80, 198, 255, 58), (66, 58), 52)
        surface.blit(glow, (x - 66, y - 58))

        tire = (25, 28, 32)
        frame = (36, 106, 174)
        skin = (235, 180, 142)
        shirt, power_name, glow_color = MICHELONE_SHIRTS[self.power]

        pygame.draw.circle(surface, tire, (x - 35, y + 24), 18, 4)
        pygame.draw.circle(surface, tire, (x + 37, y + 24), 18, 4)
        pygame.draw.line(surface, frame, (x - 35, y + 24), (x - 2, y + 2), 4)
        pygame.draw.line(surface, frame, (x + 37, y + 24), (x - 2, y + 2), 4)
        pygame.draw.line(surface, frame, (x - 8, y + 24), (x - 2, y + 2), 4)
        pygame.draw.line(surface, frame, (x - 8, y + 24), (x + 37, y + 24), 4)
        pygame.draw.line(surface, frame, (x - 2, y + 2), (x + 10, y - 15), 4)
        pygame.draw.line(surface, frame, (x + 10, y - 15), (x + 36, y - 8), 3)

        pygame.draw.ellipse(surface, shirt, (x - 25, y - 37, 50, 47))
        pygame.draw.ellipse(surface, glow_color, (x - 27, y - 35, 54, 50), 3)
        pygame.draw.circle(surface, skin, (x, y - 51), 17)
        pygame.draw.arc(surface, (68, 40, 28), (x - 18, y - 69, 36, 29), math.pi, math.tau, 6)
        pygame.draw.circle(surface, DARK, (x - 6, y - 52), 2)
        pygame.draw.circle(surface, DARK, (x + 6, y - 52), 2)
        if self.state == "crying" and self.cries:
            pygame.draw.line(surface, (73, 183, 245), (x - 7, y - 47), (x - 9, y - 38), 2)
            pygame.draw.line(surface, (73, 183, 245), (x + 7, y - 47), (x + 9, y - 38), 2)
            pygame.draw.arc(surface, DARK, (x - 7, y - 44, 14, 10), math.pi, math.tau, 2)
        else:
            pygame.draw.arc(surface, DARK, (x - 7, y - 48, 14, 10), 0, math.pi, 2)
        pygame.draw.line(surface, skin, (x - 20, y - 15), (x - 41, y + 6), 5)
        pygame.draw.line(surface, skin, (x + 20, y - 15), (x + 37, y - 8), 5)
        pygame.draw.line(surface, DARK, (x - 11, y + 6), (x - 27, y + 22), 5)
        pygame.draw.line(surface, DARK, (x + 11, y + 6), (x + 19, y + 23), 5)

        visitor_name = {
            "andrea": "ANDREA FRILICCA",
            "giuseppe": "GIUSEPPE",
        }.get(self.power, "MICHELONE")
        label_text = visitor_name if self.state == "available" else ("BAM!" if self.state == "brawl" else ("SOB..." if self.cries else "CIAO!"))
        label = font.render(label_text, True, WHITE)
        bg = label.get_rect(center=(x, y - 86)).inflate(18, 8)
        pygame.draw.rect(surface, (26, 61, 87) if self.state == "available" else DARK, bg, border_radius=5)
        surface.blit(label, label.get_rect(center=bg.center))
        if self.state == "available":
            detail = font.render(power_name, True, glow_color)
            surface.blit(detail, detail.get_rect(center=(x, y - 67)))


def make_michelone(peanut):
    michelone = Michelone(peanut.pos)
    while michelone.pos.distance_to(peanut.pos) < 210:
        michelone = Michelone(peanut.pos)
    return michelone


def make_fabio(peanut):
    fabio = FabioCamicia(peanut.pos)
    while fabio.pos.distance_to(peanut.pos) < 210:
        fabio = FabioCamicia(peanut.pos)
    return fabio


def draw_background(surface, camera, font):
    """Render an endless, camera-relative Montefiascone street map."""
    surface.fill((113, 177, 103))
    road_x_spacing, road_y_spacing = 720, 520
    road_width = 150
    street_names = (
        "Via Cassia", "Via della Rocca", "Via Verentana", "Corso Cavour",
        "Via Indipendenza", "Via delle Logge", "Via S. Lucia Filippini", "Via 24 Maggio",
    )

    first_x = math.floor((camera.x - road_width) / road_x_spacing) * road_x_spacing
    first_y = math.floor((camera.y - road_width) / road_y_spacing) * road_y_spacing
    vertical_roads = range(int(first_x), int(camera.x + WIDTH + road_width), road_x_spacing)
    horizontal_roads = range(int(first_y), int(camera.y + HEIGHT + road_width), road_y_spacing)

    # City blocks: deterministic houses and trees make every explored quarter stable.
    block_size = 180
    start_block_x = math.floor(camera.x / block_size) - 1
    start_block_y = math.floor(camera.y / block_size) - 1
    for block_x in range(start_block_x, start_block_x + WIDTH // block_size + 3):
        for block_y in range(start_block_y, start_block_y + HEIGHT // block_size + 3):
            world_x, world_y = block_x * block_size, block_y * block_size
            local_x = world_x % road_x_spacing
            local_y = world_y % road_y_spacing
            if local_x < road_width or local_y < road_width:
                continue
            seed = (block_x * 73856093) ^ (block_y * 19349663)
            width = 48 + abs(seed) % 45
            height = 42 + abs(seed // 7) % 48
            x, y = int(world_x - camera.x + 28), int(world_y - camera.y + 32)
            wall = ((191 + abs(seed) % 28), (142 + abs(seed // 11) % 32), (98 + abs(seed // 17) % 26))
            pygame.draw.rect(surface, wall, (x, y, width, height), border_radius=3)
            pygame.draw.polygon(surface, (128, 65, 45), [(x - 5, y), (x + width // 2, y - 19), (x + width + 5, y)])
            pygame.draw.rect(surface, (73, 91, 92), (x + width // 2 - 5, y + height - 16, 10, 16))
            if seed % 3 == 0:
                pygame.draw.circle(surface, (49, 122, 68), (x - 12, y + height - 4), 13)

    for world_x in vertical_roads:
        x = int(world_x - camera.x)
        pygame.draw.rect(surface, (211, 203, 181), (x - 10, 0, road_width + 20, HEIGHT))
        pygame.draw.rect(surface, ROAD, (x, 0, road_width, HEIGHT))
        pygame.draw.line(surface, ROAD_EDGE, (x + 4, 0), (x + 4, HEIGHT), 4)
        pygame.draw.line(surface, ROAD_EDGE, (x + road_width - 4, 0), (x + road_width - 4, HEIGHT), 4)
        for marker_y in range(int(math.floor(camera.y / 92) * 92), int(camera.y + HEIGHT + 92), 92):
            y = int(marker_y - camera.y)
            pygame.draw.rect(surface, (231, 231, 217), (x + road_width // 2 - 3, y, 6, 43), border_radius=3)

    for world_y in horizontal_roads:
        y = int(world_y - camera.y)
        pygame.draw.rect(surface, (211, 203, 181), (0, y - 10, WIDTH, road_width + 20))
        pygame.draw.rect(surface, ROAD, (0, y, WIDTH, road_width))
        pygame.draw.line(surface, ROAD_EDGE, (0, y + 4), (WIDTH, y + 4), 4)
        pygame.draw.line(surface, ROAD_EDGE, (0, y + road_width - 4), (WIDTH, y + road_width - 4), 4)
        for marker_x in range(int(math.floor(camera.x / 92) * 92), int(camera.x + WIDTH + 92), 92):
            x = int(marker_x - camera.x)
            pygame.draw.rect(surface, (231, 231, 217), (x, y + road_width // 2 - 3, 43, 6), border_radius=3)

    for x_index, world_x in enumerate(vertical_roads):
        for y_index, world_y in enumerate(horizontal_roads):
            x, y = int(world_x - camera.x), int(world_y - camera.y)
            pygame.draw.rect(surface, (87, 91, 96), (x, y, road_width, road_width))
            name = street_names[(world_x // road_x_spacing + world_y // road_y_spacing) % len(street_names)]
            sign = pygame.Rect(x + 12, y + 12, 126, 25)
            pygame.draw.rect(surface, (242, 238, 202), sign, border_radius=4)
            pygame.draw.rect(surface, (100, 70, 37), sign, 2, border_radius=4)
            text(surface, font, name, sign.center, (80, 55, 35), "center")

    landmarks = (
        (0, -300, "ROCCA DEI PAPI", "rocca"),
        (560, 80, "CATTEDRALE S. MARGHERITA", "cupola"),
        (-610, 220, "BASILICA S. FLAVIANO", "basilica"),
        (-80, 540, "PIAZZA S. MARGHERITA", "piazza"),
        (720, -430, "LARGO DEL PLEBISCITO", "piazza"),
    )
    for world_x, world_y, label, kind in landmarks:
        x, y = int(world_x - camera.x), int(world_y - camera.y)
        if not (-180 < x < WIDTH + 180 and -180 < y < HEIGHT + 180):
            continue
        if kind == "rocca":
            pygame.draw.rect(surface, (143, 112, 80), (x - 48, y - 25, 96, 62))
            pygame.draw.rect(surface, (112, 84, 61), (x - 62, y - 36, 26, 73))
            pygame.draw.rect(surface, (112, 84, 61), (x + 36, y - 36, 26, 73))
            for tower_x in (x - 62, x - 35, x + 35):
                pygame.draw.rect(surface, (94, 70, 55), (tower_x, y - 47, 13, 15))
        elif kind == "cupola":
            pygame.draw.rect(surface, (224, 192, 148), (x - 47, y - 16, 94, 54))
            pygame.draw.arc(surface, (96, 139, 153), (x - 38, y - 67, 76, 72), math.pi, math.tau, 12)
            pygame.draw.rect(surface, (178, 131, 89), (x - 6, y - 79, 12, 24))
        elif kind == "basilica":
            pygame.draw.rect(surface, (203, 171, 132), (x - 52, y - 12, 104, 50))
            pygame.draw.polygon(surface, (130, 67, 48), [(x - 58, y - 12), (x, y - 48), (x + 58, y - 12)])
            for arch_x in (-26, 0, 26):
                pygame.draw.arc(surface, (83, 71, 62), (x + arch_x - 9, y + 10, 18, 22), math.pi, math.tau, 3)
        else:
            pygame.draw.circle(surface, (205, 193, 158), (x, y + 15), 58)
            pygame.draw.circle(surface, (113, 155, 185), (x, y + 15), 18)
        plate = pygame.Rect(x - 90, y + 48, 180, 25)
        pygame.draw.rect(surface, (42, 65, 77), plate, border_radius=4)
        text(surface, font, label, plate.center, WHITE, "center")


def text(surface, font, value, pos, color=WHITE, anchor="topleft"):
    image = font.render(value, True, color)
    rect = image.get_rect(**{anchor: pos})
    surface.blit(image, rect)


def draw_campari_arrow(surface, peanut, bonus, font):
    direction = bonus.pos - peanut.pos
    if direction.length_squared() == 0:
        return
    direction = direction.normalize()
    distance = bonus.pos.distance_to(peanut.pos)
    radius = min(285, max(85, distance))
    center = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
    arrow_center = center + direction * radius
    perpendicular = pygame.Vector2(-direction.y, direction.x)
    tip = arrow_center + direction * 20
    tail = arrow_center - direction * 18
    points = [tip, tail + perpendicular * 15, tail + perpendicular * 5, tail - perpendicular * 5, tail - perpendicular * 15]
    pygame.draw.polygon(surface, (255, 222, 88), points)
    pygame.draw.polygon(surface, (96, 66, 28), points, 2)
    label_pos = arrow_center - direction * 31
    text(surface, font, "CAMPARI", (int(label_pos.x), int(label_pos.y)), (255, 239, 151), "center")


def reset_game():
    peanut = Peanut()
    chasers = [Chaser(0, peanut.pos)]
    bonus = Spritz(peanut.pos)
    michelone = None
    michelone_timer = random.uniform(8.0, 15.0)
    fabio = None
    fabio_timer = random.uniform(12.0, 20.0)
    immunity_timer = 0.0
    bike_timer = 0.0
    chaser_timer = random.uniform(7.0, 12.0)
    return peanut, chasers, bonus, michelone, michelone_timer, fabio, fabio_timer, immunity_timer, bike_timer, chaser_timer


def main():
    pygame.mixer.pre_init(22050, -16, 2, 512)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fuga della Nocciolina")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 34, bold=True)
    ui_font = pygame.font.SysFont("arial", 23, bold=True)
    small_font = pygame.font.SysFont("arial", 18)
    arcade_font = pygame.font.SysFont("consolas", 38, bold=True)
    music = make_arcade_music()
    if music is not None:
        music.set_volume(0.24)
        music.play(-1)
    horn_sound = make_horn_sound()

    records = load_records()
    name_input = ""
    final_score = 0
    peanut, chasers, bonus, michelone, michelone_timer, fabio, fabio_timer, immunity_timer, bike_timer, chaser_timer = reset_game()
    effects = []
    blood_stains = []
    buses = []
    giuseppe = None
    state = "intro"
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if state == "name_entry":
                    if event.key == pygame.K_BACKSPACE:
                        name_input = name_input[:-1]
                    elif event.key == pygame.K_RETURN and len(name_input) == 3:
                        records = add_record(records, name_input, final_score)
                        state = "game_over"
                    elif len(name_input) < 3 and event.unicode and event.unicode.isalnum():
                        name_input += event.unicode.upper()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and state in ("intro", "game_over"):
                    peanut, chasers, bonus, michelone, michelone_timer, fabio, fabio_timer, immunity_timer, bike_timer, chaser_timer = reset_game()
                    effects = []
                    blood_stains = []
                    buses = []
                    giuseppe = None
                    state = "playing"

        keys = pygame.key.get_pressed()
        if state == "playing":
            peanut.update(dt, keys, 1.62 if bike_timer > 0 else 1.0)
            bonus.update(dt)
            immunity_timer = max(0.0, immunity_timer - dt)
            bike_timer = max(0.0, bike_timer - dt)
            for chaser in chasers:
                chaser.update(dt, peanut)

            chaser_timer -= dt
            if chaser_timer <= 0:
                chasers.append(Chaser(peanut.score, peanut.pos))
                chaser_timer = random.uniform(7.0, 12.0)

            if immunity_timer > 0:
                for chaser in chasers:
                    away = chaser.pos - peanut.pos
                    distance = away.length()
                    if distance < 235:
                        if distance == 0:
                            away = pygame.Vector2(1, 0)
                            distance = 1
                        strength = 180 + 720 * (1 - distance / 235)
                        chaser.pos += away.normalize() * strength * dt

            if fabio is None:
                fabio_timer -= dt
                if fabio_timer <= 0:
                    fabio = make_fabio(peanut)
            else:
                fabio.update(dt)
                if peanut.hitbox.colliderect(fabio.hitbox):
                    immunity_timer = MICHELE_IMMUNITY_SECONDS
                    peanut.flash = 1.1
                    effects.append(SpecialEffect(peanut.pos, "FORZA!", (82, 217, 255), 1.3))
                    fabio = None
                    fabio_timer = random.uniform(14.0, 24.0)
                elif fabio.ttl <= 0:
                    fabio = None
                    fabio_timer = random.uniform(12.0, 20.0)

            if michelone is None:
                michelone_timer -= dt
                if michelone_timer <= 0:
                    michelone = make_michelone(peanut)
            else:
                impacts = michelone.update(dt, chasers)
                for impact in impacts:
                    effects.append(SpecialEffect(impact, "BAM!", (255, 108, 96), 0.8))

                if michelone.state == "available" and peanut.hitbox.colliderect(michelone.hitbox):
                    power = michelone.power
                    peanut.flash = 1.1
                    if power == "bike":
                        bike_timer = MICHELONE_BIKE_SECONDS
                        effects.append(SpecialEffect(peanut.pos, "BICI RUBATA!", MICHELONE_SHIRTS[power][2], 1.25))
                        michelone.start_crying(True)
                    elif power == "brawl":
                        effects.append(SpecialEffect(michelone.pos, "MICHELONE ATTACCA!", MICHELONE_SHIRTS[power][2], 1.1))
                        michelone.start_brawl()
                    elif power == "bus":
                        buses.extend((EPFToursBus(peanut.pos, 5), EPFToursBus(peanut.pos, 5)))
                        effects.append(SpecialEffect(peanut.pos, "EPF TOURS IN ARRIVO!", MICHELONE_SHIRTS[power][2], 1.3))
                        if horn_sound is not None:
                            horn_sound.play()
                        michelone.start_crying()
                    elif power == "giuseppe":
                        giuseppe = Giuseppe(peanut.pos)
                        effects.append(SpecialEffect(peanut.pos, "GIUSEPPE ARRIVA!", MICHELONE_SHIRTS[power][2], 1.3))
                        michelone.start_crying()
                    else:
                        peanut.shorten_protuberance()
                        effects.append(SpecialEffect(peanut.pos, "ANDREA: -50%!", MICHELONE_SHIRTS[power][2], 1.3))
                        michelone.start_crying()
                elif michelone.state == "available" and michelone.ttl <= 0:
                    michelone.start_crying()

                if michelone.state == "crying" and michelone.pos.distance_to(peanut.pos) > 1400:
                    michelone = None
                    michelone_timer = random.uniform(10.0, 20.0)

            if peanut.hitbox.colliderect(bonus.hitbox):
                peanut.score += 1
                peanut.flash = 0.35
                bonus = Spritz(peanut.pos)
                # Avoid respawning directly on the runner.
                while bonus.pos.distance_to(peanut.pos) < 170:
                    bonus = Spritz(peanut.pos)
                chasers.append(Chaser(peanut.score, peanut.pos))

            for bus in buses:
                casualties = bus.update(dt, chasers)
                for casualty in casualties:
                    blood_stains.append(BloodStain(casualty))
                    effects.append(SpecialEffect(casualty, "SBAM!", (226, 52, 54), 0.9))
            buses = [bus for bus in buses if not bus.done]

            if giuseppe is not None:
                loves = giuseppe.update(dt, chasers)
                for love in loves:
                    effects.append(SpecialEffect(love, "AMORE!", (255, 128, 174), 1.0))
                if giuseppe.done:
                    giuseppe = None

            for effect in effects:
                effect.update(dt)
            effects = [effect for effect in effects if effect.ttl > 0]
            for stain in blood_stains:
                stain.update(dt)
            blood_stains = [stain for stain in blood_stains if stain.ttl > 0]

            if immunity_timer <= 0 and any(peanut.hitbox.colliderect(chaser.hitbox) for chaser in chasers):
                final_score = peanut.score
                name_input = ""
                state = "name_entry"

        camera = peanut.pos - pygame.Vector2(WIDTH / 2, HEIGHT / 2)
        draw_background(screen, camera, small_font)
        for stain in blood_stains:
            stain.draw(screen, camera)
        bonus.draw(screen, camera)
        if michelone is not None:
            michelone.draw(screen, small_font, camera)
        if fabio is not None:
            fabio.draw(screen, camera, small_font)
        if giuseppe is not None:
            giuseppe.draw(screen, camera, small_font)
        for chaser in chasers:
            chaser.draw(screen, camera)
        for bus in buses:
            bus.draw(screen, camera, small_font)
        for effect in effects:
            effect.draw(screen, small_font, camera)
        if state == "playing":
            draw_campari_arrow(screen, peanut, bonus, small_font)
        if immunity_timer > 0:
            aura = pygame.Surface((150, 150), pygame.SRCALPHA)
            pygame.draw.circle(aura, (80, 205, 255, 80), (75, 75), 65)
            pygame.draw.circle(aura, (255, 255, 255, 95), (75, 75), 65, 3)
            screen.blit(aura, (WIDTH // 2 - 75, HEIGHT // 2 - 75))
        peanut.draw(screen, camera, bike_timer > 0)

        if state != "intro":
            panel = pygame.Surface((600, 100), pygame.SRCALPHA)
            panel.fill((19, 25, 35, 185))
            screen.blit(panel, (18, 18))
            text(screen, ui_font, f"Campari & Prosecco: {peanut.score}", (32, 29))
            speed_label = "TURBO x1.62" if bike_timer > 0 else "Velocita normale"
            text(screen, small_font, f"Inseguitrici: {len(chasers)}   |   {speed_label}", (32, 57), (235, 221, 177))
            text(screen, small_font, f"Protuberanza: {peanut.protuberance_length}px", (32, 80), (235, 221, 177))
            if immunity_timer > 0:
                text(screen, ui_font, f"SCUDO: {math.ceil(immunity_timer)}s", (340, 29), (100, 222, 255))
            elif bike_timer > 0:
                text(screen, ui_font, f"BICI: {math.ceil(bike_timer)}s", (420, 29), (255, 222, 88))

        if state == "intro":
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((10, 13, 21, 158))
            screen.blit(shade, (0, 0))
            text(screen, title_font, "FUGA DELLA NOCCIOLINA", (WIDTH // 2, 205), anchor="center")
            text(screen, ui_font, "Raccogli i bicchieri di Campari & Prosecco.", (WIDTH // 2, 285), anchor="center")
            text(screen, ui_font, "Ogni bicchiere allunga la protuberanza e richiama una donna; altre arrivano col tempo.", (WIDTH // 2, 321), anchor="center")
            text(screen, small_font, "Fabio Camicia da lo scudo e grida FORZA! Maglie: gialla bici, rossa botte, bianca EPF TOURS.", (WIDTH // 2, 350), (235, 221, 177), "center")
            text(screen, small_font, "Blu Giuseppe innamora 5 donne; verde Andrea accorcia la protuberanza del 50%.", (WIDTH // 2, 375), (235, 221, 177), "center")
            text(screen, small_font, "Mappa infinita: esplora Montefiascone in tutte le direzioni.", (WIDTH // 2, 400), (235, 221, 177), "center")
            text(screen, small_font, "Muoviti con WASD oppure frecce direzionali", (WIDTH // 2, 425), (235, 221, 177), "center")
            text(screen, ui_font, "PREMI INVIO O SPAZIO PER INIZIARE", (WIDTH // 2, 476), (255, 222, 88), "center")

        if state == "name_entry":
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((12, 16, 24, 190))
            screen.blit(shade, (0, 0))
            text(screen, title_font, "NUOVO TENTATIVO FINITO", (WIDTH // 2, 218), anchor="center")
            text(screen, ui_font, f"Campari raccolti: {final_score}", (WIDTH // 2, 270), (255, 222, 88), "center")
            text(screen, small_font, "Inserisci 3 caratteri per il record arcade", (WIDTH // 2, 322), (235, 221, 177), "center")
            display_name = (name_input + "___")[:3]
            text(screen, arcade_font, display_name, (WIDTH // 2, 376), (255, 255, 255), "center")
            text(screen, small_font, "INVIO conferma   |   BACKSPACE corregge", (WIDTH // 2, 428), (235, 221, 177), "center")

        if state == "game_over":
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((12, 16, 24, 174))
            screen.blit(shade, (0, 0))
            text(screen, title_font, "RECORD CAMAPARI", (WIDTH // 2, 210), anchor="center")
            if records:
                for index, record in enumerate(records[:5], start=1):
                    row = f"{index}. {record['name']}  {record['score']:03d}"
                    text(screen, arcade_font, row, (WIDTH // 2, 250 + index * 42), (255, 222, 88) if index == 1 else WHITE, "center")
            else:
                text(screen, ui_font, "Nessun record salvato", (WIDTH // 2, 305), (255, 222, 88), "center")
            text(screen, ui_font, "Premi INVIO o SPAZIO per riprovare", (WIDTH // 2, 540), anchor="center")

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
