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
# Définir la taille souhaitée pour l'affichage du joueur
PLAYER_DISPLAY_WIDTH = 40
PLAYER_DISPLAY_HEIGHT = 40 # Ajustez ces valeurs selon vos préférences
PLAYER_TARGET_SIZE = (PLAYER_DISPLAY_WIDTH, PLAYER_DISPLAY_HEIGHT) # Tuple pour scale

ZOMBIE_SIZE = 25
PLAYER_SPEED = 5
ZOMBIE_MIN_SPEED = 1
ZOMBIE_MAX_SPEED = 3

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0) # Gardé comme couleur de secours

# --- Configuration de l'écran ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Survival")

# --- Horloge pour contrôler le FPS ---
clock = pygame.time.Clock()

# --- Helper pour charger les images (inchangé) ---
def load_image(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    try:
        image = pygame.image.load(filepath).convert_alpha()
        return image
    except pygame.error as e:
        print(f"Impossible de charger l'image '{filename}': {e}")
        fallback_surface = pygame.Surface([30, 30]) # Taille par défaut si erreur
        fallback_surface.fill((255, 0, 255))
        return fallback_surface

# --- Classe pour le Joueur (inchangée) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # Charger les images originales
        original_images = {
            'nord': load_image('player_nord.png'),
            'sud': load_image('player_sud.png'),
            'est': load_image('player_est.png'),
            'west': load_image('player_west.png')
        }

        # Redimensionner les images chargées à la taille cible
        self.images = {}
        for direction, img in original_images.items():
            # Utilise pygame.transform.scale pour redimensionner
            self.images[direction] = pygame.transform.scale(img, PLAYER_TARGET_SIZE)

        # --- Le reste de __init__ est identique à avant ---
        # Vérifier si toutes les images ont été chargées (optionnel mais bon pour le debug)
        # Note: On vérifie toujours original_images au cas où le load échoue AVANT le scale
        # Simplifié pour être plus proche de l'original : on suppose que ça charge
        # if not all(original_images.values()):
        #      raise ValueError("Une ou plusieurs images du joueur n'ont pas pu être chargées.")

        # Image initiale et direction
        self.direction = 'sud'
        self.image = self.images[self.direction] # Utilise l'image redimensionnée
        self.rect = self.image.get_rect() # Obtient le rect de l'image redimensionnée

        # Position de départ au centre (utilisera la largeur/hauteur du rect redimensionné)
        self.rect.x = SCREEN_WIDTH // 2 - self.rect.width // 2
        self.rect.y = SCREEN_HEIGHT // 2 - self.rect.height // 2
        self.speed = PLAYER_SPEED

    # --- La méthode update reste exactement la même qu'avant ---
    def update(self, keys):
        move_x = 0
        move_y = 0
        new_direction = self.direction # Garde l'ancienne direction par défaut

        # Détection des touches pour le mouvement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -self.speed
            # new_direction = 'west' # On détermine la direction après
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = self.speed
            # new_direction = 'est'
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y = -self.speed
            # new_direction = 'nord'
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y = self.speed
            # new_direction = 'sud'

        # Détermination de la direction (priorité Y puis X)
        # Cette logique peut être simplifiée si désiré, mais gardée pour cohérence avec l'original
        if move_y != 0:
             if move_y < 0: new_direction = 'nord'
             else: new_direction = 'sud'
        elif move_x != 0: # Ne change la direction basée sur X que si Y est nul
             if move_x < 0: new_direction = 'west'
             else: new_direction = 'est'

        # Mise à jour de l'image si la direction change et qu'on bouge
        is_moving = move_x != 0 or move_y != 0
        if is_moving and new_direction != self.direction:
            self.direction = new_direction
            self.image = self.images[self.direction] # Sélectionne l'image redimensionnée
            # Recalculer le rect en gardant le centre pour éviter les sauts
            center = self.rect.center
            self.rect = self.image.get_rect(center=center)

        # Appliquer le mouvement
        self.rect.x += move_x
        self.rect.y += move_y

        # Garder le joueur dans les limites de l'écran
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

# --- Classe pour les Zombies (inchangée) ---
class Zombie(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Optionnel: Charger une image de zombie
        # self.original_image = load_image('zombie.png')
        # self.image = pygame.transform.scale(self.original_image, (ZOMBIE_SIZE, ZOMBIE_SIZE))
        # self.rect = self.image.get_rect()
        # Si pas d'image de zombie, garder le carré rouge:
        self.image = pygame.Surface([ZOMBIE_SIZE, ZOMBIE_SIZE])
        self.image.fill(RED)
        self.rect = self.image.get_rect()

        spawn_side = random.randint(0, 3)
        speed = random.uniform(ZOMBIE_MIN_SPEED, ZOMBIE_MAX_SPEED)
        # Calcul de la direction basé sur la vitesse (simple)
        # Note: L'original utilisait dx/dy directement, gardons cette approche
        dx = 0
        dy = 0

        if spawn_side == 0: # Haut
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
            self.rect.y = -self.rect.height
            dx = random.uniform(-0.5, 0.5) * speed # Direction légèrement aléatoire
            dy = speed # Va principalement vers le bas
        elif spawn_side == 1: # Bas
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
            self.rect.y = SCREEN_HEIGHT
            dx = random.uniform(-0.5, 0.5) * speed
            dy = -speed # Va principalement vers le haut
        elif spawn_side == 2: # Gauche
            self.rect.x = -self.rect.width
            self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)
            dx = speed # Va principalement vers la droite
            dy = random.uniform(-0.5, 0.5) * speed
        else: # Droite
            self.rect.x = SCREEN_WIDTH
            self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)
            dx = -speed # Va principalement vers la gauche
            dy = random.uniform(-0.5, 0.5) * speed

        # Stocker dx et dy pour l'update
        self.dx = dx
        self.dy = dy

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        # Condition de suppression si trop loin (inchangée)
        if (self.rect.right < -50 or self.rect.left > SCREEN_WIDTH + 50 or
            self.rect.bottom < -50 or self.rect.top > SCREEN_HEIGHT + 50):
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
    screen.fill(BLACK) # Fond noir simple comme dans l'original
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
                    waiting = False # Sort de la boucle pour relancer

