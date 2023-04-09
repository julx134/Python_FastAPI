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
    serial_no: str = ""
    x: str = ""
    y: str = ""


map_row = ''
map_col = ''
map_list = list()
mines_list = {}
init = False


@app.get("/map")
def get_map():
    row, col, map_file = get_map_file()
    return {"row": row, "col": col, "map": map_file}


@app.put("/reset_map")
def reset_map():
    global map_row
    map_row = 10
    global map_col
    map_col = 10
    global map_list
    map_list = [["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"], ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"], ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"], ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"], ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"], ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]]

    global mines_list
    mines_list = {}

    return {"row": map_row, "col": map_col, "map": map_list, 'mines': mines_list}


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
    global map_list
    global map_row
    global map_col
    map_col = col
    map_row = row
    map_list = map_file

    return {"row": data['row'], "col": data['col'], "map": map_file}


@app.post("/mines")
def create_mine(item: MineItem):
    global map_list

    # unpack data
    data = jsonable_encoder(item)

    if data['x'] == '' or data['y'] == '' or data['serial_no'] == '':
        raise HTTPException(status_code=400, detail="Invalid request. Invalid parameters")

    map_row, map_col, map_file = get_map_file()
    x = int(data['x'])
    y = int(data['y'])

    # raise exception for invalid parameters
    if x >= map_row or y >= map_col or x < 0 or y < 0:
        raise HTTPException(status_code=400, detail="Invalid request. Invalid coordinates")

    # check if mine already exists in map
    if map_file[x][y] != '0':
        raise HTTPException(status_code=400, detail="Invalid request. Mine already exists at coordinate")

    # generate random id
    mine_id = str(uuid.uuid4())[:8]

    # write to file
    global mines_list
    mines_list[mine_id] = {"id": mine_id, 'serial_no': data['serial_no'], "x": x, "y": y}

    # write to map
    map_file[x][y] = '1'
    map_list = map_file

    return {"mine_id": mine_id, "serial_no": data['serial_no'], "x": data['x'], "y": data['y']}


@app.get("/mines")
def get_mines():
    global mines_list
    if len(mines_list) == 0:
        return {"data": 'no mines listed'}

    return {"mines": mines_list}


@app.get("/mines/{mine_id}")
def get_mine_by_id(mine_id: str):
    global mines_list

    if mine_id not in mines_list.keys():
        return {"data": "no mines found with specified ID"}

    return {"mine": mine_id}


@app.delete("/mines/{mine_id}")
def delete_mine_by_id(mine_id: str):
    global mines_list
    global map_list

    if mine_id not in mines_list.keys():
        return {"data": "no mines found with specified ID"}

    # update map
    x = mines_list[mine_id]['x']
    y = mines_list[mine_id]['y']
    map_list[x][y] = '0'

    # delete mine
    del mines_list[mine_id]

    return {"deleted": "Success", "mines": mines_list}


@app.put("/mines/{mine_id}")
def update_mine(mine_id: str, item: MineItem):
    global mines_list
    global map_list
    global map_row
    global map_col

    # unpack data
    data = jsonable_encoder(item)

    if mine_id not in mines_list.keys():
        return {"data": "no mines found with specified ID"}

    # remove mine from map
    row = int(mines_list[mine_id]['x'])
    col = int(mines_list[mine_id]['y'])
    map_list[row][col] = '0'

    if data['x'] != '':
        if 0 <= int(data['x']) < int(map_row):
            mines_list[mine_id]['x'] = int(data['x'])
            row = data['x']

    if data['y'] != '':
        if 0 <= int(data['y']) < int(map_col):
            mines_list[mine_id]['y'] = int(data['y'])
            col = data['y']

    if data['serial_no'] != '':
        mines_list[mine_id]['serial_no'] = data['serial_no']

    # add mine back to map
    map_list[int(row)][int(col)] = '1'

    return {"Update": "success", 'mine': mines_list[mine_id]}

def get_map_file():
    global init
    global map_row
    global map_col
    global map_list

    if not init:
        init = True
        map_row = 10
        map_col = 10
        map_list = [["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]]

    return map_row, map_col, map_list



# <----------------- old functions (to be deleted..) ------------------>

"""
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


def write_to_map_file(map_file, data, test):
    absolute_path = os.path.dirname(__file__)
    with open(os.path.join(absolute_path, 'map.txt'), 'w+') as txt_file:
        txt_file.write(" ".join([data['row'], data['col']]) + '\n')
        for line in map_file:
            txt_file.write(" ".join(line) + '\n')


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


def get_mines_file(test):
    with open("mines.txt") as file:
        # format map as array of string
        mine_list = {}
        for line in file:
            line_data = line.split()
            data = {"id": line_data[0], 'serial_no': line_data[1], "x": line_data[2], "y": line_data[3]}
            mine_list[line_data[0]] = data
    return mine_list
"""