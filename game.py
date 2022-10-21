import os
from typing import Dict

import pygame
from pygame import Rect, Surface

import color
from constants import *
from controller import Action, Character, MoveCharacterAction

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


class InputProcessor():
    def process(self, inputs: InputStack) -> list[Action]:
        actions = list[Action]()

        x = inputs.compare(pygame.K_d, pygame.K_a)
        y = inputs.compare(pygame.K_s, pygame.K_w)

        if not (x == y == 0):
            actions.append(MoveCharacterAction(x, y))

        return actions


class Game:
    def __init__(self) -> None:
        pygame.init()

        self.image = Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.display = pygame.display.set_mode(
            (DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.RESIZABLE)

        self.background = pygame.image.load("./assets/frog.png", "frog")

        self.inputStack = InputStack()

        self.player = Character()
        self.playerController = InputProcessor()
        self.actions = list[Action]()

        self.clock = pygame.time.Clock()
        self.running = True

    def processInput(self):
        actions = list[Action]()

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.running = False
                    break
                case pygame.KEYDOWN:
                    self.inputStack.append(event.key)
                case pygame.KEYUP:
                    self.inputStack.remove(event.key)
                case _:
                    pass

        actions += self.playerController.process(self.inputStack)

        self.actions = actions

    def update(self):
        self.player.update(self.actions)

    def render(self):
        # Background
        self.image.fill(color.BLACK)

        charPos = self.player.pos

        # Character sprite location on screen
        spriteX = HALF_DISPLAY.x
        if charPos.x < HALF_DISPLAY.x:
            spriteX = charPos.x
        elif (WORLD_WIDTH - charPos.x) < (HALF_DISPLAY.x + CELL_SIZE):
            spriteX = DISPLAY_WIDTH - (WORLD_WIDTH - charPos.x)

        spriteY = HALF_DISPLAY.y
        if charPos.y < HALF_DISPLAY.y:
            spriteY = charPos.y
        elif (WORLD_HEIGHT - charPos.y) < (HALF_DISPLAY.y + CELL_SIZE + CELL_SIZE):
            spriteY = DISPLAY_HEIGHT - (WORLD_HEIGHT - charPos.y)

        # Base
        self.image.blit(self.background, (0, 0),
                        Rect(charPos.x - spriteX, charPos.y - spriteY, DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.image.fill(color.MAGENTA, Rect(
            spriteX, spriteY, CELL_SIZE, CELL_SIZE * 2))

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
