import math
import random
import sys
import pygame

# Initialize Pygame
pygame.init()

# Window Settings
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroid Game - Enemy Field of View")
clock = pygame.time.Clock()

# Colors & Font setup
BG_COLOR = (15, 15, 25)
WHITE = (255, 255, 255)
RED = (255, 60, 60)
GRAY = (90, 90, 110)
YELLOW = (255, 210, 80)
FONT = pygame.font.SysFont("Arial", 28)
SMALL_FONT = pygame.font.SysFont("Arial", 20)
BIG_FONT = pygame.font.SysFont("Arial", 72, bold=True)

# Enemy AI settings (Lesson 5)
DETECTION_RANGE = 200  # How far the enemy can see (Lesson 2: distance)
FOV_THRESHOLD = 0.7  # How "in front" the player must be (Lesson 5: dot product)
ENEMY_SCAN_SPEED = 0.5  # Degrees per frame the enemy rotates while patrolling
ENEMY_PATROL_SPEED = 1.5  # Pixels per frame while patrolling
ENEMY_CHASE_SPEED = 2.5  # Pixels per frame while attacking
ENEMY_TURN_SPEED = 2.0  # Max degrees per frame the enemy turns toward the player
ENEMY_KEEP_DISTANCE = 120  # Enemy stops chasing when this close to the player
ENEMY_MARGIN = 30  # How close to the screen edge the enemy can get
MISSILE_SPEED = 6.0
ENEMY_FIRE_COOLDOWN = 60  # Frames between enemy shots
ENEMY_FREEZE_FRAMES = (
    300  # 5 seconds (at 60 FPS) where the enemy can't move at the start
)

# Win condition
WIN_SCORE = 20

# Number of asteroids kept on screen at all times
ASTEROID_COUNT = 6

# Player collision / respawn settings
PLAYER_RADIUS = 14
SPAWN_INVULNERABLE_FRAMES = 120  # 2 seconds of safety after (re)spawning


class Asteroid:

    def __init__(self, x, y, circle_radius=20):
        self.radius = circle_radius
        self.circle_pos = pygame.math.Vector2(x, y)

        # Mass is proportional to area (radius squared)
        self.mass = self.radius**2

        # Randomized velocity vector using Vector2
        speed = random.uniform(1.5, 4.0)
        angle = random.uniform(0, 2 * math.pi)
        self.vel = pygame.math.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)

        # Asteroid color tints
        base_gray = random.randint(90, 160)
        self.color = (base_gray, base_gray + 10, base_gray + 25)

    def update(self):
        self.circle_pos += self.vel

        # Screen boundary collision (bounce off walls)
        if self.circle_pos.x - self.radius < 0:
            self.circle_pos.x = self.radius
            self.vel.x *= -1
        elif self.circle_pos.x + self.radius > WIDTH:
            self.circle_pos.x = WIDTH - self.radius
            self.vel.x *= -1

        if self.circle_pos.y - self.radius < 0:
            self.circle_pos.y = self.radius
            self.vel.y *= -1
        elif self.circle_pos.y + self.radius > HEIGHT:
            self.circle_pos.y = HEIGHT - self.radius
            self.vel.y *= -1

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            self.color,
            (int(self.circle_pos.x), int(self.circle_pos.y)),
            self.radius,
        )


