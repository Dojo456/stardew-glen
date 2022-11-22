import enum
import json


class ItemType(enum.Enum):
    HOE = "HOE"
    SWORD = "SWORD"
    SEED = "SEED"
    CROP = "CROP"


class Item:
    count = 0
    
    def __init__(self, item: dict[str, (str | int | float | bool)]) -> None:
        try:
            self.id = int(item["id"])
            self.name = str(item["name"])
            self.type = ItemType(item["type"])
            self.renderPos = str(item["renderPos"])

            stackable = False
            if "stackable" in item:
                stackable = bool(item["stackable"])
            self.stackable = stackable
            
            if self.type == ItemType.CROP:
                self.matures = int(item["matures"])
                self.season = str(item["season"])
            elif self.type == ItemType.SEED:
                self.plants = int(item["plants"])
        except Exception as e:
            print(f"item {Item.count} is invalid")
            print(e)
        finally:
            Item.count+=1



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
    allItems.append(Item(item))


def itemWithID(id: int):
    return allItems[id]
