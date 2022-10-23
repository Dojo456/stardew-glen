import enum
import time

import pygame

from constants import *


class Coord:
    x: int
    y: int

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class TileType(enum.Enum):
    CROP = 0


class Tile:
    def __init__(self, pos: Coord, type: TileType) -> None:
        self.pos = pos
        self.type = type


class Action:
    def __init__(self) -> None:
        pass


class AddCoinsAction(Action):
    def __init__(self, amount: int) -> None:
        super().__init__()

        self.amount = amount


class MoveCharacterAction(Action):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()

        allowed = [-1, 0, 1]
        if x not in allowed or y not in allowed:
            raise ValueError("allowed values are -1, 0, or 1")

        self.x = x
        self.y = y


class PlantCropAction(Action):
    def __init__(self, at: Coord) -> None:
        super().__init__()

        self.at = at


class World:
    def __init__(self) -> None:
        self.__specialTiles = list[Tile]()
        self.__tiles: list[list[Tile | None]] = [
            [None]*WORLD_WIDTH] * WORLD_HEIGHT

    @property
    def specialTiles(self):
        return tuple(self.__specialTiles)

    def update(self, actions: list[Action]):
        for action in actions:
            if isinstance(action, PlantCropAction):
                self.addTile(Tile(action.at, TileType.CROP))

    def addTile(self, tile: Tile):
        pos = tile.pos

        self.__specialTiles.append(tile)
        self.__tiles[pos.y][pos.x] = tile


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


class Character(object):
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

    @property
    def closestTile(self) -> Coord:
        pos = self.pos

        return Coord(round(pos.x / CELL_SIZE), round(pos.y / CELL_SIZE))
