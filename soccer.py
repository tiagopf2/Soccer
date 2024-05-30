import pygame
import sys
import numpy as np
from scipy.spatial import Voronoi
from game_data import GameData  # Import the GameData class

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800
BACKGROUND_COLOR = (34, 177, 76)  # Green field
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BALL_COLOR = (255, 255, 0)
PLAYER_RADIUS = 17
BALL_RADIUS = 10
LINE_COLOR = WHITE
LINE_WIDTH = 2
GREY_POINT_COLOR = (150, 150, 150)
GREY_POINT_RADIUS = 5
FONT_SIZE = 25
STRIPE_WIDTH = 20

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Soccer Tactics Board')
font = pygame.font.Font(None, FONT_SIZE)

# Load game data
game_data = GameData('game_data.csv')
current_time = 0
paused = False

# Initial player positions
players = game_data.get_positions(current_time)

# Grey points (boundary points for Voronoi diagram)
grey_points = [(50, 50), (WIDTH - 50, 50), (WIDTH - 50, HEIGHT - 50), (50, HEIGHT - 50)]

selected = None

def draw_field():
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.rect(screen, LINE_COLOR, (50, 50, WIDTH - 100, HEIGHT - 100), LINE_WIDTH)
    pygame.draw.circle(screen, LINE_COLOR, (WIDTH // 2, HEIGHT // 2), 100, LINE_WIDTH)
    pygame.draw.line(screen, LINE_COLOR, (WIDTH // 2, 50), (WIDTH // 2, HEIGHT - 50), LINE_WIDTH)
    pygame.draw.rect(screen, LINE_COLOR, (50, HEIGHT // 2 - 50, 20, 100), LINE_WIDTH)
    pygame.draw.rect(screen, LINE_COLOR, (WIDTH - 70, HEIGHT // 2 - 50, 20, 100), LINE_WIDTH)
    for point in grey_points:
        pygame.draw.circle(screen, GREY_POINT_COLOR, point, GREY_POINT_RADIUS)

def draw_players():
    for player in players['team1']:
        pygame.draw.circle(screen, BLUE, player[:2], PLAYER_RADIUS)
        text = font.render(str(player[2]), True, WHITE)
        text_rect = text.get_rect(center=player[:2])
        screen.blit(text, text_rect)
    for player in players['team2']:
        pygame.draw.circle(screen, RED, player[:2], PLAYER_RADIUS)
        text = font.render(str(player[2]), True, WHITE)
        text_rect = text.get_rect(center=player[:2])
        screen.blit(text, text_rect)
    pygame.draw.circle(screen, BALL_COLOR, players['ball'][0], BALL_RADIUS)

def get_selected(pos):
    for team, player_list in players.items():
        for i, player in enumerate(player_list):
            if (pos[0] - player[0]) ** 2 + (pos[1] - player[1]) ** 2 <= PLAYER_RADIUS ** 2:
                return team, i
    if (pos[0] - players['ball'][0][0]) ** 2 + (pos[1] - players['ball'][0][1]) ** 2 <= BALL_RADIUS ** 2:
        return 'ball', None
    return None

def draw_voronoi():
    points = [player[:2] for player in players['team1']] + [player[:2] for player in players['team2']]
    points.extend(grey_points)
    vor = Voronoi(points)

    for region_index, region in enumerate(vor.regions):
        if not -1 in region and region:
            polygon = [vor.vertices[i] for i in region]
            centroid = np.mean(polygon, axis=0)
            closest_player = None
            min_distance = float('inf')

            for player in players['team1'] + players['team2']:
                distance = np.linalg.norm(np.array(player[:2]) - centroid)
                if distance < min_distance:
                    min_distance = distance
                    if player in players['team1']:
                        closest_player = 'team1'
                    else:
                        closest_player = 'team2'

            if closest_player == 'team1':
                draw_stripes_in_region(polygon, BLUE)
            elif closest_player == 'team2':
                draw_stripes_in_region(polygon, RED)

    for simplex in vor.ridge_vertices:
        simplex = np.asarray(simplex)
        if np.all(simplex >= 0):
            pygame.draw.line(screen, (0, 0, 0), vor.vertices[simplex[0]], vor.vertices[simplex[1]], 1)

def draw_stripes_in_region(region_polygon, color):
    region_polygon = np.array(region_polygon)
    min_x = np.min(region_polygon[:, 0])
    max_x = np.max(region_polygon[:, 0])
    min_y = np.min(region_polygon[:, 1])
    max_y = np.max(region_polygon[:, 1])

    for x in np.arange(min_x, max_x, STRIPE_WIDTH):
        intersections = []
        for p1, p2 in zip(region_polygon, np.roll(region_polygon, -1, axis=0)):
            if p2[0] != p1[0] and (p1[0] <= x <= p2[0] or p2[0] <= x <= p1[0]):
                intersections.append(p1[1] + (p2[1] - p1[1]) * (x - p1[0]) / (p2[0] - p1[0]))
        if len(intersections) == 2:
            pygame.draw.line(screen, color, (x, min(intersections)), (x, max(intersections)))

    for y in np.arange(min_y, max_y, STRIPE_WIDTH):
        intersections = []
        for p1, p2 in zip(region_polygon, np.roll(region_polygon, -1, axis=0)):
            if p2[1] != p1[1] and (p1[1] <= y <= p2[1] or p2[1] <= y <= p1[1]):
                intersections.append(p1[0] + (p2[0] - p1[0]) * (y - p1[1]) / (p2[1] - p1[1]))
        if len(intersections) == 2:
            pygame.draw.line(screen, color, (min(intersections), y), (max(intersections), y))

def update_simulation(step=1):
    global current_time, players
    current_time += step
    if current_time > game_data.max_time:
        current_time = 0
    elif current_time < 0:
        current_time = game_data.max_time
    players = game_data.get_positions(current_time)

def main():
    global selected, paused
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                selected = get_selected(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                selected = None
            elif event.type == pygame.MOUSEMOTION and selected:
                team, i = selected
                if team == 'ball':
                    players['ball'][0] = event.pos
                else:
                    players[team][i] = (*event.pos, players[team][i][2])
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    update_simulation(1)  # Move one frame forward
                elif event.key == pygame.K_LEFT:
                    update_simulation(-1)  # Move one frame backward

        draw_field()
        draw_players()
        draw_voronoi()
        if not paused:
            update_simulation()
        pygame.display.flip()
        clock.tick(1)  # Increase frame rate for smoother animation

if __name__ == "__main__":
    main()

