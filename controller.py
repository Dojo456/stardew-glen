import enum
import time
from types import CellType

import pygame
from pytmx import TiledTileLayer, load_pygame
from shapely import geometry

import color
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

        self.pos = at


class World:
    def __init__(self) -> None:
        self.__specialTiles = list[Tile]()
        self.__tiles: list[list[Tile | None]] = [
            [None]*WORLD_WIDTH] * WORLD_HEIGHT

        self.mapData = load_pygame("./assets/tiled/minimap.tmx")
        self.image = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

        layerCount = len(self.mapData.layers)

        for layer in self.mapData.layers:
            if isinstance(layer, TiledTileLayer):
                for x, y, image in layer.tiles():
                    if isinstance(image, pygame.Surface):
                        self.image.blit(image, (x * CELL_SIZE, y * CELL_SIZE))

        self.collisionObjects = list[geometry.Polygon]()
        for object in self.mapData.objects:
            self.collisionObjects.append(geometry.Polygon(object.points))

        self.image.set_colorkey(color.MAGENTA)

        # Global player states
        self.coins = 0

    @property
    def specialTiles(self):
        return tuple(self.__specialTiles)

    def update(self, actions: list[Action]):
        for action in actions:
            if isinstance(action, PlantCropAction):
                self.__handlePlantCropAction(action)

    def tileAt(self, pos: Coord):
        return self.__tiles[pos.y][pos.x]

    def addTile(self, tile: Tile):
        pos = tile.pos

        self.__specialTiles.append(tile)
        self.__tiles[pos.y][pos.x] = tile

    def removeTile(self, pos: Coord):
        self.__tiles[pos.y][pos.x] = None

        for tile in self.__specialTiles:
            if tile.pos == pos:
                self.__specialTiles.remove(tile)
                break

    def __handlePlantCropAction(self, action: PlantCropAction):
        existing = self.tileAt(action.pos)

        # if harvesting
        if existing != None and existing.type == TileType.CROP:
            self.removeTile(action.pos)
            self.coins += 5
        else:
            self.addTile(Tile(action.pos, TileType.CROP))


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

    def __init__(self, world: World) -> None:
        self.pos = Vector2((WORLD_WIDTH / 2), (WORLD_HEIGHT / 2))
        self.direction = Direction.DOWN
        self.state = CharacterState.STANDING

        self.epoch = time.time_ns()
        self.accumulated = 0
        self.tick = 0

        self.world = world

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

        horz = self.pos + Vector2(scaled.x, 0)
        vert = self.pos + Vector2(0, scaled.y)

        if horz.x < 0:
            scaled.x = -self.pos.x
        elif horz.x > WORLD_WIDTH - CELL_SIZE:
            scaled.x = WORLD_WIDTH - CELL_SIZE - self.pos.x

        if vert.y < 0:
            scaled.y = -self.pos.y
        elif vert.y > WORLD_HEIGHT - (CELL_SIZE * 2):
            scaled.y = WORLD_HEIGHT - (CELL_SIZE * 2) - self.pos.y

        hitBoxVec = Vector2(CELL_SIZE /
                            2, CELL_SIZE * 1.5)

        org = _centeredRect(self.pos + hitBoxVec, CELL_SIZE - 2)
        colHorz = _centeredRect(horz + hitBoxVec, CELL_SIZE - 2)
        colVert = _centeredRect(vert + hitBoxVec, CELL_SIZE - 2)

        for object in self.world.collisionObjects:
            if object.intersects(colHorz) and not object.intersects(org):
                scaled.x = 0
            if object.intersects(colVert) and not object.intersects(org):
                scaled.y = 0

        self.pos += scaled

        newDir = self.direction
        if action.y != 0:
            newDir = Direction(1 - action.y)

        if action.x != 0:
            newDir = Direction(2 - action.x)

        self.direction = newDir
        self.state = CharacterState.WALKING
        # print(self.pos)

    @property
    def closestTile(self) -> Coord:
        pos = self.pos

        return Coord(round(pos.x / CELL_SIZE), round(pos.y / CELL_SIZE))


def _centeredRect(point: pygame.math.Vector2, size: float) -> geometry.Polygon:
    diag = Vector2(size / 2, size / 2)

    topLeft = point - diag
    bottomRight = point + diag

    diag.y = -(size / 2)

    bottomLeft = point - diag
    topRight = point + diag

    return geometry.Polygon([topLeft, bottomLeft, bottomRight, topRight])
