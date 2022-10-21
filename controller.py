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
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class Character:
    epoch: int

    CHARACTER_SPEED = 150

    coins: int
    pos: pygame.math.Vector2
    dir: Direction

    def __init__(self) -> None:
        self.pos = Vector2((WORLD_WIDTH / 2), (WORLD_HEIGHT / 2))

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

        # using the int values of the direction enums to calculate character direction
        vert = 1
        if action.y != 0:
            vert = int((action.y / 2) + 0.5)

        horz = 0
        if action.x != 0:
            horz = int((action.x / 2) + 1.5)

        self.dir = Direction(vert + horz)
        print(self.pos)
        print(self.dir)
