from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder

app = FastAPI()


class MapItem(BaseModel):
    row: str
    col: str
    map: list | None = None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/map")
def get_map():
    row, col, map_file = get_map_file()
    return {"row": row, "col": col, "map": map_file}


@app.put("/map", response_model=MapItem)
def update_map(item: MapItem):
    data = jsonable_encoder(item)
    if int(data['row']) <= 0 or int(data['col']) <= 0:
        raise HTTPException(status_code=400, detail="Invalid request. Dimensions must be above 0")

    row, col, map_file = get_map_file()
    row = int(data['row'])
    col = int(data['col'])

    map_file = map_file[:row]
    for i, row_element in enumerate(map_file):
        map_file[i] = row_element[:col]

    print(map_file)
    return {"row": data['row'], "col": data['col'], "map": map_file}


def get_map_file():
    with open("map.txt") as file:
        # get dimensions
        dim = file.readline().split()
        row = int(dim[0])
        col = int(dim[1])

        # format map as array of string
        map_file = list()
        for line in file:
            map_file.append(line.split())

    return row, col, map_file
