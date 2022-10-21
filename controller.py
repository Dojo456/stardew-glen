import enum
import time

import pygame

from constants import *


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


class Direction(enum.Enum):
    DOWN = 0
    RIGHT = 1
    UP = 2
    LEFT = 3


class Character:
    epoch: int

    CHARACTER_SPEED = 150

    coins: int
    pos: pygame.math.Vector2
    dir: Direction

    def __init__(self) -> None:
        self.pos = Vector2((WORLD_WIDTH / 2), (WORLD_HEIGHT / 2))
        self.dir = Direction.DOWN

        self.epoch = time.time_ns()

    def update(self, actions: list[Action]):
        now = time.time_ns()
        elapsed = now - self.epoch
        self.epoch = now

        # 1e9 is the number of nanoseconds in a second
        scale = elapsed / 1e9

        for action in actions:
            if isinstance(action, MoveCharacterAction):
                self.__handleMoveCharacter(scale, action)

    xErr, yErr = 0, 0

    def __handleMoveCharacter(self, scale: float, action: MoveCharacterAction):
        scaled = Vector2(action.x, action.y)
        scaled.scale_to_length(self.CHARACTER_SPEED * scale)

        newPos = self.pos + scaled

        if newPos.x < 0:
            newPos.x = 0
        elif newPos.x > WORLD_WIDTH - CELL_SIZE:
            newPos.x = WORLD_WIDTH - CELL_SIZE

        if newPos.y < 0:
            newPos.y = 0
        elif newPos.y > WORLD_HEIGHT - (CELL_SIZE * 2):
            newPos.y = WORLD_HEIGHT - (CELL_SIZE * 2)

        self.pos = newPos

        newDir = self.dir
        if action.y != 0:
            newDir = Direction(1 - action.y)

        if action.x != 0:
            newDir = Direction(2 - action.x)

        self.dir = newDir
        print(self.pos)
        print(self.dir)
