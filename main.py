import pygame
import random
import sys
import math
import os

# --- Initialisation de Pygame ---
pygame.init()

# --- Constantes ---

# Configuration de l'écran
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GAME_TITLE = "Zombie Survival + Meteors Mania!"

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
MAGENTA_FALLBACK = (255, 0, 255) # Pour images manquantes

# Joueur
PLAYER_DISPLAY_WIDTH = 40
PLAYER_DISPLAY_HEIGHT = 40
PLAYER_TARGET_SIZE = (PLAYER_DISPLAY_WIDTH, PLAYER_DISPLAY_HEIGHT)
PLAYER_SPEED = 5

# Zombies (Communs et Traqueurs)
ZOMBIE_WIDTH = 30
ZOMBIE_HEIGHT = 30
ZOMBIE_TARGET_SIZE = (ZOMBIE_WIDTH, ZOMBIE_HEIGHT)
ZOMBIE_MIN_SPEED = 1
ZOMBIE_MAX_SPEED = 3
TRACKING_ZOMBIE_SPEED = 1.8

# Météorites
METEORITE_WIDTH = 60
METEORITE_HEIGHT = 60
METEORITE_TARGET_SIZE = (METEORITE_WIDTH, METEORITE_HEIGHT)
METEORITE_MIN_SPEED = 2
METEORITE_MAX_SPEED = 6
METEORITE_DIAG_FACTOR_MIN = 0.3 # Influence l'angle des diagonales
METEORITE_DIAG_FACTOR_MAX = 0.7
METEORITE_TYPES = ['straight', 'diag_left', 'diag_right']

# Gameplay
FPS = 60
INITIAL_ZOMBIE_SPAWN_DELAY = 1500 # ms
MIN_ZOMBIE_SPAWN_DELAY = 250      # ms
ZOMBIE_SPAWN_DECREASE_RATE = 40   # ms par intervalle de difficulté
INITIAL_TRACKING_ZOMBIE_CHANCE = 0.2 # 20%

INITIAL_METEORITE_SPAWN_DELAY = 3500 # ms
MIN_METEORITE_SPAWN_DELAY = 1000     # ms
METEORITE_SPAWN_DECREASE_RATE = 60   # ms par intervalle de difficulté

DIFFICULTY_INCREASE_INTERVAL = 5000 # ms

# --- Configuration de l'écran et Horloge ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()

# --- Fonctions Utilitaires ---