# ### NOUVEAU ### --- Chargement de l'image de fond ---
try:
    background_img_original = load_image('background.png')
    # Redimensionner pour s'assurer qu'elle correspond à la taille de l'écran
    background_img = pygame.transform.scale(background_img_original, (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception as e:
    print(f"Impossible de charger ou redimensionner background.png: {e}")
    print("Utilisation d'un fond vert uni à la place.")
    # Créer une surface verte de secours si l'image manque ou erreur
    background_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background_img.fill(GREEN)

# --- Boucle Principale du Jeu (Seule modification : screen.fill -> screen.blit) ---
def game_loop():
    all_sprites = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    running = True
    game_over = False
    # score = 0 # Le score est calculé dynamiquement plus bas
    final_score = 0 # Besoin d'une variable pour le score final
    start_time = pygame.time.get_ticks()
    zombie_spawn_timer = 0
    zombie_spawn_delay = 1500 # ms
    min_spawn_delay = 200     # ms
    spawn_decrease_rate = 50  # ms
    difficulty_increase_timer = 0
    difficulty_increase_interval = 5000 # ms

    while running:
        delta_time = clock.tick(60) # Obtenir le temps écoulé (en ms) et limiter FPS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                # Ne pas mettre game_over ici, on quitte directement
                # Si on ferme la fenêtre, le jeu s'arrête

        if not game_over:
            # Mises à jour
            keys = pygame.key.get_pressed()
            player.update(keys)
            zombies.update()

            # Difficulté croissante (inchangé)
            difficulty_increase_timer += delta_time
            if difficulty_increase_timer > difficulty_increase_interval:
                difficulty_increase_timer = 0
                zombie_spawn_delay = max(min_spawn_delay, zombie_spawn_delay - spawn_decrease_rate)

            # Apparition des zombies (inchangé)
            zombie_spawn_timer += delta_time
            if zombie_spawn_timer > zombie_spawn_delay:
                zombie_spawn_timer = 0
                new_zombie = Zombie()
                all_sprites.add(new_zombie)
                zombies.add(new_zombie)

            # Vérification des collisions (inchangé)
            hits = pygame.sprite.spritecollide(player, zombies, False)
            if hits:
                game_over = True
                final_score = (pygame.time.get_ticks() - start_time) / 1000.0 # Calculer score final ici

            # Calcul du score affiché (temps actuel)
            # On le calcule ici pour l'afficher en continu
            current_score = (pygame.time.get_ticks() - start_time) / 1000.0

            # --- Dessin ---
            # ### MODIFIÉ ### : Remplacer screen.fill par screen.blit
            # screen.fill(GREEN) # Ancienne ligne
            screen.blit(background_img, (0, 0)) # Nouvelle ligne: dessine l'image de fond

            # Dessiner les sprites par dessus le fond
            all_sprites.draw(screen)
            # Dessiner le score par dessus tout
            draw_text(screen, f"Temps: {current_score:.2f}", 24, SCREEN_WIDTH / 2, 10, BLACK)

        else: # Si game_over est True
             if running: # Vérifier si on n'a pas déjà décidé de quitter
                 show_game_over_screen(screen, final_score)
                 # Après show_game_over_screen, si on appuie sur 'R', on revient ici.
                 # Pour relancer, il faut réinitialiser ou appeler à nouveau game_loop.
                 # L'appel récursif est le plus simple ici, comme dans l'original.
                 game_loop() # Relance une nouvelle partie
                 return # Important pour sortir proprement de l'instance actuelle de game_loop

        # Mettre à jour l'affichage
        pygame.display.flip()

    # Fin de la boucle principale (si running devient False)
    pygame.quit()
    sys.exit()

# --- Lancer le jeu ---
if __name__ == '__main__':
    # Ajout d'un try/except global simple pour attraper les erreurs imprévues
    try:
        game_loop()
    except Exception as e:
        print(f"Une erreur majeure est survenue: {e}")
        pygame.quit()
        sys.exit()