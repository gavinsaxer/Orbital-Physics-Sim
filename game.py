import pygame
import numpy as np
import math
from collections import deque

# --- Configuration ---
SIM_WIDTH, HEIGHT = 800, 800
SIDEBAR_WIDTH = 300
WIDTH = SIM_WIDTH + SIDEBAR_WIDTH  # Expanded to fit the UI
FPS = 60
G = 1.0  # Simplified G. We scale Mass to compensate.
dt = 0.01

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Sandbox - Inner Solar System")
clock = pygame.time.Clock()


# --- 1. Define the Unified Class ---
class Massive_Object:
    def __init__(
        self,
        x,
        y,
        mass=20000.0,
        color=(255, 80, 80),
        radius=None,
        fixed=True,
        vx=0.0,
        vy=0.0,
    ):
        self.start_pos = np.array([float(x), float(y)])
        self.start_vel = np.array([float(vx), float(vy)])

        self.pos = self.start_pos.copy()
        self.vel = self.start_vel.copy()

        if not radius:
            # cube root of mass * scale_multiplier
            self.radius = max(3, int((mass ** (1 / 3)) * 0.75))
        else:
            self.radius = radius
        self.mass = mass
        self.color = color
        self.fixed = fixed

        # Give every object its own personal trail
        self.trail = deque(maxlen=6000)

    def reset(self):
        self.pos = self.start_pos.copy()
        self.vel = self.start_vel.copy()
        self.trail.clear()

    def draw(self, surface, is_selected=False):
        # Draw the trail first so it sits under the planet
        if len(self.trail) > 1:
            pygame.draw.lines(surface, self.color, False, list(self.trail), 1)

        # Highlight if selected
        if is_selected:
            pygame.draw.circle(
                surface,
                (255, 255, 255),
                (int(self.pos[0]), int(self.pos[1])),
                self.radius + 3,
                2,
            )

        pygame.draw.circle(
            surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius
        )

    def contains(self, point):
        return np.linalg.norm(self.pos - point) <= max(
            self.radius, 10
        )  # Min hitbox of 10px


# --- 2. State & Presets Management ---
objects = []
dragging_idx = None
selected_obj = None  # Tracks the object actively shown in the sidebar
is_running = False
# Increased base speed so the planets don't take forever to orbit
steps_per_frame = 50


def load_preset(preset_id):
    global objects, is_running, selected_obj
    is_running = False
    selected_obj = None
    objects = []

    if preset_id == 2:
        # Standard Single Planet
        objects.append(Massive_Object(400, 400, 30000.0, (255, 80, 80), fixed=True))
        objects.append(
            Massive_Object(400, 250, 1.0, (200, 255, 255), 5, fixed=False, vx=14.1)
        )

    elif preset_id == 3:
        # Binary Star System
        objects.append(Massive_Object(300, 400, 20000.0, (255, 150, 50), fixed=True))
        objects.append(Massive_Object(500, 400, 20000.0, (50, 150, 255), fixed=True))
        objects.append(
            Massive_Object(400, 150, 1.0, (200, 255, 255), 5, fixed=False, vx=12.6)
        )

    elif preset_id == 1:
        # ACCURATE INNER SOLAR SYSTEM
        # 1 AU (Earth Distance) = 200 pixels. GM = 10,000.

        objects.append(
            Massive_Object(400, 400, 10000.0, (255, 200, 50), 25, fixed=False)
        )

        # Mercury (0.39 AU = 78px | v = sqrt(10000/78) = 11.32)
        objects.append(
            Massive_Object(
                400, 400 - 78, 0.05, (150, 150, 150), 3, fixed=False, vx=11.32
            )
        )

        # Venus (0.72 AU = 144px | v = sqrt(10000/144) = 8.33)
        objects.append(
            Massive_Object(
                400, 400 - 144, 0.81, (200, 180, 100), 5, fixed=False, vx=8.33
            )
        )

        # Earth (1.00 AU = 200px | v = sqrt(10000/200) = 7.07)
        objects.append(
            Massive_Object(
                400, 400 - 200, 1.0, (100, 150, 255), 5, fixed=False, vx=7.07
            )
        )

        # Mars (1.52 AU = 304px | v = sqrt(10000/304) = 5.73)
        objects.append(
            Massive_Object(
                400, 400 - 304, 0.11, (255, 100, 50), 4, fixed=False, vx=5.73
            )
        )


def reset_simulation():
    global is_running
    for obj in objects:
        obj.reset()
    is_running = False


load_preset(1)  # Start with the Solar System preset loaded


def get_acceleration(target_obj):
    accel = np.array([0.0, 0.0])
    for other in objects:
        if other is target_obj:
            continue

        diff = other.pos - target_obj.pos
        dist_sq = np.sum(diff**2)

        if dist_sq < other.radius**2:
            continue

        dist = math.sqrt(dist_sq)
        force = G * other.mass / dist_sq
        accel += force * (diff / dist)
    return accel