def load_image(filename, target_size=None):
    """
    Charge une image depuis un fichier, la convertit pour Pygame,
    la redimensionne optionnellement et gère les erreurs de chargement.

    Args:
        filename (str): Le nom du fichier image (doit être dans le même dossier).
        target_size (tuple, optional): (width, height) pour redimensionner. Défaut à None.

    Returns:
        pygame.Surface: La surface de l'image chargée (ou une surface de secours).
    """
    filepath = os.path.join(os.path.dirname(__file__), filename)
    try:
        image = pygame.image.load(filepath).convert_alpha() # convert_alpha pour transparence
        if target_size:
             image = pygame.transform.scale(image, target_size)
        return image
    except pygame.error as e:
        print(f"Erreur: Impossible de charger/redimensionner '{filename}': {e}")
        fallback_size = target_size if target_size else (30, 30)
        fallback_surface = pygame.Surface(fallback_size, pygame.SRCALPHA)
        # Dessine un cercle gris comme fallback simple
        try:
            pygame.draw.circle(fallback_surface, GRAY, fallback_surface.get_rect().center, min(fallback_size)//2)
        except Exception as draw_error:
             print(f"Erreur dessin fallback: {draw_error}")
             fallback_surface.fill(MAGENTA_FALLBACK) # Magenta si tout échoue
        return fallback_surface

def draw_text(surface, text, size, x, y, color):
    """Affiche du texte simple sur une surface donnée."""
    font = pygame.font.Font(pygame.font.match_font('arial'), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(midtop=(x, y))
    surface.blit(text_surface, text_rect)

# --- Classes du Jeu ---

class Player(pygame.sprite.Sprite):
    """Représente le personnage joueur."""
    def __init__(self):
        """Initialise le joueur, charge ses images et le positionne."""
        super().__init__()
        # Charger et redimensionner les images directionnelles
        self.images = {
            'nord': load_image('player_nord.png', PLAYER_TARGET_SIZE),
            'sud': load_image('player_sud.png', PLAYER_TARGET_SIZE),
            'est': load_image('player_est.png', PLAYER_TARGET_SIZE),
            'ouest': load_image('player_ouest.png', PLAYER_TARGET_SIZE)
        }
        self.direction = 'sud' # Direction initiale
        self.image = self._get_initial_image()
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.speed = PLAYER_SPEED

    def _get_initial_image(self):
        """Retourne l'image initiale ou une image de secours."""
        img = self.images.get(self.direction)
        if img:
            return img
        else:
            # Si l'image 'sud' manque, essayer une autre
            try:
                return next(iter(self.images.values()))
            except StopIteration: # Si aucune image n'est chargée
                print("Avertissement: Aucune image joueur chargée. Utilisation d'un carré blanc.")
                fallback = pygame.Surface(PLAYER_TARGET_SIZE)
                fallback.fill(WHITE)
                return fallback

    def update(self, keys):
        """Met à jour la position et l'image du joueur en fonction des touches."""
        move_x, move_y = 0, 0
        new_direction = self.direction

        # Détecter le mouvement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y = self.speed

        # Déterminer la nouvelle direction (priorité verticale)
        if move_y < 0: new_direction = 'nord'
        elif move_y > 0: new_direction = 'sud'
        elif move_x < 0: new_direction = 'ouest'
        elif move_x > 0: new_direction = 'est'

        # Changer l'image si la direction change et qu'on bouge
        is_moving = move_x != 0 or move_y != 0
        if is_moving and new_direction != self.direction:
             new_image = self.images.get(new_direction)
             if new_image: # Vérifier si l'image pour cette direction existe
                self.direction = new_direction
                self.image = new_image
                # Important: garder le centre lors du changement d'image pour éviter les sauts
                center = self.rect.center
                self.rect = self.image.get_rect(center=center)

        # Appliquer le mouvement
        self.rect.x += move_x
        self.rect.y += move_y

        # Garder le joueur dans l'écran
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)

class Zombie(pygame.sprite.Sprite):
    """Représente un zombie standard qui se déplace en ligne droite."""
    def __init__(self):
        """Initialise le zombie, charge ses images, définit sa trajectoire."""
        super().__init__()
        # Charger images
        self.images = {
            'nord': load_image('zombie_nord.png', ZOMBIE_TARGET_SIZE),
            'sud': load_image('zombie_sud.png', ZOMBIE_TARGET_SIZE),
            'est': load_image('zombie_est.png', ZOMBIE_TARGET_SIZE),
            'ouest': load_image('zombie_ouest.png', ZOMBIE_TARGET_SIZE)
        }

        # Déterminer la position et vitesse de départ
        spawn_side = random.randint(0, 3)
        speed = random.uniform(ZOMBIE_MIN_SPEED, ZOMBIE_MAX_SPEED)
        dx, dy = 0, 0
        start_x, start_y = 0, 0
        w, h = ZOMBIE_TARGET_SIZE # Dimensions pour le positionnement initial

        # Calcul basé sur le côté d'apparition (0:Haut, 1:Bas, 2:Gauche, 3:Droite)
        if spawn_side == 0: # Haut
            start_x = random.randint(0, SCREEN_WIDTH - w); start_y = -h
            dy = speed; dx = random.uniform(-0.5, 0.5) * speed # Principalement bas
        elif spawn_side == 1: # Bas
            start_x = random.randint(0, SCREEN_WIDTH - w); start_y = SCREEN_HEIGHT
            dy = -speed; dx = random.uniform(-0.5, 0.5) * speed # Principalement haut
        elif spawn_side == 2: # Gauche
            start_x = -w; start_y = random.randint(0, SCREEN_HEIGHT - h)
            dx = speed; dy = random.uniform(-0.5, 0.5) * speed # Principalement droite
        else: # Droite
            start_x = SCREEN_WIDTH; start_y = random.randint(0, SCREEN_HEIGHT - h)
            dx = -speed; dy = random.uniform(-0.5, 0.5) * speed # Principalement gauche

        self.dx, self.dy = dx, dy # Stocker les vitesses pour l'update

        # Déterminer la direction visuelle initiale
        if abs(dy) > abs(dx): # Mouvement vertical dominant
            self.direction = 'sud' if dy > 0 else 'nord'
        else: # Mouvement horizontal dominant (ou égal)
            self.direction = 'est' if dx > 0 else 'ouest'

        # Définir l'image initiale ou fallback
        self.image = self.images.get(self.direction)
        if not self.image:
            print(f"Avertissement: Image manquante pour Zombie direction {self.direction}. Carré rouge.")
            self.image = pygame.Surface(ZOMBIE_TARGET_SIZE); self.image.fill(RED)

        self.rect = self.image.get_rect(topleft=(start_x, start_y))

    def update(self, player): # Accepte 'player' pour cohérence, mais ne l'utilise pas
        """Met à jour la position du zombie selon sa trajectoire initiale."""
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Supprimer le zombie s'il est trop loin hors de l'écran
        margin = 50 # Marge de sécurité
        if (self.rect.right < -margin or self.rect.left > SCREEN_WIDTH + margin or
            self.rect.bottom < -margin or self.rect.top > SCREEN_HEIGHT + margin):
            self.kill() # Se retire de tous les groupes

class TrackingZombie(pygame.sprite.Sprite):
    """Représente un zombie qui suit activement le joueur."""
    def __init__(self):
        """Initialise le zombie traqueur, charge ses images et le positionne."""
        super().__init__()
        # Charger images spécifiques
        self.images = {
            'nord': load_image('zombie_tracking_nord.png', ZOMBIE_TARGET_SIZE),
            'sud': load_image('zombie_tracking_sud.png', ZOMBIE_TARGET_SIZE),
            'est': load_image('zombie_tracking_est.png', ZOMBIE_TARGET_SIZE),
            'ouest': load_image('zombie_tracking_ouest.png', ZOMBIE_TARGET_SIZE)
        }
        self.speed = TRACKING_ZOMBIE_SPEED
        self.direction = 'sud' # Direction initiale par défaut

        # Position de départ aléatoire sur les bords (similaire à Zombie)
        spawn_side = random.randint(0, 3)
        start_x, start_y = 0, 0
        w, h = ZOMBIE_TARGET_SIZE
        if spawn_side == 0: start_x = random.randint(0,SCREEN_WIDTH-w); start_y = -h
        elif spawn_side == 1: start_x = random.randint(0,SCREEN_WIDTH-w); start_y = SCREEN_HEIGHT
        elif spawn_side == 2: start_x = -w; start_y = random.randint(0, SCREEN_HEIGHT-h)
        else: start_x = SCREEN_WIDTH; start_y = random.randint(0, SCREEN_HEIGHT-h)

        # Définir l'image initiale ou fallback
        self.image = self.images.get(self.direction)
        if not self.image:
            try: self.image = next(iter(self.images.values()))
            except StopIteration:
                 print("Avertissement: Aucune image zombie traqueur. Carré bleu.")
                 self.image = pygame.Surface(ZOMBIE_TARGET_SIZE); self.image.fill(BLUE)

        self.rect = self.image.get_rect(topleft=(start_x, start_y))
        # dx/dy sont calculés dynamiquement dans update

    def update(self, player):
        """Met à jour la position et l'image du zombie pour suivre le joueur."""
        # Calculer vecteur direction vers le centre du joueur
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy) # Distance euclidienne

        if distance > 0: # Éviter division par zéro
            # Normaliser le vecteur (longueur 1)
            norm_dx = dx / distance
            norm_dy = dy / distance

            # Calculer le déplacement basé sur la vitesse
            move_x = norm_dx * self.speed
            move_y = norm_dy * self.speed

            # Appliquer le déplacement
            self.rect.x += move_x
            self.rect.y += move_y

            # --- Mise à jour de l'image directionnelle ---
            new_direction = self.direction
            # Déterminer la direction principale du mouvement
            if abs(move_y) > abs(move_x): # Vertical dominant
                new_direction = 'sud' if move_y > 0 else 'nord'
            elif abs(move_x) > abs(move_y): # Horizontal dominant
                 new_direction = 'est' if move_x > 0 else 'ouest'
            # Si égalité, on garde l'ancienne direction pour stabilité visuelle

            # Changer l'image si la direction a changé
            if new_direction != self.direction:
                new_image = self.images.get(new_direction)
                if new_image:
                    self.direction = new_direction
                    self.image = new_image
                    # Garder le centre constant
                    center = self.rect.center
                    self.rect = self.image.get_rect(center=center)

        # Supprimer si trop loin (peut arriver si le joueur est très rapide)
        margin = 150
        if (self.rect.right < -margin or self.rect.left > SCREEN_WIDTH + margin or
            self.rect.bottom < -margin or self.rect.top > SCREEN_HEIGHT + margin):
            self.kill()

