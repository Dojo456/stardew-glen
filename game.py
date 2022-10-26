import os
import time
from typing import Dict

import pygame
from pygame import Rect, Surface
from pytmx import TiledTileLayer  # type: ignore

import color
from constants import *
from controller import (Action, ChangeInventorySelectionAction, Character,
                        CharacterState, Coord, MoveCharacterAction,
                        PlantCropAction, Tile, World)

os.environ['SDL_VIDEO_CENTERED'] = '1'


INVENTORY_KEYS = [
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
    pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8,
    pygame.K_9, pygame.K_0, pygame.K_MINUS, pygame.K_EQUALS
]


class InputStack:
    def __init__(self) -> None:
        self.count = 0
        self.dict: Dict[int, int] = {}
        self._awaitingRelease = set[int]()

    def append(self, key: int):
        if key not in self._awaitingRelease:
            self.count += 1
            self.dict[key] = self.count

    def remove(self, key: int):
        if self.dict.pop(key, -1) != -1:
            self.count -= 1
        try:
            self._awaitingRelease.remove(key)
        except KeyError:
            pass

    def has(self, key: int):
        return key in self.dict

    def consume(self, key: int):
        contains = False

        if self.dict.pop(key, -1) != -1:
            self._awaitingRelease.add(key)
            self.count -= 1

            contains = True

        return contains

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

    def highest(self, keys: list[int]):
        sorted = keys.copy()

        anyPressed = False

        def key(x: int):
            nonlocal anyPressed
            val = self.dict.get(x, -1)

            if val != -1:
                anyPressed = True

            return val

        sorted.sort(key=key, reverse=True)

        return sorted[0] if anyPressed else -1


class DrawableCharacter(Character):
    def __init__(self, identifier: str, tileSet: str, world: World) -> None:
        super().__init__(world)

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
            (col * CELL_SIZE) + 21, (row * CELL_SIZE * 2) + 46, CELL_SIZE, CELL_SIZE * 2))
        image.set_colorkey(color.MAGENTA)

        return image


class DrawableWorld(World):
    def __init__(self) -> None:
        super().__init__()

        self.image = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

        for layer in self.mapData.layers:  # type: ignore
            if isinstance(layer, TiledTileLayer):
                for x, y, image in layer.tiles():  # type: ignore
                    if isinstance(image, pygame.Surface):
                        self.image.blit(image, (x * CELL_SIZE, y * CELL_SIZE))

        self.dirtTileSet = pygame.image.load("./assets/hoed.png", "hoed dirt")

        self.overlayImage = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        self.overlayImage.fill(color.MAGENTA)
        self.overlayImage.set_colorkey(color.MAGENTA)

    def addTile(self, tile: Tile):
        self.overlayImage.blit(self.dirtTileSet, (tile.pos.x * CELL_SIZE,
                                                  tile.pos.y * CELL_SIZE), Rect(0, 0, CELL_SIZE, CELL_SIZE))

        return super().addTile(tile)

    def removeTile(self, pos: Coord):
        self.overlayImage.fill(color.MAGENTA, Rect(pos.x * CELL_SIZE,
                                                   pos.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        return super().removeTile(pos)


class Game:
    def __init__(self) -> None:
        pygame.init()

        self.image = Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.display = pygame.display.set_mode(
            (DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.RESIZABLE)

        self.background = pygame.image.load("./assets/frog.png", "frog")
        self.defaultFont = pygame.font.Font("./assets/font.ttf", 16)

        self.inputs = InputStack()

        self.world = DrawableWorld()
        self.player = DrawableCharacter(
            "player", "./assets/penny.png", self.world)
        self.actions = list[Action]()

        self.clock = pygame.time.Clock()
        self.running = True

    mouseReleased = True

    def captureInputs(self):
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                break
            elif event.type == pygame.KEYDOWN:
                self.inputs.append(event.key)
            elif event.type == pygame.KEYUP:
                self.inputs.remove(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.inputs.append(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.inputs.remove(event.button)

    def processInputs(self):
        actions = list[Action]()

        x = self.inputs.compare(pygame.K_d, pygame.K_a)
        y = self.inputs.compare(pygame.K_s, pygame.K_w)

        if not (x == y == 0):
            actions.append(MoveCharacterAction(x, y))

        if self.inputs.consume(pygame.BUTTON_LEFT):
            pos = self.player.closestTile
            actions.append(PlantCropAction(pos))

        inventorySelection = self.inputs.highest(INVENTORY_KEYS)

        if inventorySelection != -1:
            actions.append(ChangeInventorySelectionAction(
                INVENTORY_KEYS.index(inventorySelection)))

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
        self.image.blit(self.world.overlayImage, (0, 0),
                        Rect(playerPos.x - spriteX, playerPos.y - spriteY, DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # Character
        self.image.blit(self.player.image(), (spriteX, spriteY))

        # HUD Elements

        # FPS Counter
        fpsSurface = self.defaultFont.render(
            str(round(self.clock.get_fps())), False, color.GREEN)
        fpsRect = fpsSurface.get_rect()
        self.image.blit(
            fpsSurface, (0, DISPLAY_HEIGHT-fpsRect.height), fpsRect)

        # Coin Counter
        coinsSurface = self.defaultFont.render(
            str(self.world.coins), False, color.RED4
        )
        coinsRect = coinsSurface.get_rect()
        self.image.blit(
            coinsSurface, (DISPLAY_WIDTH-coinsRect.width-5, 5), coinsRect)

        # Inventory Selection
        inventorySlotPos = Vector2(
            72 + (self.world.inventorySelection * 20), DISPLAY_HEIGHT - 25)
        self.image.fill(color.RED1, Rect(
            inventorySlotPos.x, inventorySlotPos.y, 20, 20))
        inventorySlotText = self.defaultFont.render(
            str(self.world.inventorySelection), False, color.BLACK)
        self.image.blit(inventorySlotText, inventorySlotPos +
                        Vector2((20 - inventorySlotText.get_width()) / 2,
                                (20 - inventorySlotText.get_height()) / 2,
                                ))

        pygame.transform.scale(
            self.image, self.display.get_size(), self.display)
        pygame.display.update()

    def run(self):
        while self.running:
            self.captureInputs()
            self.processInputs()
            self.update()
            self.render()
            self.clock.tick(FRAME_LIMIT)


game = Game()
game.run()

pygame.quit()
