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

ZOMBIE_WIDTH = 30
ZOMBIE_HEIGHT = 30
ZOMBIE_TARGET_SIZE = (ZOMBIE_WIDTH, ZOMBIE_HEIGHT)

PLAYER_SPEED = 5
ZOMBIE_MIN_SPEED = 1 # Vitesse pour les zombies normaux
ZOMBIE_MAX_SPEED = 3
# ### NOUVEAU ### Vitesse pour les zombies traqueurs
TRACKING_ZOMBIE_SPEED = 1.8 # Un peu plus lent mais constant et direct

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255) # Pour un éventuel fallback du zombie traqueur

# --- Configuration de l'écran ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Survival")

# --- Horloge pour contrôler le FPS ---
clock = pygame.time.Clock()

# --- Helper pour charger les images (inchangé, mais utilisé par les deux zombies) ---
def load_image(filename, target_size=None): # Ajout taille cible optionnelle
    filepath = os.path.join(os.path.dirname(__file__), filename)
    try:
        image = pygame.image.load(filepath).convert_alpha()
        if target_size: # Redimensionner directement si demandé
             image = pygame.transform.scale(image, target_size)
        return image
    except pygame.error as e:
        print(f"Impossible de charger/redimensionner l'image '{filename}': {e}")
        # Utiliser target_size pour le fallback si fourni, sinon une taille par défaut
        fallback_size = target_size if target_size else (30, 30)
        fallback_surface = pygame.Surface(fallback_size)
        fallback_surface.fill((255, 0, 255)) # Magenta
        return fallback_surface

# --- Classe pour le Joueur (inchangée) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Utiliser la fonction load_image modifiée
        self.images = {
            'nord': load_image('player_nord.png', PLAYER_TARGET_SIZE),
            'sud': load_image('player_sud.png', PLAYER_TARGET_SIZE),
            'est': load_image('player_est.png', PLAYER_TARGET_SIZE),
            'west': load_image('player_west.png', PLAYER_TARGET_SIZE) # 'west' ici
        }
        self.direction = 'sud'
        if self.direction in self.images:
             self.image = self.images[self.direction]
        else:
            try: self.image = next(iter(self.images.values()))
            except StopIteration:
                 self.image = pygame.Surface(PLAYER_TARGET_SIZE); self.image.fill(WHITE)

        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.speed = PLAYER_SPEED

    def update(self, keys):
        move_x = 0
        move_y = 0
        # Utiliser 'west' ici pour correspondre aux noms de fichiers/clés
        new_direction = self.direction

        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y = self.speed

        if move_y < 0: new_direction = 'nord'
        elif move_y > 0: new_direction = 'sud'
        elif move_x < 0: new_direction = 'west' # 'west' ici
        elif move_x > 0: new_direction = 'est'

        is_moving = move_x != 0 or move_y != 0
        if is_moving and new_direction != self.direction:
             if new_direction in self.images:
                self.direction = new_direction
                self.image = self.images[self.direction]
                center = self.rect.center
                self.rect = self.image.get_rect(center=center)

        self.rect.x += move_x
        self.rect.y += move_y

        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)


