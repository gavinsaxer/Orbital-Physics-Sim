import pygame
import numpy as np
import math
from collections import deque

# --- Configuration ---
WIDTH, HEIGHT = 800, 800
FPS = 60
G = 10000
dt = 0.01

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Sandbox")
clock = pygame.time.Clock()


class Planet:
    def __init__(self, x, y, radius=10, mass=30.0, color=(255, 80, 80)):
        self.pos = np.array([float(x), float(y)])
        self.radius = radius
        self.mass = mass
        self.color = color

    def draw(self, surface):
        """Handles drawing itself to the screen."""
        pygame.draw.circle(
            surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius
        )

    def contains(self, point):
        """Returns True if a given (x,y) point is inside this planet."""
        return np.linalg.norm(self.pos - point) <= self.radius



planets = [Planet(400.0, 350.0)]


def reset_asteroid():
    return np.array([400.0, 300.0]), np.array([0.0, 0.0])


asteroid_pos, asteroid_vel = reset_asteroid()
trail = deque(maxlen=600)
dragging_planet_idx = None


def get_acceleration(pos):
    accel = np.array([0.0, 0.0])
    for p in planets:
        diff = p.pos - pos
        dist_sq = np.sum(diff**2)

        if dist_sq < p.radius**2:
            continue

        dist = math.sqrt(dist_sq)
        force = G * p.mass / dist_sq
        accel += force * (diff / dist)
    return accel


running = True
paused = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_r:
                asteroid_pos, asteroid_vel = reset_asteroid()
                trail.clear()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = np.array(event.pos)

            if event.button == 1:  # left click
                clicked_existing = False
                for i, p in enumerate(planets):
                    if p.contains(mouse_pos):
                        dragging_planet_idx = i
                        clicked_existing = True
                        break

                if not clicked_existing:
                    planets.append(Planet(mouse_pos[0], mouse_pos[1]))
                    dragging_planet_idx = len(planets) - 1

            elif event.button == 3:  # right click
                for i, p in enumerate(planets):
                    if p.contains(mouse_pos):
                        planets.pop(i)
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging_planet_idx = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging_planet_idx is not None:
                planets[dragging_planet_idx].pos = np.array(
                    [float(event.pos[0]), float(event.pos[1])]
                )

    if not paused:
        for _ in range(5):
            curr_accel = get_acceleration(asteroid_pos)

            asteroid_pos += asteroid_vel * dt + 0.5 * curr_accel * (dt**2)
            new_accel = get_acceleration(asteroid_pos)
            asteroid_vel += 0.5 * (curr_accel + new_accel) * dt

            for p in planets:
                if p.contains(asteroid_pos):
                    asteroid_pos, asteroid_vel = reset_asteroid()
                    trail.clear()
                    break

        trail.append((int(asteroid_pos[0]), int(asteroid_pos[1])))

    screen.fill((15, 15, 20))

    if len(trail) > 1:
        pygame.draw.lines(screen, (100, 150, 255), False, list(trail), 2)

    for p in planets:
        p.draw(screen)

    pygame.draw.circle(
        screen, (200, 255, 255), (int(asteroid_pos[0]), int(asteroid_pos[1])), 5
    )

    font = pygame.font.SysFont(None, 24)
    controls = "Left Click: Add/Drag | Right Click: Remove | SPACE: Pause | R: Reset"
    img = font.render(controls, True, (150, 150, 150))
    screen.blit(img, (15, 15))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
