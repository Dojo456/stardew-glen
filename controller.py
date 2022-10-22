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
        allowed = [-1, 0, 1]
        if x not in allowed or y not in allowed:
            raise ValueError("allowed values are -1, 0, or 1")

        super().__init__(ActionType.MoveCharacter)

        self.x = x
        self.y = y


class Direction(enum.Enum):
    DOWN = 0
    RIGHT = 1
    UP = 2
    LEFT = 3


class CharacterState(enum.Enum):
    STANDING = 0
    WALKING = 1
    SITTING = 2


CHARACTER_SPEED = 150
ANIMATION_SPEED = 2


class Character:
    epoch: int

    coins: int
    pos: pygame.math.Vector2
    direction: Direction

    state: CharacterState

    def __init__(self) -> None:
        self.pos = Vector2((WORLD_WIDTH / 2), (WORLD_HEIGHT / 2))
        self.direction = Direction.DOWN
        self.state = CharacterState.STANDING

        self.epoch = time.time_ns()
        self.accumulated = 0
        self.tick = 0

    def update(self, actions: list[Action]):
        now = time.time_ns()
        elapsed = now - self.epoch

        self.accumulated += elapsed
        self.epoch = now

        # if more than one fourth of a second has elapsed, update tick
        if self.accumulated > (25e7):
            self.accumulated -= 25e7
            self.tick = (self.tick + 1) % 4

        # 1e9 is the number of nanoseconds in a second
        scale = elapsed / 1e9

        newState = CharacterState.STANDING

        # handle all actions
        for action in actions:
            if isinstance(action, MoveCharacterAction):
                self.__handleMoveCharacter(scale, action)
                newState = CharacterState.WALKING

        self.state = newState

    xErr, yErr = 0, 0

    def __handleMoveCharacter(self, scale: float, action: MoveCharacterAction):
        scaled = Vector2(action.x, action.y)
        scaled.scale_to_length(CHARACTER_SPEED * scale)

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

        newDir = self.direction
        if action.y != 0:
            newDir = Direction(1 - action.y)

        if action.x != 0:
            newDir = Direction(2 - action.x)

        self.direction = newDir
        self.state = CharacterState.WALKING
        print(self.pos)
        print(self.direction)
