import enum
import os
from abc import ABC, abstractmethod
from typing import Dict

import pygame
from pygame import Vector2

import color

os.environ['SDL_VIDEO_CENTERED'] = '1'

FRAME_LIMIT = 144

CELL_SIZE = 16
BOARD_SIZE = Vector2(16, 10)

WINDOW_WIDTH = BOARD_SIZE.x * CELL_SIZE
WINDOW_HEIGHT = BOARD_SIZE.y * CELL_SIZE


class GameState:
    coins: int

    def __init__(self) -> None:
        self.coins = 0


class ActionType(enum.Enum):
    AddCoins = 1
    SubtractCoins = 2


class Action(ABC):
    def __init__(self, type: ActionType) -> None:
        self.actionType = type

    @abstractmethod
    def transform(self, state: GameState) -> None:
        pass


class AddCoinsAction(Action):
    def __init__(self, amount: int) -> None:
        super().__init__(ActionType.AddCoins)

        self.amount = amount

    def transform(self, state: GameState) -> None:
        state.coins += self.amount


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


class Game:
    def __init__(self) -> None:
        pygame.init()

        windowSize = Vector2(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.window = pygame.display.set_mode(
            (int(windowSize.x), int(windowSize.y)))
        self.background = color.BLACK

        self.state = GameState()
        self.actions = list[Action]()

        self.clock = pygame.time.Clock()
        self.running = True

    def processInput(self):
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.running = False
                    break
                case _:
                    pass

    def update(self):
        for action in self.actions:
            action.transform(self.state)

    def render(self):
        # Background
        self.window.fill(self.background)

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