class Player:

    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)
        self.angle = 0.0  # Rotation angle in radians

        # Physics Constants
        self.THRUST = 0.15
        self.DRAG = 0.99
        self.MAX_SPEED = 7.0
        self.ROTATION_SPEED = 0.05

        self.radius = PLAYER_RADIUS
        self.invulnerable = SPAWN_INVULNERABLE_FRAMES

    def update(self, keys):
        if self.invulnerable > 0:
            self.invulnerable -= 1

        # 1. Rotate spaceship with LEFT/RIGHT or A/D keys
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= self.ROTATION_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += self.ROTATION_SPEED

        # 2. Reset acceleration each frame
        self.acceleration = pygame.math.Vector2(0, 0)

        # 3. Calculate forward direction vector based on ship's angle
        forward = pygame.math.Vector2(math.sin(self.angle), -math.cos(self.angle))

        # 4. Apply thrust with UP or W key
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.acceleration = forward * self.THRUST

        # 5. Physics calculations: Update velocity, apply drag, and limit max speed
        self.velocity += self.acceleration
        self.velocity *= self.DRAG

        if self.velocity.length() > self.MAX_SPEED:
            self.velocity.scale_to_length(self.MAX_SPEED)

        # 6. Update position
        self.pos += self.velocity

        # 7. Screen wrapping (allows ship to fly off one side and appear on the other)
        if self.pos.x > WIDTH:
            self.pos.x = 0
        elif self.pos.x < 0:
            self.pos.x = WIDTH

        if self.pos.y > HEIGHT:
            self.pos.y = 0
        elif self.pos.y < 0:
            self.pos.y = HEIGHT

    def get_nose_pos(self):
        # Calculate the tip of the ship for bullet launching
        nose_distance = 20
        nose_x = self.pos.x + math.sin(self.angle) * nose_distance
        nose_y = self.pos.y - math.cos(self.angle) * nose_distance
        return pygame.math.Vector2(nose_x, nose_y)

    def draw(self, surface):
        # Blink while invulnerable after spawning
        if self.invulnerable > 0 and (self.invulnerable // 6) % 2 == 0:
            return

        points = [
            pygame.math.Vector2(0, -20),  # Nose
            pygame.math.Vector2(-12, 15),  # Bottom Left
            pygame.math.Vector2(12, 15),  # Bottom Right
        ]

        rotated_points = []
        for p in points:
            rx = p.x * math.cos(self.angle) - p.y * math.sin(self.angle)
            ry = p.x * math.sin(self.angle) + p.y * math.cos(self.angle)
            rotated_points.append((self.pos.x + rx, self.pos.y + ry))

        # Draw filled black spaceship body
        pygame.draw.polygon(surface, (0, 0, 0), rotated_points, width=0)
        # Draw white outline around the spaceship
        pygame.draw.polygon(surface, (255, 255, 255), rotated_points, width=2)


class Bullet:

    def __init__(self, x, y, angle):
        self.pos = pygame.math.Vector2(x, y)
        self.speed = 10.0
        # Straight-line velocity vector based on ship's firing angle
        self.vel = pygame.math.Vector2(math.sin(angle), -math.cos(angle)) * self.speed
        self.radius = 4
        self.active = True

    def update(self):
        # Move in a straight line
        self.pos += self.vel

        # Deactivate if out of bounds
        if (
            self.pos.x < 0
            or self.pos.x > WIDTH
            or self.pos.y < 0
            or self.pos.y > HEIGHT
        ):
            self.active = False

    def draw(self, surface):
        # Draw bullets as red circles
        pygame.draw.circle(
            surface, (255, 60, 60), (int(self.pos.x), int(self.pos.y)), self.radius
        )


class Enemy:
    """Enemy spaceship that uses distance + dot product to 'see' the player."""

    def __init__(self, x, y):
        self.position = pygame.math.Vector2(x, y)
        self.angle = 0.0  # Degrees; 0 = facing right
        self.state = "PATROL"
        self.detected = False
        self.fire_timer = 0
        self.freeze_timer = ENEMY_FREEZE_FRAMES

        # The AI's math, stored so it can be displayed on screen
        self.distance = 0.0
        self.dot = 0.0

    def get_forward_vector(self):
        # Lesson 3: angle -> direction vector (y is negated because screen y points down)
        radians = math.radians(self.angle)
        return pygame.math.Vector2(math.cos(radians), -math.sin(radians))

    def update(self, player, missiles):
        # Cooldown: the enemy is frozen (no moving, turning or shooting) until the timer runs out
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            self.state = "FROZEN"
            self.detected = False
            self.distance = self.position.distance_to(player.pos)
            return

        forward = self.get_forward_vector()

        # Lesson 2: direction toward the player (keep direction, remove distance)
        to_player = player.pos - self.position
        if to_player.length() > 0:
            to_player = to_player.normalize()

        # Lesson 2: how far away is the player?
        self.distance = self.position.distance_to(player.pos)

        # Lesson 5: how similar are the two directions?
        self.dot = forward.dot(to_player)

        # The core AI decision: close enough AND in front
        self.detected = self.distance < DETECTION_RANGE and self.dot > FOV_THRESHOLD

        if self.detected:
            self.state = "ATTACK"

            # Turn toward the player, but only a little each frame (so you can escape)
            offset = player.pos - self.position
            target_angle = math.degrees(math.atan2(-offset.y, offset.x))
            diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += max(-ENEMY_TURN_SPEED, min(ENEMY_TURN_SPEED, diff))

            # Chase the player, but hold back at a safe distance
            if self.distance > ENEMY_KEEP_DISTANCE:
                self.position += forward * ENEMY_CHASE_SPEED
        else:
            self.state = "PATROL"
            # Challenge 4: slowly scan the area while patrolling
            self.angle += ENEMY_SCAN_SPEED
            self.position += forward * ENEMY_PATROL_SPEED

        self.angle %= 360
        self.keep_on_screen()

        # Challenge 3: fire toward the player's current position when detected
        if self.fire_timer > 0:
            self.fire_timer -= 1
        if self.detected and self.fire_timer == 0 and to_player.length() > 0:
            nose = self.position + forward * 22
            missiles.append(EnemyMissile(nose, to_player * MISSILE_SPEED))
            self.fire_timer = ENEMY_FIRE_COOLDOWN

    def keep_on_screen(self):
        # Bounce off the walls by reflecting the facing angle
        if self.position.x < ENEMY_MARGIN or self.position.x > WIDTH - ENEMY_MARGIN:
            self.position.x = max(
                ENEMY_MARGIN, min(WIDTH - ENEMY_MARGIN, self.position.x)
            )
            self.angle = (180 - self.angle) % 360  # flips the x direction
        if self.position.y < ENEMY_MARGIN or self.position.y > HEIGHT - ENEMY_MARGIN:
            self.position.y = max(
                ENEMY_MARGIN, min(HEIGHT - ENEMY_MARGIN, self.position.y)
            )
            self.angle = (-self.angle) % 360  # flips the y direction

    def draw(self, surface):
        forward = self.get_forward_vector()
        side = forward.rotate(90)

        # Part 9: detection range circle
        pygame.draw.circle(surface, GRAY, self.position, DETECTION_RANGE, 1)

        # Field-of-view cone edges: dot > threshold means angle < acos(threshold)
        half_fov = math.degrees(math.acos(max(-1.0, min(1.0, FOV_THRESHOLD))))
        cone_color = RED if self.detected else GRAY
        for edge_angle in (half_fov, -half_fov):
            edge = forward.rotate(edge_angle) * DETECTION_RANGE
            pygame.draw.line(
                surface, cone_color, self.position, self.position + edge, 1
            )

        # Part 10: forward vector
        pygame.draw.line(surface, RED, self.position, self.position + forward * 100, 3)

        # Part 8: enemy body (white when patrolling, red when the player is detected)
        color = RED if self.detected else WHITE
        nose = self.position + forward * 22
        left = self.position - forward * 14 + side * 14
        back = self.position - forward * 6
        right = self.position - forward * 14 - side * 14
        points = [nose, left, back, right]
        pygame.draw.polygon(surface, (0, 0, 0), points)
        pygame.draw.polygon(surface, color, points, 2)

        if self.freeze_timer > 0:
            label = f"FROZEN {self.freeze_timer / 60:.1f}s"
            color = YELLOW
        else:
            label = "PLAYER DETECTED!" if self.detected else "PATROL"
        text = SMALL_FONT.render(f"Enemy: {label}", True, color)
        surface.blit(
            text, (self.position.x - text.get_width() / 2, self.position.y + 28)
        )


class EnemyMissile:

    def __init__(self, pos, velocity):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(velocity)
        self.radius = 5
        self.active = True

    def update(self):
        self.pos += self.vel
        if (
            self.pos.x < 0
            or self.pos.x > WIDTH
            or self.pos.y < 0
            or self.pos.y > HEIGHT
        ):
            self.active = False

    def draw(self, surface):
        pygame.draw.circle(
            surface, YELLOW, (int(self.pos.x), int(self.pos.y)), self.radius
        )


def handle_collision(ast1, ast2):
    delta = ast2.circle_pos - ast1.circle_pos
    distance = delta.length()
    min_distance = ast1.radius + ast2.radius

    if 0 < distance < min_distance:
        overlap = min_distance - distance
        normal = delta.normalize()

        total_mass = ast1.mass + ast2.mass
        ast1.circle_pos -= normal * overlap * (ast2.mass / total_mass)
        ast2.circle_pos += normal * overlap * (ast1.mass / total_mass)

        vel_rel = ast2.vel - ast1.vel
        vel_along_normal = vel_rel.dot(normal)

        if vel_along_normal < 0:
            restitution = 0.95
            impulse = -(1 + restitution) * vel_along_normal
            impulse /= (1 / ast1.mass) + (1 / ast2.mass)

            ast1.vel -= (impulse / ast1.mass) * normal
            ast2.vel += (impulse / ast2.mass) * normal


def spawn_asteroid(asteroids, avoid_pos=None):
    circle_radius = random.randint(20, 45)
    x = random.randint(circle_radius + 50, WIDTH - circle_radius - 50)
    y = random.randint(circle_radius + 50, HEIGHT - circle_radius - 50)

    overlap = False
    for ast in asteroids:
        if ast.circle_pos.distance_to(pygame.math.Vector2(x, y)) < (
            ast.radius + circle_radius + 20
        ):
            overlap = True
            break

    # Don't spawn an asteroid right on top of the player
    if avoid_pos is not None and avoid_pos.distance_to(pygame.math.Vector2(x, y)) < (
        circle_radius + 120
    ):
        overlap = True

    if not overlap:
        asteroids.append(Asteroid(x, y, circle_radius))


def fill_asteroids(asteroids, avoid_pos=None, max_attempts=200):
    # Keep trying random spots until there are exactly ASTEROID_COUNT asteroids
    attempts = 0
    while len(asteroids) < ASTEROID_COUNT and attempts < max_attempts:
        spawn_asteroid(asteroids, avoid_pos)
        attempts += 1


def draw_hud(enemy, score):
    # Score board
    score_surface = FONT.render(f"Score: {score} / {WIN_SCORE}", True, WHITE)
    screen.blit(score_surface, (20, 20))

    # Enemy cooldown countdown
    if enemy.freeze_timer > 0:
        cooldown = FONT.render(
            f"Enemy frozen: {math.ceil(enemy.freeze_timer / 60)}", True, YELLOW
        )
        screen.blit(cooldown, (WIDTH / 2 - cooldown.get_width() / 2, 20))

    # Challenge 1: display the AI's math
    state_color = RED if enemy.detected else WHITE
    lines = [
        (f"Distance: {enemy.distance:.1f}", WHITE),
        (f"Dot Product: {enemy.dot:.2f}", WHITE),
        (f"FOV Threshold: {FOV_THRESHOLD:.1f}  (keys 1-4)", GRAY),
        (f"Enemy State: {enemy.state}", state_color),
    ]
    for i, (text, color) in enumerate(lines):
        text_surface = SMALL_FONT.render(text, True, color)
        screen.blit(text_surface, (WIDTH - text_surface.get_width() - 20, 20 + i * 26))


def draw_game_over(score, won=False):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    if won:
        title = BIG_FONT.render("YOU WIN!", True, YELLOW)
    else:
        title = BIG_FONT.render("YOU DIED", True, RED)
    info = FONT.render(f"Final Score: {score}", True, WHITE)
    hint = SMALL_FONT.render("Press R to restart", True, WHITE)
    screen.blit(title, (WIDTH / 2 - title.get_width() / 2, HEIGHT / 2 - 90))
    screen.blit(info, (WIDTH / 2 - info.get_width() / 2, HEIGHT / 2 + 5))
    screen.blit(hint, (WIDTH / 2 - hint.get_width() / 2, HEIGHT / 2 + 50))


def new_game():
    player = Player(WIDTH // 2, HEIGHT // 2)
    enemy = Enemy(WIDTH / 4, HEIGHT / 2)
    asteroids = []
    fill_asteroids(asteroids, avoid_pos=player.pos)
    return player, enemy, asteroids


def main():
    global FOV_THRESHOLD

    player, enemy, asteroids = new_game()
    bullets = []
    missiles = []
    score = 0  # Initialize the score counter
    game_over = False
    won = False

    # Challenge 2: number keys switch between FOV thresholds
    fov_keys = {pygame.K_1: 0.0, pygame.K_2: 0.5, pygame.K_3: 0.7, pygame.K_4: 0.9}

    running = True
    while running:
        clock.tick(60)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not game_over:  # Left click shoots bullet
                    nose_pos = player.get_nose_pos()
                    bullets.append(Bullet(nose_pos.x, nose_pos.y, player.angle))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # Restart the game
                    player, enemy, asteroids = new_game()
                    bullets = []
                    missiles = []
                    score = 0
                    game_over = False
                    won = False
                elif event.key in fov_keys:
                    FOV_THRESHOLD = fov_keys[event.key]

        if not game_over:
            # Update entities (passing keys for continuous movement)
            player.update(keys)
            for ast in asteroids:
                ast.update()

            # Enemy AI: can it see the player?
            enemy.update(player, missiles)

            for bullet in bullets[:]:
                bullet.update()
                if not bullet.active:
                    bullets.remove(bullet)
                    continue

                # Check collision with asteroids
                for ast in asteroids[:]:
                    if (
                        bullet.pos.distance_to(ast.circle_pos)
                        < ast.radius + bullet.radius
                    ):
                        bullets.remove(bullet)
                        asteroids.remove(ast)
                        score += 1  # Increase score by 1 point per hit
                        # Immediately respawn so there are always ASTEROID_COUNT asteroids
                        fill_asteroids(asteroids, avoid_pos=player.pos)
                        if score >= WIN_SCORE:
                            won = True
                            game_over = True
                        break

            # Safety net: top up in case a respawn couldn't find free space last frame
            fill_asteroids(asteroids, avoid_pos=player.pos)

            for missile in missiles[:]:
                missile.update()
                if not missile.active:
                    missiles.remove(missile)

            # Handle asteroid-to-asteroid collisions
            for i in range(len(asteroids)):
                for j in range(i + 1, len(asteroids)):
                    handle_collision(asteroids[i], asteroids[j])

            # Player dies when touching an asteroid or an enemy missile
            if player.invulnerable == 0 and not won:
                for ast in asteroids:
                    if (
                        player.pos.distance_to(ast.circle_pos)
                        < ast.radius + player.radius
                    ):
                        game_over = True
                        break
                for missile in missiles:
                    if (
                        player.pos.distance_to(missile.pos)
                        < missile.radius + player.radius
                    ):
                        game_over = True
                        break

        # Draw everything
        screen.fill(BG_COLOR)

        enemy.draw(screen)

        for ast in asteroids:
            ast.draw(screen)

        for bullet in bullets:
            bullet.draw(screen)

        for missile in missiles:
            missile.draw(screen)

        if not game_over or won:
            player.draw(screen)

        draw_hud(enemy, score)

        if game_over:
            draw_game_over(score, won)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
