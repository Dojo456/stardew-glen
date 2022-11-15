import enum
import json


class ItemType(enum.Enum):
    TOOL = "TOOL"
    WEAPON = "WEAPON"
    SEED = "SEED"
    CROP = "CROP"


class Item:
    def __init__(self, type: ItemType, id: int, name: str, stackable: bool, renderPos: str) -> None:
        self.type = type
        self.id = id
        self.name = name
        self.stackable = stackable
        self.renderPos = renderPos


class ItemStack:
    def __init__(self, item: Item, count: int = 1) -> None:
        self.item = item
        self.count = count

    def add(self, count: int = 1):
        self.count += count

    def remove(self, count: int = 1):
        self.count -= count


"""BEGIN SCRIPT"""

allItems = list[Item]()
itemsJson = json.loads(open("./assets/items.json").read())
for item in itemsJson:
    stackable = False
    if "stackable" in item:
        stackable = item["stackable"]

    allItems.append(Item(
        ItemType(item["type"]),
        item["id"],
        item["name"],
        stackable,
        item["renderPos"],
    ))


def itemWithID(id: int):
    return allItems[id]
