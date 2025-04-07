import pygame
import random
import sys
import math
import os

# --- Initialisation de Pygame ---
pygame.init()

# --- Constantes ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_DISPLAY_WIDTH = 40
PLAYER_DISPLAY_HEIGHT = 40
PLAYER_TARGET_SIZE = (PLAYER_DISPLAY_WIDTH, PLAYER_DISPLAY_HEIGHT)

# ### MODIFIÉ ### : Définir aussi une taille cible pour les zombies
ZOMBIE_WIDTH = 30 # Ajustez si nécessaire
ZOMBIE_HEIGHT = 30 # Ajustez si nécessaire
ZOMBIE_TARGET_SIZE = (ZOMBIE_WIDTH, ZOMBIE_HEIGHT) # Tuple pour scale
# ZOMBIE_SIZE = 25 # L'ancienne constante n'est plus directement utilisée pour le carré

PLAYER_SPEED = 5
ZOMBIE_MIN_SPEED = 1
ZOMBIE_MAX_SPEED = 3

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0) # Gardé comme couleur de secours
GREEN = (0, 255, 0)

# --- Configuration de l'écran ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Survival")

# --- Horloge pour contrôler le FPS ---
clock = pygame.time.Clock()

# --- Helper pour charger les images (inchangé) ---
def load_image(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    try:
        # Tenter de charger l'image
        image = pygame.image.load(filepath)
        # Convertir avec convert_alpha() pour gérer la transparence correctement
        image = image.convert_alpha()
        return image
    except pygame.error as e:
        print(f"Impossible de charger l'image '{filename}': {e}")
        # Créer une surface de secours si l'image est introuvable
        # Utiliser les nouvelles constantes ZOMBIE_WIDTH/HEIGHT pour la taille par défaut
        fallback_surface = pygame.Surface([ZOMBIE_WIDTH, ZOMBIE_HEIGHT])
        fallback_surface.fill((255, 0, 255)) # Magenta pour indiquer l'erreur
        return fallback_surface

# --- Classe pour le Joueur (inchangée) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        original_images = {
            'nord': load_image('player_nord.png'),
            'sud': load_image('player_sud.png'),
            'est': load_image('player_est.png'),
            'west': load_image('player_west.png')
        }
        self.images = {}
        for direction, img in original_images.items():
            self.images[direction] = pygame.transform.scale(img, PLAYER_TARGET_SIZE)

        self.direction = 'sud'
        # Gérer le cas où l'image 'sud' n'a pas pu être chargée
        if self.direction in self.images:
             self.image = self.images[self.direction]
        else:
            # Solution de secours très simple: prendre la première image dispo ou planter
            try:
                self.image = next(iter(self.images.values()))
            except StopIteration:
                 # Si AUCUNE image n'a été chargée, créer un carré blanc
                 print("ERREUR: Aucune image joueur chargée. Utilisation d'un carré blanc.")
                 self.image = pygame.Surface(PLAYER_TARGET_SIZE)
                 self.image.fill(WHITE)

        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) # Positionner par le centre
        self.speed = PLAYER_SPEED

    def update(self, keys):
        move_x = 0
        move_y = 0
        new_direction = self.direction

        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y = self.speed

        # Déterminer la direction basée sur le mouvement
        if move_y < 0: new_direction = 'nord'
        elif move_y > 0: new_direction = 'sud'
        elif move_x < 0: new_direction = 'west'
        elif move_x > 0: new_direction = 'est'

        is_moving = move_x != 0 or move_y != 0
        if is_moving and new_direction != self.direction:
             if new_direction in self.images: # Vérifier si l'image existe
                self.direction = new_direction
                self.image = self.images[self.direction]
                center = self.rect.center # Sauvegarder le centre
                self.rect = self.image.get_rect(center=center) # Recréer le rect centré

        self.rect.x += move_x
        self.rect.y += move_y

        # Contraintes écran
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)


