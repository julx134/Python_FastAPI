from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
import os
import uuid

app = FastAPI()


class MapItem(BaseModel):
    row: str
    col: str
    map: list | None = None


class MineItem(BaseModel):
    serial_no: str
    x: str
    y: str


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

    # check cases for adding/removing rows and columns
    if row > old_row:
        for i in range(row - old_row):
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
    write_to_map_file(map_file, data)

    return {"row": data['row'], "col": data['col'], "map": map_file}


@app.post("/mines")
def create_mine(item: MineItem):
    # unpack data
    data = jsonable_encoder(item)

    map_row, map_col, map_list = get_map_file()
    x = int(data['x'])
    y = int(data['y'])

    # raise exception for invalid parameters
    if x >= map_row or y >= map_col or x < 0 or y < 0:
        raise HTTPException(status_code=400, detail="Invalid request. Invalid coordinates")

    # check if mine already exists in map
    if map_list[x][y] != '0':
        raise HTTPException(status_code=400, detail="Invalid request. Mine already exists at coordinate")

    # generate random id
    mine_id = str(uuid.uuid4())[:8]

    # write to file
    write_mines_to_file(mine_id, data['serial_no'], data['x'], data['y'])

    # write to map
    map_list[x][y] = '1'
    data_map = {"row": str(map_row), "col": str(map_col)}
    write_to_map_file(map_list, data_map)

    return {"mine_id": mine_id, "serial_no": data['serial_no'], "x": data['x'], "y": data['y']}


@app.get("/mines")
def get_mines():
    return get_mines_file()


@app.get("/mines/{mine_id}")
def get_mine_by_id(mine_id: str):
    mines = get_mines_file()

    return mines[mine_id]


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


def write_mines_to_file(mine_id, serial_no, x, y):
    mines_data = get_mines_file()

    # add to mines list
    data = {"id": mine_id, 'serial_no': serial_no, "x": x, "y": y}
    mines_data[mine_id] = data

    # convert dictionary to list
    mine_list = list()
    for key, val in mines_data.items():
        # appending list of corresponding key-value pair to a list
        mine_list.append(list(val.values()))

    # overwrite mines.txt file
    absolute_path = os.path.dirname(__file__)
    with open(os.path.join(absolute_path, 'mines.txt'), 'w+') as txt_file:
        for line in mine_list:
            txt_file.write(" ".join(line) + '\n')


def get_mines_file():
    with open("mines.txt") as file:
        # format map as array of string
        mine_list = {}
        for line in file:
            line_data = line.split()
            data = {"id": line_data[0], 'serial_no': line_data[1], "x": line_data[2], "y": line_data[3]}
            mine_list[line_data[0]] = data
    return mine_list


def write_to_map_file(map_file, data):
    absolute_path = os.path.dirname(__file__)
    with open(os.path.join(absolute_path, 'map.txt'), 'w+') as txt_file:
        txt_file.write(" ".join([data['row'], data['col']]) + '\n')
        for line in map_file:
            txt_file.write(" ".join(line) + '\n')



















