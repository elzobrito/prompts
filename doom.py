import pygame
import math
import time

# Inicializar Pygame
pygame.init()

# Configurar a tela
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Jogo de Corrida")

# Cores
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)

# Configurar a pista
track_center = (screen_width // 2, screen_height // 2)
track_radius = 200
track_width = 50

# Fonte para o HUD
font = pygame.font.SysFont(None, 30)

class Car:
    def __init__(self, color, start_position):
        self.color = color
        self.position = start_position
        self.speed = 0
        self.max_speed = 10
        self.acceleration = 1
        self.brake_deceleration = 2
        self.orientation_angle = 0  # Começa apontando para a direita (0 radianos)
        self.nitro_boosts = 3
        self.nitro_duration = 0
        self.lap_start_time = time.time()  # Tempo inicial da volta
        self.lap_time = 0  # Tempo da volta atual
        self.best_time = float('inf')  # Melhor tempo inicial
        self.total_rotation = 0
        self.previous_theta = math.atan2(start_position[1] - track_center[1], start_position[0] - track_center[0])

    def move(self, keys, is_player=True):
        if is_player:
            if keys[pygame.K_UP]:
                if self.nitro_duration > 0:
                    self.speed = min(self.speed + self.acceleration, 15)
                    self.nitro_duration -= 1
                else:
                    self.speed = min(self.speed + self.acceleration, self.max_speed)
            elif keys[pygame.K_DOWN]:
                self.speed = max(self.speed - self.brake_deceleration, 0)
            if keys[pygame.K_LEFT]:
                self.orientation_angle -= 0.1
            if keys[pygame.K_RIGHT]:
                self.orientation_angle += 0.1
            if keys[pygame.K_SPACE] and self.nitro_boosts > 0:
                self.nitro_boosts -= 1
                self.nitro_duration = 120
        else:
            # Movimento simples para o oponente: segue a pista em uma velocidade constante
            self.speed = 5
            self.orientation_angle += 0.05  # Curva constante para seguir a pista

        # Atualizar a posição
        velocity_x = self.speed * math.cos(self.orientation_angle)
        velocity_y = self.speed * math.sin(self.orientation_angle)
        new_position = (self.position[0] + velocity_x, self.position[1] + velocity_y)

        # Verificar se a nova posição está na pista
        distance_from_center = math.hypot(new_position[0] - track_center[0], new_position[1] - track_center[1])
        if track_radius - track_width / 2 <= distance_from_center <= track_radius + track_width / 2:
            self.position = new_position
        else:
            self.speed = 0  # Reduz a velocidade se fora da pista, mas não termina o jogo imediatamente

        # Calcular o ângulo atual
        current_theta = math.atan2(self.position[1] - track_center[1], self.position[0] - track_center[0])
        delta_theta = current_theta - self.previous_theta
        if delta_theta > math.pi:
            delta_theta -= 2 * math.pi
        elif delta_theta < -math.pi:
            delta_theta += 2 * math.pi
        self.total_rotation += delta_theta
        self.previous_theta = current_theta

        # Verificar se completou uma volta
        if self.total_rotation >= 2 * math.pi:
            self.total_rotation -= 2 * math.pi
            current_lap_time = time.time() - self.lap_start_time
            if current_lap_time > 0:  # Evitar tempos inválidos
                self.lap_time = current_lap_time
                if self.lap_time < self.best_time:
                    self.best_time = self.lap_time
            self.lap_start_time = time.time()  # Reinicia o tempo da volta

        return True  # Sempre retorna True para evitar Game Over imediato por colisão

    def draw(self, screen):
        car_rect = pygame.Rect(0, 0, 30, 15)
        car_rect.center = self.position
        pygame.draw.rect(screen, self.color, car_rect)

# Criar os carros (posições iniciais ajustadas para dentro da pista)
start_angle = 0  # Ângulo inicial (0 radianos = direita)
start_x = track_center[0] + track_radius * math.cos(start_angle)
start_y = track_center[1] + track_radius * math.sin(start_angle)
player_car = Car(RED, (start_x, start_y))
opponent_car = Car(BLUE, (start_x + 20, start_y))  # Oponente um pouco deslocado

clock = pygame.time.Clock()
running = True
game_over = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        keys = pygame.key.get_pressed()

        # Mover o carro do jogador
        player_car.move(keys)

        # Mover o carro do oponente
        opponent_car.move(keys, is_player=False)

    # Desenhar a tela
    screen.fill(BLACK)
    pygame.draw.circle(screen, GREEN, track_center, track_radius, track_width)

    # Desenhar os carros
    player_car.draw(screen)
    opponent_car.draw(screen)

    # Desenhar o HUD
    speed_text = font.render(f"Velocidade: {int(player_car.speed)}", True, WHITE)
    screen.blit(speed_text, (10, 10))
    lap_time_text = font.render(f"Tempo da Volta: {int(time.time() - player_car.lap_start_time)}s", True, WHITE)
    screen.blit(lap_time_text, (10, 40))
    best_time_text = font.render(f"Melhor Tempo: {int(player_car.best_time) if player_car.best_time != float('inf') else 'N/A'}s", True, WHITE)
    screen.blit(best_time_text, (10, 70))
    nitro_text = font.render(f"Boosts de Nitro: {player_car.nitro_boosts}", True, WHITE)
    screen.blit(nitro_text, (10, 100))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()