import os
import time
from typing import Dict

import pygame
from pygame import Rect, Surface

import color
from constants import *
from controller import (Action, Character, CharacterState, MoveCharacterAction,
                        PlantCropAction, Tile, World)

os.environ['SDL_VIDEO_CENTERED'] = '1'


class InputStack:
    def __init__(self) -> None:
        self.count = 0
        self.dict: Dict[int, int] = {}

    def append(self, key: int):
        self.count += 1
        self.dict[key] = self.count

    def remove(self, key: int):
        self.dict.pop(key, -1)

    def has(self, key: int):
        return self.dict.__contains__(key)

    def compare(self, key1: int, key2: int) -> int:
        """
        compare returns 1 is key1 is of higher precedence, -1
        if key2 is higher, or 0 if neither keys are pressed.
        If a key has not been pressed, it has the lowest possible
        precedence.
        """

        val1 = self.dict.get(key1) or -1
        val2 = self.dict.get(key2) or -1

        if val1 == val2:
            return 0

        return 1 if val1 > val2 else -1


class DrawableCharacter(Character):
    def __init__(self, identifier: str, tileSet: str) -> None:
        super().__init__()

        self.identifier = identifier
        self.tileSet = pygame.image.load(tileSet)

        self.epoch = time.time_ns()
        self.tick = 0
        self.accumulated = 0

    def image(self) -> Surface:
        row = 0
        col = self.tick

        if self.state == CharacterState.STANDING:
            row = int(self.direction.value)
            col = 0
        elif self.state == CharacterState.WALKING:
            row = int(self.direction.value)

        image = Surface((CELL_SIZE, CELL_SIZE * 2))
        image.blit(self.tileSet, (0, 0), Rect(
            (col * CELL_SIZE) + 22, (row * CELL_SIZE * 2) + 51, CELL_SIZE, CELL_SIZE * 2))
        image.set_colorkey(color.MAGENTA)

        return image


class DrawableWorld(World):
    def __init__(self) -> None:
        super().__init__()

        self.dirtTileSet = pygame.image.load("./assets/hoed.png", "hoed dirt")
        self.image = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        self.image.fill(color.MAGENTA)

        self.image.set_colorkey(color.MAGENTA)

    def addTile(self, tile: Tile):
        self.image.blit(self.dirtTileSet, (tile.pos.x * CELL_SIZE,
                        tile.pos.y * CELL_SIZE), Rect(0, 0, CELL_SIZE, CELL_SIZE))

        return super().addTile(tile)


class Game:
    def __init__(self) -> None:
        pygame.init()

        self.image = Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.display = pygame.display.set_mode(
            (DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.RESIZABLE)

        self.background = pygame.image.load("./assets/frog.png", "frog")

        self.inputs = InputStack()

        self.player = DrawableCharacter("player", "./assets/penny.png")
        self.world = DrawableWorld()
        self.actions = list[Action]()

        self.clock = pygame.time.Clock()
        self.running = True

    mouseReleased = True

    def processInput(self):
        actions = list[Action]()

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.running = False
                    break
                case pygame.KEYDOWN:
                    self.inputs.append(event.key)
                    print(event.key)
                case pygame.KEYUP:
                    self.inputs.remove(event.key)
                case pygame.MOUSEBUTTONDOWN:
                    b = event.button
                    a = -1

                    match(b):
                        case 1:
                            a = pygame.BUTTON_LEFT
                        case 2:
                            a = pygame.BUTTON_MIDDLE
                        case 3:
                            a = pygame.BUTTON_RIGHT
                        case _:
                            pass

                    self.inputs.append(a)
                case pygame.MOUSEBUTTONUP:
                    b = event.button
                    r = -1

                    match(b):
                        case 1:
                            r = pygame.BUTTON_LEFT
                            self.mouseReleased = True
                        case 2:
                            r = pygame.BUTTON_MIDDLE
                        case 3:
                            r = pygame.BUTTON_RIGHT
                        case _:
                            pass

                    self.inputs.remove(r)
                case _:
                    pass

        actions = list[Action]()

        x = self.inputs.compare(pygame.K_d, pygame.K_a)
        y = self.inputs.compare(pygame.K_s, pygame.K_w)

        if not (x == y == 0):
            actions.append(MoveCharacterAction(x, y))

        if self.inputs.has(pygame.BUTTON_LEFT):
            if self.mouseReleased:
                pos = self.player.closestTile
                pos.y += 1
                actions.append(PlantCropAction(pos))
                self.mouseReleased = False

        self.actions = actions

    def update(self):
        self.player.update(self.actions)
        self.world.update(self.actions)

    def render(self):
        # Background
        self.image.fill(color.BLACK)

        playerPos = self.player.pos

        # Character sprite location on screen
        spriteX = HALF_DISPLAY.x
        if playerPos.x < HALF_DISPLAY.x:
            spriteX = playerPos.x
        elif (WORLD_WIDTH - playerPos.x) < (HALF_DISPLAY.x + CELL_SIZE):
            spriteX = DISPLAY_WIDTH - (WORLD_WIDTH - playerPos.x)

        spriteY = HALF_DISPLAY.y
        if playerPos.y < HALF_DISPLAY.y:
            spriteY = playerPos.y
        elif (WORLD_HEIGHT - playerPos.y) < (HALF_DISPLAY.y + CELL_SIZE + CELL_SIZE):
            spriteY = DISPLAY_HEIGHT - (WORLD_HEIGHT - playerPos.y)

        # Base
        self.image.blit(self.background, (0, 0),
                        Rect(playerPos.x - spriteX, playerPos.y - spriteY, DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # World Elements
        self.image.blit(self.world.image, (0, 0),
                        Rect(playerPos.x - spriteX, playerPos.y - spriteY, DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # Character
        self.image.blit(self.player.image(), (spriteX, spriteY))

        pygame.transform.scale(
            self.image, self.display.get_size(), self.display)
        pygame.display.update()

    def run(self):
        while self.running:
            self.processInput()
            self.update()
            self.render()
            self.clock.tick(FRAME_LIMIT)


game = Game()
game.run()

pygame.quit()
