import pygame
import random
from itertools import *

from particles import create_particles, generate_particles
from sprites import Sprite
from load_image import load_image

from settings import *


class Triangle(Sprite):
    def __init__(self, pos, particles_g, bullet_g, player, *group):
        super().__init__(*group)
        self.image = load_image('triangle')
        self.rect = self.image.get_rect()

        self.rect.center = pos

        self.elapsed_time = 0
        self.max_speed = random.randint(30, 50) / 10
        self.speed = self.max_speed
        self.health = 2
        self.max_health = 2
        self.damage = 1
        self.score_weight = int(
            self.max_speed + self.health + self.damage) // 2

        self.dx = 0
        self.dy = 0

        self.particles_g = particles_g
        self.bullet_g = bullet_g
        self.player = player

        self.damage_timer = 0

        self.hitbox = pygame.Rect(0, 0, 30, 30)
        self.hitbox.topleft = (
            self.rect.centerx + - self.hitbox.w // 2,
            self.rect.centery + - self.hitbox.h // 2)

        self.acceleration = 0.7  # How quickly the enemy accelerates
        self.deceleration = 0.3  # How quickly the enemy decelerates
        self.velocity = pygame.Vector2(0, 0)  # Current velocity
        self.recovering = False  # Track if the enemy is recovering after the hit

    def update(self, screen, screen_rect, target_pos, dt):
        self.move(target_pos, dt)
        self.bullet_check()
        self.draw_health_bar(screen)
        self.player_check()

        # Handle damage cooldown and recovery
        if self.damage_timer < 120:
            self.damage_timer += dt
            self.recovering = True
        else:
            self.speed = self.max_speed
            self.recovering = False  # Stop recovering when cooldown is done

    def move(self, target_pos, dt):
        direction = pygame.Vector2(target_pos) - pygame.Vector2(self.rect.center)

        if direction.length() > 0:
            direction = direction.normalize()

            # If recovering (after hitting the player), decelerate
            if self.recovering:
                self.velocity.x -= self.velocity.x * self.deceleration * 0.5 * dt
                self.velocity.y -= self.velocity.y * self.deceleration * 0.5 * dt
            else:
                # Normal acceleration towards the target
                self.velocity.x += direction.x * self.acceleration * dt
                self.velocity.y += direction.y * self.acceleration * dt
        else:
            # Decelerate when no input
            if self.velocity.length() > 0:
                self.velocity.x -= self.velocity.x * self.deceleration * dt
                self.velocity.y -= self.velocity.y * self.deceleration * dt

        # Cap velocity to max speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        # Update position based on velocity
        self.rect.centerx += self.velocity.x * dt
        self.hitbox.centerx += self.velocity.x * dt
        self.rect.centery += self.velocity.y * dt
        self.hitbox.centery += self.velocity.y * dt

    def bullet_check(self):
        for bullet in self.bullet_g:
            if self.rect.colliderect(bullet.rect):
                self.health -= 1
                bullet.kill()
                if self.health:
                    play_sound('enemy_hit')
                    create_particles(self.rect.center,
                                     generate_particles('particle'),
                                     30, 15,
                                     self.particles_g)
                else:
                    self.player.score += self.score_weight
                    play_sound('explosion')
                    create_particles(self.rect.center,
                                     generate_particles('particle'),
                                     50, 30,
                                     self.particles_g)
                    self.kill()

    def player_check(self):
        if self.damage_timer >= 120:
            if self.hitbox.colliderect(self.player.hitbox):
                self.player.health -= self.damage
                self.damage_timer = 0
                self.recovering = True  # Start recovering after hitting the player
                play_sound('hit')
                create_particles(self.player.rect.center,
                                 generate_particles('particle'),
                                 50, 20,
                                 self.particles_g)

    def draw_health_bar(self, screen):
        pygame.draw.rect(screen, pygame.Color('#306230'),
                         pygame.Rect(self.rect.centerx - 15, self.rect.y - 10,
                                     30, 5))
        pygame.draw.rect(screen, pygame.Color('#8bac0f'),
                         pygame.Rect(self.rect.centerx - 15, self.rect.y - 10,
                                     30 / self.max_health * self.health, 5))



class Square(Triangle):
    def __init__(self, pos, particles_g, bullet_g, player, *group):
        super().__init__(pos, particles_g, bullet_g, player, *group)
        self.image = load_image('square')
        self.rect = self.image.get_rect()

        self.rect.center = pos

        self.elapsed_time = 0
        self.speed = random.randint(10, 20) / 10
        self.health = 4
        self.max_health = 4
        self.damage = 2
        self.score_weight = int(
            self.max_speed + self.health + self.damage) // 2

        self.dx = 0
        self.dy = 0

        self.particles_g = particles_g
        self.bullet_g = bullet_g
        self.player = player

        self.damage_timer = 0

        self.hitbox = pygame.Rect(0, 0, 40, 40)
        self.hitbox.topleft = (
            self.rect.centerx + - self.hitbox.w // 2,
            self.rect.centery + - self.hitbox.h // 2)

        self.acceleration = 0.1  # How quickly the player accelerates
        self.deceleration = 0.05  # How quickly the player decelerates
        self.velocity = pygame.Vector2(0, 0)  # Current velocity


class EnemySpawn:
    def __init__(self, group, particles_g, bullet_g, player):
        self.elapsed_time = 0
        self.spawn_time = 30
        self.group = group
        self.particles_g = particles_g
        self.bullet_g = bullet_g
        self.player = player

    def update(self, dt):
        self.elapsed_time += dt

        if self.elapsed_time >= self.spawn_time and len(self.group) < 10:
            self.elapsed_time = 0

            x = chain(range(-SW - 400, -SW - 200),
                      range(SW + 200, SW + 400))
            y = chain(range(-SH - 400, -SH - 200),
                      range(SH + 200, SH + 400))
            pos = random.choice(list(x)), random.choice(list(y))

            enemy_type = \
            random.choices(['square', 'triangle'], weights=(3, 7), k=1)[0]
            if enemy_type == 'square':
                enemy = Square(pos, self.particles_g, self.bullet_g,
                               self.player, self.group)
            else:
                enemy = Triangle(pos, self.particles_g, self.bullet_g,
                                 self.player, self.group)
            self.group.add(enemy)
