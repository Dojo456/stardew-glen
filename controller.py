import enum
import time

import pygame
from pytmx import TiledObject, TiledObjectGroup, load_pygame  # type: ignore
from shapely import geometry  # type: ignore
from shapely.ops import nearest_points  # type: ignore

import items
from constants import *
from items import Item, ItemStack

HITBOX_VEC = Vector2(CELL_SIZE /
                     2, CELL_SIZE * 1.5)

CHARACTER_SPEED = 80
ANIMATION_SPEED = 5


class Coord:
    x: int
    y: int

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, __o: object) -> bool:
        return self.x == __o.x and self.y == __o.y  # type: ignore

    def __str__(self) -> str:
        return f"x: {self.x}, y: {self.y}"

    def __repr__(self) -> str:
        return self.__str__()


class InventoryManager:
    items: list[Item | ItemStack | None]

    def __init__(self, rowCount: int = 1) -> None:
        self.items = [None] * (12 * rowCount)
        self.slotSelection = 0
        self.rowSelection = 0
        self.rowCount = rowCount

    def addItem(self, item: Item, slot: int = -1):
        print("adding item")

        if slot == -1:  # did not specify slot, auto stack and first on row
            if item.stackable:
                for thisItem in self.items:
                    if isinstance(thisItem, ItemStack) and thisItem.item.id == item.id:
                        thisItem.add()
                        return

            rowOffset = self.rowSelection * 12
            for i in range(12):
                index = i + rowOffset

                itemSlot = self.items[index]

                if itemSlot == None:
                    if item.stackable:
                        self.items[index] = ItemStack(item)
                    else:
                        self.items[index] = item

                    return

    @property
    def currentItems(self):
        row = list[Item | ItemStack | None]()
        rowOffset = self.rowSelection * 12

        for i in range(12):
            row.append(self.items[i + rowOffset])

        return row


class TileType(enum.Enum):
    TILLED_DIRT = 0
    CROP = 1


class Tile:
    def __init__(self, type: TileType) -> None:
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


class HoeGroundAction(Action):
    def __init__(self, pos: Coord) -> None:
        super().__init__()

        self.pos = pos


class PlantCropAction(Action):
    def __init__(self, pos: Coord) -> None:
        super().__init__()

        self.pos = pos


class AddItemAction(Action):
    def __init__(self, item: Item) -> None:
        super().__init__()

        self.item = item


class ChangeInventorySelectionAction(Action):
    def __init__(self, selection: int) -> None:
        super().__init__()

        if selection < 0 or selection > 11:
            raise ValueError("must be between 0 and 11")

        self.selection = selection


class World:
    def __init__(self) -> None:
        self.__tiles: list[list[Tile | None]] = [
            [None] * int(WORLD_HEIGHT / CELL_SIZE) for _ in range(int(WORLD_WIDTH / CELL_SIZE))]

        self.mapData = load_pygame("./assets/tiled/minimap.tmx")

        self.collisionObjects = list[geometry.Polygon]()
        collisionLayer: TiledObjectGroup = self.mapData.get_layer_by_name(
            "Collision Objects")
        for object in collisionLayer:  # type: ignore
            assert (type(object) == TiledObject)  # type: ignore
            self.collisionObjects.append(
                geometry.Polygon(object.as_points))  # type: ignore

        spawnPoint = self.mapData.get_object_by_name(  # type: ignore
            "spawnPoint")
        self.spawnPoint = Vector2(spawnPoint.x, spawnPoint.y)

        self.queuedActions = list[Action]()

        # Global player states
        self.coins = 0
        self.inventoryManager = InventoryManager()

    def update(self, actions: list[Action]):
        allActions = self.queuedActions + actions
        self.queuedActions = list[Action]()

        for action in allActions:
            if isinstance(action, PlantCropAction):
                self.handlePlantCropAction(action)
            elif isinstance(action, HoeGroundAction):
                self.handleHoeGroundAction(action)
            elif isinstance(action, ChangeInventorySelectionAction):
                self.handleChangeInventorySelectionAction(action)
            elif isinstance(action, AddItemAction):
                self.handleAddItemAction(action)

    def tileAt(self, pos: Coord):
        return self.__tiles[pos.x][pos.y]

    def setTile(self, pos: Coord, tile: Tile):
        print(f"setting {tile.type} at {pos}")

        self.__tiles[pos.x][pos.y] = tile

    def removeTile(self, pos: Coord):
        tile = self.tileAt(pos)

        if tile != None:
            print(f"removing {tile.type} at {pos}")

        self.__tiles[pos.x][pos.y] = None

    def handlePlantCropAction(self, action: PlantCropAction):
        existing = self.tileAt(action.pos)

        if existing != None and existing.type == TileType.TILLED_DIRT:
            self.setTile(action.pos, Tile(TileType.CROP))

    def handleHoeGroundAction(self, action: HoeGroundAction):
        existing = self.tileAt(action.pos)

        if existing != None and existing.type == TileType.CROP:  # if harvesting
            self.removeTile(action.pos)
            self.queuedActions.append(AddItemAction(items.itemWithID(2)))
        else:
            self.setTile(action.pos, Tile(TileType.TILLED_DIRT))

    def handleChangeInventorySelectionAction(self, action: ChangeInventorySelectionAction):
        self.inventoryManager.slotSelection = action.selection

    def handleAddItemAction(self, action: AddItemAction):
        self.inventoryManager.addItem(action.item)


class Direction(enum.Enum):
    DOWN = 0
    RIGHT = 1
    UP = 2
    LEFT = 3


class CharacterState(enum.Enum):
    STANDING = 0
    WALKING = 1
    SITTING = 2


class Character(object):
    epoch: int

    coins: int
    pos: pygame.math.Vector2
    direction: Direction

    state: CharacterState

    def __init__(self, world: World) -> None:
        self.world = world

        self.pos = world.spawnPoint
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

        # if enough time has elapsed for one frame of animation, update tick
        if self.accumulated > (1e9 / ANIMATION_SPEED):
            self.accumulated -= 1e9 / ANIMATION_SPEED
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

        # print(str(scaled))

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

        org = _centeredRect(self.pos + HITBOX_VEC, CELL_SIZE - 3)
        colHorz = _centeredRect(horz + HITBOX_VEC, CELL_SIZE - 3)
        colVert = _centeredRect(vert + HITBOX_VEC, CELL_SIZE - 3)

        for object in self.world.collisionObjects:
            if object.intersects(colHorz) and not object.intersects(org):  # type: ignore
                scaled.x = 0
            if object.intersects(colVert) and not object.intersects(org):  # type: ignore
                scaled.y = 0

        self.pos += scaled

        for object in self.world.collisionObjects:
            if object.contains(_centeredRect(self.pos + HITBOX_VEC, CELL_SIZE)):  # type: ignore
                print("clipping")

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
        pos = self.pos + HITBOX_VEC

        return Coord(int(pos.x / CELL_SIZE), int(pos.y / CELL_SIZE))


def _centeredRect(point: pygame.math.Vector2, size: float) -> geometry.Polygon:
    diag = Vector2(size / 2, size / 2)

    topLeft = point - diag
    bottomRight = point + diag

    diag.y = -(size / 2)

    bottomLeft = point - diag
    topRight = point + diag

    return geometry.Polygon([topLeft, bottomLeft, bottomRight, topRight])
