# import json
# import requests
# import sim

# def load_json(file_path):
#     with open(file_path, 'r') as file:
#         return json.load(file)

# def get_names(data):
#     names = []
#     if 'agents' in data:
#         for agent in data['agents']:
#             full_name = f"{agent['name'].get('prefix', '')} {agent['name'].get('first_name', '')} {agent['name'].get('last_name', '')}".strip()
#             names.append(full_name)
#     if 'objects' in data:
#         for obj in data['objects']:
#             names.append(obj['name'])
#     return names

# def get_position_from_api(clientID, name):
#     res, tmp_handle = sim.simxGetObjectHandle(clientID, name, sim.simx_opmode_blocking)
#     ret, pos = sim.simxGetObjectPosition(clientID, tmp_handle, -1, sim.simx_opmode_blocking)
#     if ret == sim.simx_return_ok:
#         return pos
#     else:
#         print(f"Failed to get position for {name}, return code: {ret}")
#         return None

# def update_poses(data, positions):
#     if 'agents' in data:
#         for agent in data['agents']:
#             full_name = f"{agent['name'].get('prefix', '')} {agent['name'].get('first_name', '')} {agent['name'].get('last_name', '')}".strip()
#             if full_name in positions:
#                 agent['pose'] = positions[full_name]
#     if 'objects' in data:
#         for obj in data['objects']:
#             if obj['name'] in positions:
#                 obj['pose'] = positions[obj['name']]
#     return data

# def main():
#     print('Program started')
#     sim.simxFinish(-1)  # just in case, close all opened connections
#     clientID = sim.simxStart('127.0.0.1', 19982, True, True, 5000, 5)  # Connect to CoppeliaSim
    
#     if clientID != -1:
#         print('Connected to remote API server')
#         file_paths = ['objects.json', 'agents.json']
        
#         for file_path in file_paths:
#             data = load_json(file_path)
#             names = get_names(data)
#             positions = {name: get_position_from_api(clientID, name) for name in names}
#             print(positions)
#             updated_data = update_poses(data, positions)
#             with open(file_path, 'w') as file:
#                 json.dump(updated_data, file, indent=4)

#     else:
#         print('Failed connecting to remote API server')

# if __name__ == '__main__':
#     main()
import json
import requests
import sim
import time

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def get_names(data):
    names = []
    if 'agents' in data:
        for agent in data['agents']:
            full_name = f"{agent['name'].get('prefix', '')} {agent['name'].get('first_name', '')} {agent['name'].get('last_name', '')}".strip()
            names.append(agent['name'].get('first_name', ''))
    if 'objects' in data:
        for obj in data['objects']:
            names.append(obj['name'])
    return names

def get_position_from_api(clientID, name):
    res, tmp_handle = sim.simxGetObjectHandle(clientID, name, sim.simx_opmode_blocking)
    res, parentHandle = sim.simxGetObjectParent(clientID, tmp_handle, sim.simx_opmode_blocking)
    
    while True:
        #print(parentHandle)
        if parentHandle == -1:
            break
        res, retInts, retFloats, retStrings, retBuffer = sim.simxCallScriptFunction(
                  clientID, 
                  'remoteApiFunctions', 
                  sim.sim_scripttype_childscript, 
                  'getName', 
                  [parentHandle], 
                  [], 
                  [], 
                  bytearray(), 
                  sim.simx_opmode_blocking
              )
        name =  retStrings[0] + "/" + name
        res, parentHandle = sim.simxGetObjectParent(clientID, parentHandle, sim.simx_opmode_blocking)
    
    name = "/" + name
    res, tmp_handle = sim.simxGetObjectHandle(clientID, name, sim.simx_opmode_blocking)
    ret, pos = sim.simxGetObjectPosition(clientID, tmp_handle, -1, sim.simx_opmode_blocking)
    #print(f"Name: {name} pos:{pos}")
    if ret == sim.simx_return_ok:
        return pos
    else:
        print(f"Failed to get position for {name}, return code: {ret}")
        return None


def update_poses(data, positions):
    if 'agents' in data:
        for agent in data['agents']:
            full_name = agent['name'].get('first_name', '')
            if full_name in positions:
                agent['pose'] = positions[full_name]
    if 'objects' in data:
        for obj in data['objects']:
            if obj['name'] in positions:
                obj['pose'] = positions[obj['name']]
    return data

def get_room_vertices(rooms_data):
    room_vertices = {}
    if 'rooms' in rooms_data:
        for room in rooms_data['rooms']:
            room_vertices[room['name']] = room['area']
    return room_vertices

def is_point_in_polygon(point, polygon):
    x, y = point
    inside = False
    for i in range(len(polygon)):
        j = (i + 1) % len(polygon)
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
    return inside

def localize_entities(data, room_vertices):
    if 'agents' in data:
        for agent in data['agents']:
            pose = agent.get('pose', [0, 0, 0])
            point = (pose[0], pose[1])
            for room_name, vertices in room_vertices.items():
                if is_point_in_polygon(point, vertices):
                    agent['localization'] = room_name
                    break
    if 'objects' in data:
        for obj in data['objects']:
            pose = obj.get('pose', [0, 0, 0])
            point = (pose[0], pose[1])
            for room_name, vertices in room_vertices.items():
                if is_point_in_polygon(point, vertices):
                    obj['localization'] = room_name
                    break
    return data

def main():
    print('Program started')
    sim.simxFinish(-1)  # just in case, close all opened connections
    clientID = sim.simxStart('127.0.0.1', 19982, True, True, 5000, 5)  # Connect to CoppeliaSim
    
    if clientID != -1:
        print('Connected to remote API server')
        file_paths = ['objects.json', 'agents.json', 'rooms.json']
        #res, p3_handle = sim.simxGetObjectHandle(clientID, 'P3DX', sim.simx_opmode_blocking)
        inicio = time.time()
        room_vertices = None
        for file_path in file_paths:
            data = load_json(file_path)
            if file_path == 'rooms.json':
                room_vertices = get_room_vertices(data)
            else:
                names = get_names(data)
                positions = {name: get_position_from_api(clientID, name) for name in names}
                
                updated_data = update_poses(data, positions)
                if room_vertices:
                    updated_data = localize_entities(updated_data, room_vertices)
                with open(file_path, 'w') as file:
                    json.dump(updated_data, file, indent=4)
        print(inicio-time.time())
    else:
        print('Failed connecting to remote API server')

if __name__ == '__main__':
    main()
