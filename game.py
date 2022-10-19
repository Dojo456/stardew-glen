import enum
import os
import time
from math import trunc
from typing import Dict

import pygame
from pygame import Rect, Surface, Vector2

import color

os.environ['SDL_VIDEO_CENTERED'] = '1'

FRAME_LIMIT = 144

CELL_SIZE = 32

BOARD_WIDTH = 32 * CELL_SIZE
BOARD_HEIGHT = 20 * CELL_SIZE


class ActionType(enum.Enum):
    AddCoins = 1
    SubtractCoins = 2
    MoveCharacter = 2


class Action:
    def __init__(self, type: ActionType) -> None:
        self.actionType = type


class AddCoinsAction(Action):
    def __init__(self, amount: int) -> None:
        super().__init__(ActionType.AddCoins)

        self.amount = amount


class MoveCharacterAction(Action):
    def __init__(self, x: int, y: int) -> None:
        super().__init__(ActionType.MoveCharacter)

        self.x = x
        self.y = y


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


class CharacterController():
    def process(self, inputs: InputStack) -> list[Action]:
        actions = list[Action]()

        x = inputs.compare(pygame.K_d, pygame.K_a)
        y = inputs.compare(pygame.K_s, pygame.K_w)

        if not (x == y == 0):
            actions.append(MoveCharacterAction(x, y))

        return actions


class GameState:
    epoch: int

    CHARACTER_SPEED = 300

    coins: int
    characterRect: Rect
    globalX: float
    globalY: float

    def __init__(self) -> None:
        self.boardRect = Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT)
        self.characterRect = Rect(0, 0, CELL_SIZE, CELL_SIZE*2)

        self.epoch = time.time_ns()

    def update(self, actions: list[Action]):
        now = time.time_ns()
        elapsed = now - self.epoch
        self.epoch = now

        # 1e9 is the number of nanoseconds in a second
        scale = elapsed / 1e9

        for action in actions:
            if isinstance(action, MoveCharacterAction):
                self.handleMoveCharacter(scale, action)

    xErr, yErr = 0, 0

    def handleMoveCharacter(self, scale: float, action: MoveCharacterAction):
        scaled = Vector2(action.x, action.y)
        scaled.scale_to_length(self.CHARACTER_SPEED * scale)

        scaled.x += self.xErr
        scaled.y += self.yErr

        newRect = self.characterRect.move(
            scaled.x, scaled.y)

        self.xErr = scaled.x - trunc(scaled.x)
        self.yErr = scaled.y - trunc(scaled.y)

        # check moving within board bounds
        if not self.boardRect.contains(newRect):
            return

        self.characterRect = Rect(newRect)


class Game:
    def __init__(self) -> None:
        pygame.init()

        self.image = Surface((BOARD_WIDTH, BOARD_HEIGHT))
        self.display = pygame.display.set_mode(
            (BOARD_WIDTH, BOARD_HEIGHT), pygame.RESIZABLE)
        self.background = color.BLACK

        self.inputStack = InputStack()

        self.state = GameState()
        self.characterController = CharacterController()
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

        actions += self.characterController.process(self.inputStack)

        self.actions = actions

    def update(self):
        self.state.update(self.actions)

    def render(self):
        # Base
        self.image.fill(self.background)

        # Character sprite
        self.image.fill(color.MAGENTA, self.state.characterRect)

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