class Meteorite(pygame.sprite.Sprite):
    """Représente une météorite tombant du ciel avec différentes trajectoires."""
    def __init__(self, meteor_type='straight'):
        """
        Initialise une météorite d'un type donné ('straight', 'diag_left', 'diag_right').
        Charge l'image appropriée et définit la trajectoire.
        """
        super().__init__()
        self.meteor_type = meteor_type

        # Charger l'image et définir la taille cible selon le type
        if self.meteor_type == 'diag_left':
            image_file = 'meteorite_diag_gauche.png'
            target_size = METEORITE_TARGET_SIZE # Adapter si tailles différentes
        elif self.meteor_type == 'diag_right':
            image_file = 'meteorite_diag_droite.png'
            target_size = METEORITE_TARGET_SIZE
        else: # 'straight' ou type inconnu
            image_file = 'meteorite_straight.png'
            target_size = METEORITE_TARGET_SIZE

        self.image = load_image(image_file, target_size)
        self.rect = self.image.get_rect()

        # Position de départ aléatoire en haut, hors de l'écran
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -self.rect.height - 10) # Commence bien au-dessus

        # Définir la vitesse verticale (dy) et horizontale (dx) selon le type
        self.dy = random.uniform(METEORITE_MIN_SPEED, METEORITE_MAX_SPEED)
        diag_factor = random.uniform(METEORITE_DIAG_FACTOR_MIN, METEORITE_DIAG_FACTOR_MAX)

        if self.meteor_type == 'diag_left':
            self.dx = -diag_factor * self.dy # Vers la gauche, proportionnel à dy
        elif self.meteor_type == 'diag_right':
            self.dx = diag_factor * self.dy  # Vers la droite, proportionnel à dy
        else: # 'straight'
            self.dx = random.uniform(-0.3, 0.3) # Très faible dérive aléatoire

    def update(self):
        """Met à jour la position de la météorite."""
        self.rect.y += self.dy
        self.rect.x += self.dx

        # Supprimer si sorti par le bas de l'écran
        if self.rect.top > SCREEN_HEIGHT + 10: # Marge de 10px
            self.kill()
        # Optionnel: Supprimer si sorti par les côtés (utile pour diagonales)
        # if self.rect.right < -10 or self.rect.left > SCREEN_WIDTH + 10:
        #     self.kill()