# --- Classe pour les Zombies Normaux (MODIFIÉE pour accepter 'player' dans update) ---
class Zombie(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = {
            'nord': load_image('zombie_nord.png', ZOMBIE_TARGET_SIZE),
            'sud': load_image('zombie_sud.png', ZOMBIE_TARGET_SIZE),
            'est': load_image('zombie_est.png', ZOMBIE_TARGET_SIZE),
            'ouest': load_image('zombie_ouest.png', ZOMBIE_TARGET_SIZE) # 'ouest' ici
        }
        spawn_side = random.randint(0, 3)
        speed = random.uniform(ZOMBIE_MIN_SPEED, ZOMBIE_MAX_SPEED)
        dx = 0
        dy = 0
        start_x = 0
        start_y = 0
        temp_rect_width = ZOMBIE_TARGET_SIZE[0]
        temp_rect_height = ZOMBIE_TARGET_SIZE[1]

        if spawn_side == 0: # Haut
            start_x = random.randint(0, SCREEN_WIDTH - temp_rect_width)
            start_y = -temp_rect_height; dy = speed
            dx = random.uniform(-0.5, 0.5) * speed
        elif spawn_side == 1: # Bas
            start_x = random.randint(0, SCREEN_WIDTH - temp_rect_width)
            start_y = SCREEN_HEIGHT; dy = -speed
            dx = random.uniform(-0.5, 0.5) * speed
        elif spawn_side == 2: # Gauche
            start_x = -temp_rect_width
            start_y = random.randint(0, SCREEN_HEIGHT - temp_rect_height); dx = speed
            dy = random.uniform(-0.5, 0.5) * speed
        else: # Droite
            start_x = SCREEN_WIDTH
            start_y = random.randint(0, SCREEN_HEIGHT - temp_rect_height); dx = -speed
            dy = random.uniform(-0.5, 0.5) * speed

        self.dx = dx
        self.dy = dy

        # Déterminer direction initiale pour l'image
        if abs(self.dy) > abs(self.dx):
            self.direction = 'sud' if self.dy > 0 else 'nord'
        else:
            self.direction = 'est' if self.dx > 0 else 'ouest' # 'ouest' ici

        if self.direction in self.images:
            self.image = self.images[self.direction]
        else:
            self.image = pygame.Surface(ZOMBIE_TARGET_SIZE); self.image.fill(RED)

        self.rect = self.image.get_rect(topleft=(start_x, start_y))

    # ### MODIFIÉ: Accepte 'player' mais ne l'utilise pas ###
    def update(self, player):
        self.rect.x += self.dx
        self.rect.y += self.dy
        margin = 50
        if (self.rect.right < -margin or self.rect.left > SCREEN_WIDTH + margin or
            self.rect.bottom < -margin or self.rect.top > SCREEN_HEIGHT + margin):
            self.kill()

# ### NOUVEAU ### --- Classe pour les Zombies Traqueurs ---
class TrackingZombie(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Utiliser les noms de fichiers fournis, mais clés cohérentes ('ouest')
        self.images = {
            'nord': load_image('zombie_tracking_nord.png', ZOMBIE_TARGET_SIZE),
            'sud': load_image('zombie_tracking_sud.png', ZOMBIE_TARGET_SIZE),
            'est': load_image('zombie_tracking_est.png', ZOMBIE_TARGET_SIZE),
            'ouest': load_image('zombie_tracking_ouest.png', ZOMBIE_TARGET_SIZE) # 'ouest' ici
        }
        self.speed = TRACKING_ZOMBIE_SPEED
        self.direction = 'sud' # Direction initiale par défaut

        # Apparition aléatoire sur les bords (similaire à Zombie)
        spawn_side = random.randint(0, 3)
        start_x = 0
        start_y = 0
        temp_rect_width = ZOMBIE_TARGET_SIZE[0]
        temp_rect_height = ZOMBIE_TARGET_SIZE[1]

        if spawn_side == 0: # Haut
            start_x = random.randint(0, SCREEN_WIDTH - temp_rect_width)
            start_y = -temp_rect_height
        elif spawn_side == 1: # Bas
            start_x = random.randint(0, SCREEN_WIDTH - temp_rect_width)
            start_y = SCREEN_HEIGHT
        elif spawn_side == 2: # Gauche
            start_x = -temp_rect_width
            start_y = random.randint(0, SCREEN_HEIGHT - temp_rect_height)
        else: # Droite
            start_x = SCREEN_WIDTH
            start_y = random.randint(0, SCREEN_HEIGHT - temp_rect_height)

        # Définir l'image initiale et le rect
        if self.direction in self.images:
            self.image = self.images[self.direction]
        else:
            # Fallback si image 'sud' manque ou tout a échoué
             try: self.image = next(iter(self.images.values()))
             except StopIteration:
                 self.image = pygame.Surface(ZOMBIE_TARGET_SIZE); self.image.fill(BLUE) # Bleu pour distinguer

        self.rect = self.image.get_rect(topleft=(start_x, start_y))
        # Pas besoin de dx/dy fixes, ils seront calculés dans update

    # ### NOUVEAU: Méthode update qui suit le joueur ###
    def update(self, player):
        # Calculer le vecteur direction vers le centre du joueur
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        # Calculer la distance
        distance = math.hypot(dx, dy) # Plus direct que sqrt(dx*dx + dy*dy)

        # Normaliser le vecteur (le rendre de longueur 1) et calculer le mouvement
        if distance > 0: # Eviter division par zéro si le zombie est sur le joueur
            norm_dx = dx / distance
            norm_dy = dy / distance
            move_x = norm_dx * self.speed
            move_y = norm_dy * self.speed

            # Appliquer le mouvement
            self.rect.x += move_x
            self.rect.y += move_y

            # Déterminer la nouvelle direction pour l'image
            new_direction = self.direction
            if abs(move_y) > abs(move_x): # Mouvement vertical dominant
                new_direction = 'sud' if move_y > 0 else 'nord'
            elif abs(move_x) > abs(move_y): # Mouvement horizontal dominant
                 new_direction = 'est' if move_x > 0 else 'ouest' # 'ouest' ici
            # Si abs(move_x) == abs(move_y), on garde l'ancienne direction pour éviter des changements trop rapides

            # Mettre à jour l'image si la direction a changé
            if new_direction != self.direction:
                if new_direction in self.images:
                    self.direction = new_direction
                    self.image = self.images[self.direction]
                    # Important: recentrer le rect après changement d'image
                    center = self.rect.center
                    self.rect = self.image.get_rect(center=center)

        # Condition de suppression si trop loin (peut arriver s'il spawn loin et le joueur bouge vite)
        margin = 150 # Marge plus grande car il suit
        if (self.rect.right < -margin or self.rect.left > SCREEN_WIDTH + margin or
            self.rect.bottom < -margin or self.rect.top > SCREEN_HEIGHT + margin):
            self.kill()


# --- Fonction pour afficher le texte (inchangée) ---
def draw_text(surface, text, size, x, y, color):
    font = pygame.font.Font(pygame.font.match_font('arial'), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(midtop=(x, y))
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
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: pygame.quit(); sys.exit()
                if event.key == pygame.K_r: waiting = False

# --- Chargement de l'image de fond (inchangé) ---
try:
    background_img_original = load_image('background.png')
    background_img = pygame.transform.scale(background_img_original, (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception as e:
    print(f"Impossible de charger background.png: {e}. Fond vert utilisé.")
    background_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); background_img.fill(GREEN)

# --- Boucle Principale du Jeu (MODIFIÉE pour spawn et update) ---
def game_loop():
    all_sprites = pygame.sprite.Group()
    zombies = pygame.sprite.Group() # Ce groupe contiendra les deux types
    player = Player()
    all_sprites.add(player)

    running = True
    game_over = False
    final_score = 0
    start_time = pygame.time.get_ticks()

    # Variables de spawn
    zombie_spawn_timer = 0
    zombie_spawn_delay = 1500 # ms
    min_spawn_delay = 250     # ms (augmenté un peu car traqueurs plus dangereux)
    spawn_decrease_rate = 40  # ms
    difficulty_increase_timer = 0
    difficulty_increase_interval = 5000 # ms
    # ### NOUVEAU: Probabilité de spawn un traqueur ###
    tracking_zombie_chance = 0.2 # 20% de chance qu'un zombie soit un traqueur

    while running:
        delta_time = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        if not game_over:
            keys = pygame.key.get_pressed()
            player.update(keys)
            # ### MODIFIÉ: Passer l'objet 'player' à l'update du groupe ###
            zombies.update(player) # Les deux types de zombies utilisent cet appel

            # Difficulté croissante
            difficulty_increase_timer += delta_time
            if difficulty_increase_timer > difficulty_increase_interval:
                difficulty_increase_timer = 0
                zombie_spawn_delay = max(min_spawn_delay, zombie_spawn_delay - spawn_decrease_rate)
                # Optionnel: augmenter la chance d'avoir des traqueurs avec le temps
                # tracking_zombie_chance = min(0.5, tracking_zombie_chance + 0.02) # Plafonné à 50%

            # Apparition des zombies
            zombie_spawn_timer += delta_time
            if zombie_spawn_timer > zombie_spawn_delay:
                zombie_spawn_timer = 0
                # ### MODIFIÉ: Choisir quel type de zombie créer ###
                if random.random() < tracking_zombie_chance:
                    new_zombie = TrackingZombie()
                else:
                    new_zombie = Zombie()
                all_sprites.add(new_zombie)
                zombies.add(new_zombie) # Ajouter au même groupe pour collisions/dessin

            # Vérification des collisions (inchangé, fonctionne pour les deux types)
            hits = pygame.sprite.spritecollide(player, zombies, False, pygame.sprite.collide_mask) # collide_mask est plus précis
            # hits = pygame.sprite.spritecollide(player, zombies, False) # Si collide_mask pose problème
            if hits:
                game_over = True
                final_score = (pygame.time.get_ticks() - start_time) / 1000.0

            current_score = (pygame.time.get_ticks() - start_time) / 1000.0

            # --- Dessin ---
            screen.blit(background_img, (0, 0))
            all_sprites.draw(screen) # Dessine tous les sprites (joueur, zombies, traqueurs)
            draw_text(screen, f"Temps: {current_score:.2f}", 24, SCREEN_WIDTH / 2, 10, BLACK)

        else:
             if running:
                 show_game_over_screen(screen, final_score)
                 game_loop() # Relance
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