from hashlib import sha256
from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import uuid
import copy

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
rover_list = {}
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

    return {"mine": mines_list[mine_id]}


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


@app.post("/rovers")
def create_rover(commands: str):
    global rover_list

    # generate random id
    rover_id = str(uuid.uuid4())[:8]

    data = {"rover_id": rover_id, "commands": commands, "status": "Not Started"}

    rover_list[rover_id] = data

    return rover_list[rover_id]


@app.get("/rovers")
def get_rovers():
    global rover_list

    if len(rover_list) == 0:
        return {"data": 'no rovers listed'}
    
    return {'rovers': rover_list}


@app.get("/rovers/{rover_id}")
def get_rover_by_id(rover_id: str):
    global rover_list

    if rover_id not in rover_list.keys():
        return {"data": "no rovers found with specified ID"}

    return {"rovers": rover_list[rover_id]}


@app.delete("/rovers/{rover_id}")
def delete_rover_by_id(rover_id: str):
    global rover_list

    if rover_id not in rover_list.keys():
        return {"data": "no rovers found with specified ID"}

    # delete rover
    del rover_list[rover_id]

    return {"deleted": "Success", "rovers": rover_list}


@app.put("/rovers/{rover_id}")
def change_rover_state(rover_id: str, commands: str | None):
    global rover_list

    if rover_id not in rover_list.keys():
        return {"data": "no rovers found with specified ID"}

    rover = rover_list[rover_id]
    if rover['status'] != "Not Started" and rover['status'] != "Finished":
        return {"data": "rover status not applicable"}

    rover_list[rover_id]['commands'] = commands
    return {"rovers":  rover_list[rover_id]}


@app.post("/rovers/{rover_id}/dispatch")
def dispatch_rover(rover_id: str):
    global rover_list

    if rover_id not in rover_list.keys():
        return {"data": "no rovers found with specified ID"}

    if rover_list[rover_id]['status'] == "Not Started":
        return rover_execute_command(rover_id)
    else:
        return {"data": "rover status not applicable"}


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


def rover_execute_command(rover_id):
    global map_list
    global map_row
    global map_col
    global mines_list
    global rover_list

    # change rover status to Moving
    rover_list[rover_id]['status'] = 'Moving'

    # copy map to list -- this is so we don't have to write to map.txt directly
    rover_map = copy.deepcopy(map_list)

    # initialize path map for rover
    path = [['0' for x in range(map_col)] for j in range(map_row)]

    # dictionary to track rover position
    rover_pos = {'x': 0, 'y': 0, 'dir': 'S'}

    i = 0
    outer_x_bounds = map_row - 1
    outer_y_bounds = map_col - 1
    x = rover_pos['x']
    y = rover_pos['y']
    path[x][y] = '*'

    disarmed_mines = list()
    rover = rover_list[rover_id]
    # for loop and match-case statements that handle rover movement
    for move in rover['commands']:
        dig_move = False
        # if rover finds a mine and doesnt dig, it explodes
        if int(rover_map[x][y]) > 0 and move != 'D':
            rover_list[rover_id]['status'] = 'Eliminated'
            path[x][y] = 'X'
            return {"data": {"rover_map": path, "rover": rover_list[rover_id], "disarmed_mines": disarmed_mines}}

        # otherwise add diffused mines to disarmed mines
        if int(rover_map[x][y]) > 0 and move == 'D':
            # get mine location and update map
            rover_map[x][y] = '0'

            # get serial mine number
            serial_no = ''
            for mine_id in mines_list:
                if mines_list[mine_id]['x'] == x and mines_list[mine_id]['y'] == y:
                    serial_no = mines_list[mine_id]['serial_no']
                    break

            # diffuse mine
            pin, hash_ = disarm_mine(serial_no)
            dig_move = True
            disarmed_mines.append({'pin': pin, 'hash': hash_, 'x': x, 'y': y})

        match move:
            case 'M':  # move forward
                match rover_pos['dir']:
                    case 'S':
                        if rover_pos['x'] + 1 <= outer_x_bounds:
                            rover_pos['x'] += 1
                    case 'N':
                        if rover_pos['x'] - 1 >= 0:
                            rover_pos['x'] -= 1
                    case 'W':
                        if rover_pos['y'] - 1 >= 0:
                            rover_pos['y'] -= 1
                    case 'E':
                        if rover_pos['y'] + 1 <= outer_y_bounds:
                            rover_pos['y'] += 1
            case 'L':  # turn left
                match rover_pos['dir']:
                    case 'S':
                        rover_pos['dir'] = 'E'
                    case 'N':
                        rover_pos['dir'] = 'W'
                    case 'W':
                        rover_pos['dir'] = 'S'
                    case 'E':
                        rover_pos['dir'] = 'N'
            case 'R':  # turn right
                match rover_pos['dir']:
                    case 'S':
                        rover_pos['dir'] = 'W'
                    case 'N':
                        rover_pos['dir'] = 'E'
                    case 'W':
                        rover_pos['dir'] = 'N'
                    case 'E':
                        rover_pos['dir'] = 'S'

        x = rover_pos['x']
        y = rover_pos['y']
        if dig_move:
            path[x][y] = '#'
        else:
            path[x][y] = '*'
        i += 1

    # if successful, send status to server
    rover_list[rover_id]['status'] = "Finished"
    return {"data": {"rover_map": path, "rover": rover_list[rover_id], "disarmed_mines": disarmed_mines}}


def disarm_mine(serial_no):
    # note: we increment pin instead of using random to make sure results are reproducible
    # i.e. same time pin is found vs. random time generating random pins
    pin = 0
    success_code = '0' * 4
    mine_key = str(pin) + serial_no
    while not (hash_ := sha256(f'{mine_key}'.encode()).hexdigest()).startswith(success_code):
        pin += 1
        mine_key = str(pin) + serial_no

    return pin, hash_

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