# --- Écran de Game Over ---

def show_game_over_screen(current_screen, score):
    """Affiche l'écran de fin de partie et attend une action."""
    # Option: Dessiner le fond du jeu derrière le texte ?
    # current_screen.blit(background_img, (0,0)) # Décommenter si background_img est accessible ici

    current_screen.fill(BLACK) # Fond noir simple
    draw_text(current_screen, "GAME OVER !", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED)
    draw_text(current_screen, f"Temps survécu : {score:.2f} secondes", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE)
    draw_text(current_screen, "Appuyez sur 'R' pour Rejouer ou 'Q' pour Quitter", 18, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4, WHITE)
    pygame.display.flip() # Mettre à jour l'écran

    waiting = True
    while waiting:
        clock.tick(FPS / 2) # Moins de FPS ici, pas besoin de 60
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: # Quitter
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r: # Rejouer
                    waiting = False # Sortir de la boucle pour relancer game_loop

# --- Chargement Image de Fond ---
try:
    background_img = load_image('background.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception as e: # Attrape aussi les erreurs potentielles de load_image
    print(f"Erreur chargement background.png: {e}. Utilisation fond vert.")
    background_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background_img.fill(GREEN)


# --- Boucle Principale du Jeu ---

def game_loop():
    """Lance et gère une partie complète."""

    # --- Initialisation de la partie ---
    all_sprites = pygame.sprite.Group()   # Tous les éléments à dessiner
    zombies = pygame.sprite.Group()       # Pour collisions avec zombies
    meteorites = pygame.sprite.Group()    # Pour collisions avec météorites

    player = Player()
    all_sprites.add(player)

    # Variables de jeu
    running = True
    game_over = False
    final_score = 0
    start_time = pygame.time.get_ticks() # Temps de début de partie
    current_score = 0

    # Configuration du spawn des zombies
    zombie_spawn_timer = 0
    zombie_spawn_delay = INITIAL_ZOMBIE_SPAWN_DELAY
    tracking_zombie_chance = INITIAL_TRACKING_ZOMBIE_CHANCE

    # Configuration du spawn des météorites
    meteorite_spawn_timer = 0
    meteorite_spawn_delay = INITIAL_METEORITE_SPAWN_DELAY

    # Timer pour augmenter la difficulté
    difficulty_increase_timer = 0

    # --- Boucle de Jeu ---
    while running:
        # Contrôler le FPS et obtenir le temps delta (pour mouvements fluides si besoin)
        delta_time = clock.tick(FPS) # en millisecondes

        # --- Gestion des Événements ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False # Sortir de la boucle principale

        # --- Logique du jeu (si pas game over) ---
        if not game_over:

            # --- Mises à jour des Sprites ---
            keys = pygame.key.get_pressed()
            player.update(keys)
            zombies.update(player) # Les zombies ont besoin de connaître la position du joueur
            meteorites.update()    # Les météorites bougent indépendamment

            # --- Augmentation de la Difficulté ---
            difficulty_increase_timer += delta_time
            if difficulty_increase_timer > DIFFICULTY_INCREASE_INTERVAL:
                difficulty_increase_timer = 0 # Réinitialiser le timer
                # Rendre le spawn des zombies plus rapide
                zombie_spawn_delay = max(MIN_ZOMBIE_SPAWN_DELAY, zombie_spawn_delay - ZOMBIE_SPAWN_DECREASE_RATE)
                # Rendre le spawn des météorites plus rapide
                meteorite_spawn_delay = max(MIN_METEORITE_SPAWN_DELAY, meteorite_spawn_delay - METEORITE_SPAWN_DECREASE_RATE)
                # Optionnel: augmenter la chance des traqueurs ?
                # tracking_zombie_chance = min(0.5, tracking_zombie_chance + 0.01)

            # --- Apparition des Zombies ---
            zombie_spawn_timer += delta_time
            if zombie_spawn_timer > zombie_spawn_delay:
                zombie_spawn_timer = 0 # Réinitialiser le timer de spawn zombie
                # Choisir aléatoirement le type de zombie
                if random.random() < tracking_zombie_chance:
                    new_zombie = TrackingZombie()
                else:
                    new_zombie = Zombie()
                # Ajouter le nouveau zombie aux groupes appropriés
                all_sprites.add(new_zombie)
                zombies.add(new_zombie)

            # --- Apparition des Météorites ---
            meteorite_spawn_timer += delta_time
            if meteorite_spawn_timer > meteorite_spawn_delay:
                meteorite_spawn_timer = 0 # Réinitialiser le timer de spawn météorite
                # Choisir aléatoirement le type de météorite
                chosen_type = random.choice(METEORITE_TYPES)
                new_meteorite = Meteorite(meteor_type=chosen_type)
                # Ajouter la nouvelle météorite aux groupes
                all_sprites.add(new_meteorite)
                meteorites.add(new_meteorite)

            # --- Vérification des Collisions ---
            # Collision joueur vs zombies
            # collide_mask est plus précis mais plus lent que collide_rect
            zombie_hits = pygame.sprite.spritecollide(player, zombies, False, pygame.sprite.collide_mask)
            if zombie_hits:
                game_over = True

            # Collision joueur vs météorites
            # dokill=True supprime la météorite du groupe lors de la collision
            meteorite_hits = pygame.sprite.spritecollide(player, meteorites, True, pygame.sprite.collide_mask)
            if meteorite_hits:
                print("Touché par une météorite !") # Message de debug
                game_over = True # Mettre game_over après la collision

            # Calculer le score final seulement si on vient de mourir
            if game_over:
                final_score = (pygame.time.get_ticks() - start_time) / 1000.0

            # --- Calcul du score en temps réel ---
            if not game_over:
                 current_score = (pygame.time.get_ticks() - start_time) / 1000.0

            # --- Dessin ---
            # 1. Dessiner le fond
            screen.blit(background_img, (0, 0))
            # 2. Dessiner tous les sprites (joueur, zombies, météorites)
            all_sprites.draw(screen)
            # 3. Dessiner le score par-dessus
            draw_text(screen, f"Temps: {current_score:.2f}", 24, SCREEN_WIDTH / 2, 10, BLACK)

        # --- Logique de Fin de Partie ---
        else: # si game_over est True
             if running: # Assure qu'on n'a pas déjà cliqué sur Quitter
                 show_game_over_screen(screen, final_score)
                 # Si l'utilisateur appuie sur 'R', show_game_over_screen se termine.
                 # On relance alors une nouvelle partie.
                 game_loop() # Appel récursif pour recommencer
                 # Après l'appel récursif, il faut quitter cette instance de game_loop
                 return # Quitte cette exécution de game_loop proprement

        # --- Mettre à jour l'affichage final ---
        pygame.display.flip()

    # --- Fin de la boucle principale (si running devient False) ---
    pygame.quit() # Nettoyer Pygame
    sys.exit()  # Quitter le programme

# --- Point d'Entrée Principal ---
if __name__ == '__main__':
    # Utiliser un bloc try...except pour attraper les erreurs imprévues globales
    try:
        game_loop() # Lancer la boucle principale du jeu
    except Exception as main_error:
        print(f"Une erreur non gérée est survenue: {main_error}")
        pygame.quit()
        sys.exit()