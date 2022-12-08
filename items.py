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
        except Exception as e:
            print(f"item {Item.count} is invalid")
            print(e)
        finally:
            Item.count+=1

class Crop(Item):
    def __init__(self, item: dict[str, (str | int | float | bool)]) -> None:
        super().__init__(item)

        self.matures = int(item["matures"])
        self.season = str(item["season"])

class Seed(Item):
    def __init__(self, item: dict[str, (str | int | float | bool)]) -> None:
        super().__init__(item)

        self.plantsID = int(item["plants"])
    
    @property
    def plants(self) -> Crop:
        item = itemWithID(self.plantsID)

        if isinstance(item, Crop):
            return item
        else:
            raise ValueError(f"{self.name} must plant type crop")

class ItemFactory():
    def build(self, item: dict[str, (str | int | float | bool)]) -> Item:
        itemType = ItemType(item["type"])

        if itemType == ItemType.CROP:
            return Crop(item)
        elif itemType == ItemType.SEED:
            return Seed(item)
        else:
            return Item(item)

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

factory = ItemFactory()

for item in itemsJson:
    allItems.append(factory.build(item))

def itemWithID(id: int):
    return allItems[id]
