from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
import os

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
    # unpack data
    data = jsonable_encoder(item)

    # throw error for invalid dimensions
    if int(data['row']) <= 0 or int(data['col']) <= 0:
        raise HTTPException(status_code=400, detail="Invalid request. Dimensions must be above 0")

    # get old map dimensions and content
    old_row, old_col, map_file = get_map_file()
    row = int(data['row'])
    col = int(data['col'])

    # check cases for adding/removig rows and columns
    if row > old_row:
        for i in range(row-old_row):
            map_file.append(['0'] * old_col)
    else:
        map_file = map_file[:row]

    if col < old_col:
        for i, row_element in enumerate(map_file):
            map_file[i] = row_element[:col]
    else:
        for row_element in map_file:
            for i in range(old_col, col):
                row_element.append('0')

    # write to map
    absolute_path = os.path.dirname(__file__)
    with open(os.path.join(absolute_path, 'map.txt'), 'w+') as txt_file:
        txt_file.write(" ".join([data['row'], data['col']]) + '\n')
        for line in map_file:
            txt_file.write(" ".join(line) + '\n')

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