# --- 3. Sidebar UI Rendering ---
def draw_sidebar(surface, selected):
    ui_elements = []

    # Draw Background
    sidebar_rect = pygame.Rect(SIM_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(surface, (30, 32, 40), sidebar_rect)
    pygame.draw.line(surface, (80, 80, 100), (SIM_WIDTH, 0), (SIM_WIDTH, HEIGHT), 2)

    font = pygame.font.SysFont(None, 26)
    title_font = pygame.font.SysFont(None, 34)

    if not selected:
        text = font.render("Click an object to edit", True, (150, 150, 150))
        surface.blit(text, (SIM_WIDTH + 20, 20))
        return ui_elements

    # Title
    title = title_font.render("Object Properties", True, (255, 255, 255))
    surface.blit(title, (SIM_WIDTH + 20, 20))

    y_offset = 70
    spacing = 55

    def draw_row(label, val_str, action_minus, action_plus, y):
        lbl = font.render(label, True, (200, 200, 200))
        surface.blit(lbl, (SIM_WIDTH + 20, y))

        # Minus Button
        rect_m = pygame.Rect(SIM_WIDTH + 100, y - 5, 30, 30)
        pygame.draw.rect(surface, (150, 50, 50), rect_m, border_radius=4)
        surface.blit(
            font.render("-", True, (255, 255, 255)), (rect_m.x + 10, rect_m.y + 7)
        )
        ui_elements.append((rect_m, action_minus))

        # Value
        val = font.render(val_str, True, (255, 255, 255))
        surface.blit(val, (SIM_WIDTH + 140, y))

        # Plus Button
        rect_p = pygame.Rect(SIM_WIDTH + 250, y - 5, 30, 30)
        pygame.draw.rect(surface, (50, 150, 50), rect_p, border_radius=4)
        surface.blit(
            font.render("+", True, (255, 255, 255)), (rect_p.x + 8, rect_p.y + 7)
        )
        ui_elements.append((rect_p, action_plus))

    # Rows
    draw_row("Mass", f"{selected.mass:.1f}", "mass_down", "mass_up", y_offset)
    draw_row("Radius", f"{selected.radius}", "rad_down", "rad_up", y_offset + spacing)
    draw_row(
        "Vel X", f"{selected.vel[0]:.2f}", "vx_down", "vx_up", y_offset + spacing * 2
    )
    draw_row(
        "Vel Y", f"{selected.vel[1]:.2f}", "vy_down", "vy_up", y_offset + spacing * 3
    )

    # Fixed Toggle Button
    fixed_y = y_offset + spacing * 4
    btn_color = (100, 150, 100) if selected.fixed else (150, 100, 100)
    fixed_rect = pygame.Rect(SIM_WIDTH + 20, fixed_y, 260, 40)
    pygame.draw.rect(surface, btn_color, fixed_rect, border_radius=5)
    f_text = font.render(
        f"Fixed in Place: {'YES' if selected.fixed else 'NO'}", True, (255, 255, 255)
    )
    surface.blit(f_text, (fixed_rect.x + 15, fixed_rect.y + 12))
    ui_elements.append((fixed_rect, "toggle_fixed"))

    # Delete Button
    del_y = fixed_y + 60
    del_rect = pygame.Rect(SIM_WIDTH + 20, del_y, 260, 40)
    pygame.draw.rect(surface, (200, 50, 50), del_rect, border_radius=5)
    d_text = font.render("Delete Object", True, (255, 255, 255))
    surface.blit(d_text, (del_rect.x + 65, del_rect.y + 12))
    ui_elements.append((del_rect, "delete"))

    # Tip
    tip = font.render("Tip: Hold SHIFT to adjust faster", True, (120, 120, 120))
    surface.blit(tip, (SIM_WIDTH + 20, HEIGHT - 40))

    return ui_elements


# --- Main Game Loop ---
program_active = True
active_ui_elements = []

while program_active:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            program_active = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                is_running = not is_running
            elif event.key == pygame.K_r:
                reset_simulation()
            elif event.key == pygame.K_1:
                load_preset(1)
            elif event.key == pygame.K_2:
                load_preset(2)
            elif event.key == pygame.K_3:
                load_preset(3)
            elif event.key == pygame.K_UP:
                steps_per_frame = min(120, int(steps_per_frame * 1.25))
            elif event.key == pygame.K_DOWN:
                steps_per_frame = max(4, int(steps_per_frame / 1.25))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = np.array(event.pos)

            # Check if clicked inside the Simulation Area
            if mouse_pos[0] < SIM_WIDTH:
                if event.button == 1:  # Left Click
                    clicked_existing = False
                    for i, obj in enumerate(objects):
                        if obj.contains(mouse_pos):
                            dragging_idx = i
                            selected_obj = obj
                            clicked_existing = True
                            break

                    if not clicked_existing:
                        new_obj = Massive_Object(mouse_pos[0], mouse_pos[1])
                        objects.append(new_obj)
                        dragging_idx = len(objects) - 1
                        selected_obj = new_obj

                elif event.button == 3:  # Right Click
                    for i, obj in enumerate(objects):
                        if obj.contains(mouse_pos):
                            if obj is selected_obj:
                                selected_obj = None
                            objects.pop(i)
                            break

            # Check if clicked inside the UI Sidebar area
            elif mouse_pos[0] >= SIM_WIDTH and selected_obj is not None:
                if event.button == 1:
                    mods = pygame.key.get_mods()
                    multiplier = 10 if (mods & pygame.KMOD_SHIFT) else 1

                    for rect, action in active_ui_elements:
                        if rect.collidepoint(event.pos):
                            if action == "mass_up":
                                selected_obj.mass += 100 * multiplier
                            elif action == "mass_down":
                                selected_obj.mass = max(
                                    0.01, selected_obj.mass - (100 * multiplier)
                                )
                            elif action == "rad_up":
                                selected_obj.radius += 1 * multiplier
                            elif action == "rad_down":
                                selected_obj.radius = max(
                                    2, selected_obj.radius - (1 * multiplier)
                                )
                            elif action == "vx_up":
                                selected_obj.vel[0] += 0.5 * multiplier
                                selected_obj.start_vel[0] = selected_obj.vel[0]
                            elif action == "vx_down":
                                selected_obj.vel[0] -= 0.5 * multiplier
                                selected_obj.start_vel[0] = selected_obj.vel[0]
                            elif action == "vy_up":
                                selected_obj.vel[1] += 0.5 * multiplier
                                selected_obj.start_vel[1] = selected_obj.vel[1]
                            elif action == "vy_down":
                                selected_obj.vel[1] -= 0.5 * multiplier
                                selected_obj.start_vel[1] = selected_obj.vel[1]
                            elif action == "toggle_fixed":
                                selected_obj.fixed = not selected_obj.fixed
                            elif action == "delete":
                                objects.remove(selected_obj)
                                selected_obj = None
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging_idx = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging_idx is not None and event.pos[0] < SIM_WIDTH:
                objects[dragging_idx].pos = np.array(
                    [float(event.pos[0]), float(event.pos[1])]
                )
                objects[dragging_idx].start_pos = objects[dragging_idx].pos.copy()

    # --- PHYSICS ---
    if is_running:
        for step in range(steps_per_frame):
            unfixed = [obj for obj in objects if not obj.fixed]

            accels = [get_acceleration(obj) for obj in unfixed]

            for i, obj in enumerate(unfixed):
                obj.pos += obj.vel * dt + 0.5 * accels[i] * (dt**2)

            new_accels = [get_acceleration(obj) for obj in unfixed]

            collision = False
            for i, obj in enumerate(unfixed):
                obj.vel += 0.5 * (accels[i] + new_accels[i]) * dt

                for other in objects:
                    if obj is not other and other.contains(obj.pos):
                        collision = True
                        break

            if collision:
                reset_simulation()
                break

            # Only record the trail once every 5 physics steps to keep lines smooth
            # but prevent them from consuming too much memory
            if step % 5 == 0:
                for obj in unfixed:
                    obj.trail.append((int(obj.pos[0]), int(obj.pos[1])))

    # --- RENDERING ---
    screen.fill((15, 15, 20))

    # All drawing is handled securely by the objects themselves
    for obj in objects:
        is_selected = obj is selected_obj
        obj.draw(screen, is_selected=is_selected)

    # UI overlays for the simulation side
    font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 32)

    if is_running:
        status_text = large_font.render("RUNNING", True, (50, 255, 50))
    else:
        status_text = large_font.render("SETUP MODE", True, (255, 200, 50))
    screen.blit(status_text, (15, 15))

    controls1 = font.render(
        "Presets: [1] Solar | [2] Basic | [3] Binary", True, (150, 150, 150)
    )
    controls2 = font.render(
        "Controls: [SPACE] Play/Pause | [R] Reset | Mouse to edit",
        True,
        (150, 150, 150),
    )
    speed_text = font.render(
        f"Speed: {steps_per_frame/4}x (UP/DOWN to change)", True, (200, 255, 200)
    )

    screen.blit(controls1, (15, 50))
    screen.blit(controls2, (15, 75))
    screen.blit(speed_text, (15, 100))

    # Draw the Sidebar and update clickable elements
    active_ui_elements = draw_sidebar(screen, selected_obj)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