# --- Classe pour les Zombies (MODIFIÉE) ---
class Zombie(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # ### NOUVEAU: Charger les images originales du zombie ###
        original_images = {
            'nord': load_image('zombie_nord.png'),
            'sud': load_image('zombie_sud.png'),
            'est': load_image('zombie_est.png'),
            'ouest': load_image('zombie_ouest.png') # 'ouest' au lieu de 'west' pour correspondre au joueur
        }

        # ### NOUVEAU: Redimensionner les images chargées à la taille cible ###
        self.images = {}
        has_loaded_any = False
        for direction, img in original_images.items():
            # Vérifier si l'image a été chargée correctement (n'est pas la surface de secours)
            # C'est une vérification simple, on pourrait être plus précis
            if img and img.get_width() > 0 and img.get_height() > 0:
                 # Utilise pygame.transform.scale pour redimensionner
                try:
                    self.images[direction] = pygame.transform.scale(img, ZOMBIE_TARGET_SIZE)
                    has_loaded_any = True
                except pygame.error as scale_error:
                    print(f"Erreur de redimensionnement pour zombie_{direction}.png: {scale_error}")
                    # Ne pas ajouter d'image si le redimensionnement échoue
            # else: L'image n'a pas été chargée, ne rien faire

        # ### MODIFIÉ: Déterminer la vitesse et la direction initiale ###
        spawn_side = random.randint(0, 3)
        speed = random.uniform(ZOMBIE_MIN_SPEED, ZOMBIE_MAX_SPEED)
        dx = 0
        dy = 0
        start_x = 0
        start_y = 0

        # Définir dx, dy et position de départ
        temp_rect_width = ZOMBIE_TARGET_SIZE[0] # Utiliser la taille cible pour le spawn
        temp_rect_height = ZOMBIE_TARGET_SIZE[1]

        if spawn_side == 0: # Haut
            start_x = random.randint(0, SCREEN_WIDTH - temp_rect_width)
            start_y = -temp_rect_height
            dx = random.uniform(-0.5, 0.5) * speed
            dy = speed # Principalement vers le bas
        elif spawn_side == 1: # Bas
            start_x = random.randint(0, SCREEN_WIDTH - temp_rect_width)
            start_y = SCREEN_HEIGHT
            dx = random.uniform(-0.5, 0.5) * speed
            dy = -speed # Principalement vers le haut
        elif spawn_side == 2: # Gauche
            start_x = -temp_rect_width
            start_y = random.randint(0, SCREEN_HEIGHT - temp_rect_height)
            dx = speed # Principalement vers la droite
            dy = random.uniform(-0.5, 0.5) * speed
        else: # Droite
            start_x = SCREEN_WIDTH
            start_y = random.randint(0, SCREEN_HEIGHT - temp_rect_height)
            dx = -speed # Principalement vers la gauche
            dy = random.uniform(-0.5, 0.5) * speed

        self.dx = dx
        self.dy = dy

        # ### NOUVEAU: Déterminer la direction visuelle basée sur dx/dy ###
        if abs(self.dy) > abs(self.dx): # Mouvement vertical dominant
            if self.dy > 0:
                self.direction = 'sud'
            else:
                self.direction = 'nord'
        else: # Mouvement horizontal dominant (ou égal)
            if self.dx > 0:
                self.direction = 'est'
            else:
                # Inclut le cas dx == 0 et dy == 0 (peu probable mais sûr)
                self.direction = 'ouest' # 'ouest' comme pour le joueur

        # ### MODIFIÉ: Définir l'image et le rect initiaux ###
        if has_loaded_any and self.direction in self.images:
            self.image = self.images[self.direction]
        else:
            # Fallback: si l'image spécifique manque ou aucune image chargée, utiliser un carré rouge
            if not has_loaded_any:
                print("Aucune image de zombie chargée. Utilisation d'un carré rouge.")
            else:
                 print(f"Image manquante pour zombie direction {self.direction}. Utilisation d'un carré rouge.")

            self.image = pygame.Surface(ZOMBIE_TARGET_SIZE)
            self.image.fill(RED)
            # Si on utilise le fallback, on doit quand même définir une direction "logique"
            # pour éviter les erreurs si on essaie d'y accéder plus tard.
            if not hasattr(self, 'direction'):
                 self.direction = 'sud' # Défaut arbitraire


        self.rect = self.image.get_rect()
        # Positionner le zombie à sa position de départ
        self.rect.x = start_x
        self.rect.y = start_y


    def update(self):
        # Le mouvement est basé sur dx/dy définis à l'initialisation
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Pas besoin de changer self.image ici car dx/dy ne changent pas pour ce zombie
        # Si les zombies devaient changer de direction (ex: suivre le joueur),
        # il faudrait ajouter ici une logique similaire à celle de __init__ pour
        # recalculer la direction et mettre à jour self.image.

        # Condition de suppression si trop loin (inchangée)
        margin = 50 # Une petite marge
        if (self.rect.right < -margin or self.rect.left > SCREEN_WIDTH + margin or
            self.rect.bottom < -margin or self.rect.top > SCREEN_HEIGHT + margin):
            self.kill()


# --- Fonction pour afficher le texte (inchangée) ---
def draw_text(surface, text, size, x, y, color):
    font = pygame.font.Font(pygame.font.match_font('arial'), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

# --- Fonction pour l'écran de Game Over (inchangée) ---
def show_game_over_screen(screen, score):
    screen.fill(BLACK)
    draw_text(screen, "GAME OVER !", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED)
    draw_text(screen, f"Temps survécu : {score:.2f} secondes", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE)
    draw_text(screen, "Appuyez sur 'R' pour Rejouer ou 'Q' pour Quitter", 18, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4, WHITE)
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    waiting = False

# --- Chargement de l'image de fond (inchangé) ---
try:
    background_img_original = load_image('background.png')
    background_img = pygame.transform.scale(background_img_original, (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception as e:
    print(f"Impossible de charger ou redimensionner background.png: {e}")
    print("Utilisation d'un fond vert uni à la place.")
    background_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background_img.fill(GREEN)

# --- Boucle Principale du Jeu (inchangée) ---
def game_loop():
    all_sprites = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    running = True
    game_over = False
    final_score = 0
    start_time = pygame.time.get_ticks()
    zombie_spawn_timer = 0
    zombie_spawn_delay = 1500 # ms
    min_spawn_delay = 200     # ms
    spawn_decrease_rate = 50  # ms
    difficulty_increase_timer = 0
    difficulty_increase_interval = 5000 # ms

    while running:
        delta_time = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not game_over:
            keys = pygame.key.get_pressed()
            player.update(keys)
            zombies.update() # L'update du zombie gère maintenant son image initiale

            difficulty_increase_timer += delta_time
            if difficulty_increase_timer > difficulty_increase_interval:
                difficulty_increase_timer = 0
                zombie_spawn_delay = max(min_spawn_delay, zombie_spawn_delay - spawn_decrease_rate)

            zombie_spawn_timer += delta_time
            if zombie_spawn_timer > zombie_spawn_delay:
                zombie_spawn_timer = 0
                new_zombie = Zombie() # Crée un zombie avec la bonne image initiale
                all_sprites.add(new_zombie)
                zombies.add(new_zombie)

            hits = pygame.sprite.spritecollide(player, zombies, False)
            if hits:
                game_over = True
                final_score = (pygame.time.get_ticks() - start_time) / 1000.0

            current_score = (pygame.time.get_ticks() - start_time) / 1000.0

            # --- Dessin ---
            screen.blit(background_img, (0, 0))
            all_sprites.draw(screen)
            draw_text(screen, f"Temps: {current_score:.2f}", 24, SCREEN_WIDTH / 2, 10, BLACK)

        else:
             if running:
                 show_game_over_screen(screen, final_score)
                 game_loop()
                 return

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# --- Lancer le jeu ---
if __name__ == '__main__':
    try:
        game_loop()
    except Exception as e:
        print(f"Une erreur majeure est survenue: {e}")
        pygame.quit()
        sys.exit()