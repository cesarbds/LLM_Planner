try:
    import sim
except:
    print ('--------------------------------------------------------------')
    print ('"sim.py" could not be imported. This means very probably that')
    print ('either "sim.py" or the remoteApi library could not be found.')
    print ('Make sure both are in the same folder as this file,')
    print ('or appropriately adjust the file "sim.py"')
    print ('--------------------------------------------------------------')
    print ('')

import sys
import csv
import ctypes
import math
import time
import re
import json
from langchain import hub
from rich.pretty import pprint
from collections import Counter
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain.indexes import SQLRecordManager, index
from langchain_elasticsearch import ElasticsearchStore
from langchain_community.retrievers import BM25Retriever
from langchain.agents import AgentExecutor, create_react_agent
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.tools.tavily_search import TavilySearchResults
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from System_prompt import*
from React_prompt import prompt_base_react
from groq import Groq
import random
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import shutil
from shapely.geometry import Point, Polygon


# List to hold all parsed results
all_results = []
client = RemoteAPIClient()
sim2 = client.require('sim') 
objects_1 = ["banana", "apple", "cup", "plate", "laptop", "red_book", "green_book", "bowl", "bottle"]
places_1 = ["dinnertable", "smalltable", "bed", "rack", "kitchen_drawer", "countertop", "kitchnet"]

def check_p3dx_container(file_path):
    data = load_json(file_path)
    for agent in data['agents']:
        #print(agent['name']['first_name'] )
        #input('')
        if agent['name']['first_name'] == 'p3dx' and agent['container'] != 'empty':
            return False
    return True

def generate_phrase(objects_t, places_t, n):
    if n > len(objects_t) or n > len(places_t):
        return "Error: 'n' is larger than the number of available objects or places."
    
    selected_objects = random.sample(objects_t, n)
    selected_places = random.sample(places_t, n)
    
    actions = []
    for i in range(n):
        obj = selected_objects[i]
        place_t = selected_places[i].capitalize()
        if i == 0:
            actions.append(f"put the {obj} in the {place_t}")
        else:
            actions.append(f"then pick the {obj} and put it in the {place_t}")
    
    phrase = "Can you " + ", ".join(actions) + "?"
    return phrase

def find_room(position):    
    with open(file_paths_tmp[2], 'r') as file:
            data = json.load(file)
    point = Point(position)
    for room in data['rooms']:
        polygon = Polygon(room['area'])
        if polygon.contains(point):
            return room['name']
    return None

def modify_agent_file(object_name, key, new_value):
    try:
        # Lê o conteúdo do arquivo JSON
        with open(file_paths_tmp[2], 'r') as file:
            data = json.load(file)
        
        # Encontra o objeto com o id especificado e modifica o valor da chave
        for obj in data['agents']:
            if obj['name']['first_name'] == object_name:
                obj[key] = new_value
                if obj['container'] != "empty":
                  with open(file_paths_tmp[0], 'r') as file:
                    data2 = json.load(file)
                  for object in data2['objects']:
                     if object['name'] == obj['container']:
                        modify_object_file(object['name'], key, new_value)
                        break

        # Salva o conteúdo modificado de volta no arquivo JSON
        with open(file_paths_tmp[2], 'w') as file:
            json.dump(data, file, indent=4)

        #print(f"O valor da chave '{key}' do objeto com id {object_name} foi alterado para '{new_value}' com sucesso.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

def modify_object_file(object_name, key, new_value):
    try:
        # Lê o conteúdo do arquivo JSON
        with open(file_paths_tmp[0], 'r') as file:
            data = json.load(file)
        
        # Encontra o objeto com o id especificado e modifica o valor da chave
        for obj in data['objects']:
            if obj['name'] == object_name:
                obj[key] = new_value
                break

        # Salva o conteúdo modificado de volta no arquivo JSON
        with open(file_paths_tmp[0], 'w') as file:
            json.dump(data, file, indent=4)

        #print(f"O valor da chave '{key}' do objeto com id {object_name} foi alterado para '{new_value}' com sucesso.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

def copy_json_file(src, dest):
    try:
        # Copia o arquivo fonte para o destino
        shutil.copy(src, dest)
        #print(f"Arquivo {src} copiado para {dest} com sucesso.")
    except IOError as e:
        print(f"Erro ao copiar arquivo: {e}")



client       = Groq(api_key='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')
GROQ_API_KEY = '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'

places = {
   "smalltable" : [0.975, -1.62408, 0.42739],
   "smalltable2" : [1.2, -1.4, 0.42739],
   "bed" : [10.225, 3.750, 0.4],
   "bed2" : [10.99, 4.4, 0.4],
   "sofa" : [1.75433, -3.05705, 0.37494],
   "rack" : [4.175, -1.5, 0.6],
   "rack2" : [4.175, -2.1, 0.89],
   "rack3" : [4.175, -1.8, 1.19],
   "kitchnet" : [3.7, 4.95, 0.8905],
   "kitchnet2" : [3.4, 4.97, 0.8431],
   "kitchen_drawer" : [3.9, 2.7, 0.845],
   "kitchen_drawer2" : [3.92, 2.5, 0.84],
   "dinnertable2": [1.225, 1.075,0.85],
   "dinnertable": [1.80, 1.075,0.85],
   "countertop": [2.525, 3.350, 1.0]
}


rooms = {
    "kitchen": [2.95, 4.125],
    "diningroom": [2.025, 2.15],
    "livingroom": [2.725, -1.75],
    "toilet": [5.2, 4.15],
    "bedroom": [10.58, 2.9],
    "corridor": [6.2, 0.7],
    "bathroom": [8, 4.4]
}

objects = {
    "dinnertable": [1.955, 1.955],
    "coffe_maker": [3.375, 3.090],
    "fridge": [0.295, 4.195],
    "countertop": [1.875, 2.735],
    "sink": [3.1, 4.056],
    "microwave": [1.76, 4.0],
    "kitchen_drawer": [3.22, 2.5],
    "kitchnet": [2.25, 4.13],
    "stove": [1.57, 4.23],
    "bed": [9.625, 3.675],
    "toiletbowl": [4.9, 4.5],
    "handbasin": [5.3, 4.25],
    "sofa[0]": [0.625, 2.42],
    "sofa[1]": [1.8, 2.42],
    "smalltable": [2.3, -1.5],
    "tv_stand": [1.25, -0.66],
    "rack": [3.775, -1.7]
}


def generate(prompt, max_tokens=1024, temperature=0):
  completion = client.chat.completions.create(
    model="llama3-70b-8192",
    messages=prompt,
    temperature=1,
    max_tokens=1024,
    top_p=1,
    stream=False,
    stop=None,
  )
  return completion.choices[0].message.content

file_paths = ['objects.json', 'rooms.json', 'agents.json']
file_paths_tmp = ['objects_tmp.json', 'rooms_tmp.json', 'agents_tmp.json']

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def find_name_in_files(name, file_paths):
    for file_path in file_paths:
        data = load_json(file_path)
        if file_path == 'objects_tmp.json':
          for item in data['objects']:
              item_name = item['name']
              time.sleep(0.1)
              if item_name == name:
                  return file_path, item
        if file_path == 'rooms_tmp.json':
          for item in data['rooms']:
              item_name = item['name']
              time.sleep(0.1)
              if item_name == name:
                  return file_path, item
        if file_path == 'agents_tmp.json':  
          for item in data['agents']:
              item_name = item['name']
              time.sleep(0.1)
              if item_name == name:
                  return file_path, item
    return None, None

def look_around(input):
  try:
    handles, retFloats, objects_close, retBuffer = sim2.callScriptFunction("getCollisionObjects@./objects_detector",sim2.scripttype_childscript,[], [],[])
    return "You have the following objects: " + ", ".join(objects_close)
  #print(res, handles, retFloats, objects_close, retBuffer)
  except:
    return "Error while using the tool, try again"

def move_to(target):
  
  target = target.lower()
  #print(f"a{target}")
  file_path, item = find_name_in_files(target, file_paths_tmp)
  #print(file_path, item)
  if item:
    #pose = item['pose'][0:2] ##mudar para pegar a informação do infront of
    #pose.append(0.0)
    #res, retInts, retFloats, retStrings, retBuffer = sim.simxCallScriptFunction(clientID, 'remoteApiFunctions', sim.sim_scripttype_childscript, 'moveTo', [], [], ['P3DX', target], bytearray(), sim.simx_opmode_blocking)
    #ret = sim.simxGetObjectPosition(clientID, robot.robotHandle,-1, item['pose'][0:2], sim.simx_opmode_blocking)
   
    if file_path == 'objects_tmp.json':
      if target in objects:
        pose = []
        pose = objects[target]
        if len(pose) < 3:
          pose.append(0)
        #print("POSEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
        #print(pose)
        robotHandle = sim2.getObject("/P3DX")
        #print(robotHandle)
        try:
          tghandle, retFloats, retStrings, retBuffer = sim2.callScriptFunction('moveTo@./remoteApiFunctions', sim2.scripttype_childscript, [robotHandle], pose, ['P3DX'], '')
          print(f"\n Moving to the {target}")
          #sim2.setObjectPosition(robotHandle ,-1, pose)

          d = bytearray('busy'.encode('utf-8'))
          while d.decode('utf-8') !='reached':
            a = sim2.getStringSignal('status')
            if a != None:
              d = a
           
          modify_agent_file('p3dx', 'pose', pose)
          return f"Now you are in front of the {target}"
        except:
          return f"Error while going to the {target}. try again"
      else:
        return "You cannot go directly to a not static object."
      
    if file_path == 'rooms_tmp.json':
      pose = item['room_center']
      pose.append(+0.13868)
      #print(pose)
      if len(pose) == 3:
        robotHandle = sim2.getObject("/P3DX")
            #print(robotHandle)
        try:
          tghandle, retFloats, retStrings, retBuffer = sim2.callScriptFunction('moveTo@./remoteApiFunctions', sim2.scripttype_childscript, [robotHandle], pose, ['P3DX'], '')
          print(f"\n Moving to the {target}")
          #sim2.setObjectPosition(robotHandle ,-1, pose)
          d = bytearray('busy'.encode('utf-8'))
          while d.decode('utf-8') !='reached':
            a = sim2.getStringSignal('status')
            if a != None:
              d = a
          modify_agent_file('p3dx', 'pose', pose)
          modify_agent_file('p3dx', 'current_room', item['name'])
          return f"Now you are in the {target}"
        except:
          return f"Error, try again"
    if file_path == 'agents_tmp.json':
      return f"Now you are in front of the {target}"
  else:
        return "This is not a valid target to go."


clientID = 0

def pick(target):
  if check_p3dx_container(file_paths[2]):
  
    target = target.lower()
    file_path, item = find_name_in_files(target, file_paths_tmp)  
    #res, handles, retFloats, objects_close, retBuffer = sim.simxCallScriptFunction(clientID, 'remoteApiFunctions',sim.sim_scripttype_childscript,'getRobotCloseObjects',[], [],[],bytearray(),sim.simx_opmode_blocking)
    try:
      handles, retFloats, objects_close, retBuffer = sim2.callScriptFunction("getCollisionObjects@./objects_detector",sim2.scripttype_childscript,[], [],[])
    #print(res, handles, retFloats, objects_close, retBuffer)
      if item and file_path == 'objects_tmp.json':
        if item['resources']['pickeable']:
          objects_close = [s.lower() for s in objects_close]
          if target in objects_close:
            try:
              retInts, retFloats, retStrings, retBuffer = sim2.callScriptFunction('pick@./remoteApiFunctions', sim2.scripttype_childscript, [], [], [target], '')
              #print("/"+target.title())
              #object_handle = sim2.getObject("/"+target.title())
              robotHandle = sim2.getObject("/P3DX")
              #sim2.setObjectParent(object_handle, robotHandle, True)
              pos = sim2.getObjectPosition(robotHandle, -1)
              modify_object_file(target, 'pose', pos)
              modify_object_file(target, 'inside', 'p3dx')
              modify_object_file(target, 'on_top', None)
              modify_agent_file('p3dx', 'container', target)
              return f"Now you have the {target} object with you"
            except:
              return "Error while using the tool, try again"
          return f"The {target} is not close enough to be picked"
        return f"This {target} cannot be picked"
      return f'{target} is not an object, so cannot be picked'
    except:
      return 'Error, try again'
  else:
     return "You can only carry one thing at a time"

def place(input):
  #if len(input)==1:
  input = input.split(', ')
  target, place = input
  target = target.lower()
  place = place.lower()
  #else:
  #   raise ValueError('More than one object passed to the function')
  file_path, item = find_name_in_files(target, file_paths_tmp)
  file_path2, place_item = find_name_in_files(place, file_paths_tmp)
  if item and file_path == 'objects_tmp.json':
    handles, retFloats, objects_close, retBuffer = sim2.callScriptFunction("getCollisionObjects@./objects_detector",sim2.scripttype_childscript,[], [],[])
    objects_close = [s.lower() for s in objects_close]
    if target in objects_close:
      if item['resources']['placeable']: 
        if place in objects_close:
          if place_item['resources']['surface']:
            #print(target.title())
            obj = sim2.getObject("/" + target)
            # Start by getting the initial parent handle
            parentHandle = sim2.getObjectParent(obj)
            #print(parentHandle)
            # Loop until the parent handle is -1
            while parentHandle != -1:
                # Call the script function with the current parent handle
                retInts, retFloats, retStrings, retBuffer = sim2.callScriptFunction('getName@./remoteApiFunctions', sim2.scripttype_childscript,[parentHandle],[],[], '')
                
                # Print the returned strings for debugging
                #print(retStrings)
                
                # Check if "Left_Hand" is in the returned strings
                if "P3DX" in retStrings:
                    break
                
                # Get the next parent handle
                parentHandle = parentHandle = sim2.getObjectParent(obj)

            #if retStrings[0] == 'P3DX':
            if "P3DX" in retStrings:
              try:
                retInts, retFloats, retStrings, retBuffer = sim2.callScriptFunction('place@./remoteApiFunctions', sim2.scripttype_childscript, [], places[place], [target], '')
                modify_object_file(target, 'pose', places[place])
                modify_object_file(target, 'on_top', place)
                modify_object_file(target, 'inside', None)
                modify_agent_file('p3dx', 'container', "empty")
                return f"You just placed the {target} on top of the {place}"
              except:
                  return "Error while using the tool, try again"
            return f"You are not with the {target}"
          return f"{place} is not a valid place"
        return f"You are not close enough to the {place}"
      return f"This type of object cannot be placed"
    return f"{target} is not with you, so you cannot place it"
  return 'This is not an object, so cannot be placed and you are not with it'

def search(query):
    prompt_base = initialize_prompt()
    message={
            "role": "user",
            "content": query
        }
    #print(prompt_base)
    prompt_base.append(message)
    return generate(prompt_base)

def say(text):
  ##Utilizar text-to-speech para demonstração
  print(text)
  return "Tool used successfully"


def main():
   print ('Program started')
   # Copia o conteúdo do arquivo inicial para o arquivo temporário
   
   try:
      sim2.stopSimulation()
   except:
      pass
   time.sleep(1)
   sim2.loadScene(r'/home/cesar/Documents/Doutorado/IA_024/main/run_v2.ttt')
   sim2.startSimulation()
   time.sleep(2)
  
   if clientID!=-1:
        print ('Connected to remote API server')

        search_tool = Tool(
            name="Search",
            func=search,
            description="This tool provides information about the house enviroment that you are in. If you have any doubts about ojects location, rooms or agents, you SHOULD use this tool."
                        "Provides summarized context to answer the questions. "
                        "Use a detailed plain text question as input to the tool. Expected input: <query>"
        )

        look_around_tool = Tool(
            name="Vision",
            func=look_around,
            description="Provides the objects that are around you. "
                        "Just ask for the tool, with no parameters."
        )

        move_to_tool = Tool(
            name="Locomotion",
            func=move_to,
            description="Move the robot to the desired object or room. "
                        "Use the ONLY the name of the object or room desired as input to the tool. Expected input: <place name>" 
        )


        pick_tool = Tool(
            name="Manipulation_Pick",
            func=pick,
            description="Pick up an object if is close to the robot. Before use the manipulation, use the vision tool, to be sure that you are close enough to the desired object."
                        "Use ONLY the name of the desired object as input to the tool. Expected input: <desired object>"
        )

        place_tool = Tool(
            name = "Manipulation_Place",
            func = place,
            description = "Place an object on top of another object, if it possible.  Before use the manipulation, use the vision tool, to be sure that you are close enough to the desired place."
                          "Use the name of the desired object and where it put as input to the tool. Expected input: <desired object>, <only the name of the object to place>"
        )

        say_tool = Tool(
            name="Comunication",
            func=say,
            description="Say something to the human, used to answer questions, give explanations and interact with the user."
                        "Use a detailed plain text question as input to the tool."
        )

        prompt_base = prompt_base_react()
        prompt = PromptTemplate.from_template(prompt_base)
        llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="llama3-70b-8192")
        agent = create_react_agent(
            llm    = llm,
            tools  = [search_tool, look_around_tool, move_to_tool, pick_tool, place_tool, say_tool],
            prompt = prompt
        )
        
        agent_executor = AgentExecutor(agent=agent, tools = [search_tool, look_around_tool, move_to_tool, pick_tool, place_tool, say_tool], verbose = True, handle_parsing_errors=True, max_iterations= 25)

        for i in range(21,50):
          all_results = []
          chunks = [] 
          copy_json_file(file_paths[0], file_paths_tmp[0])
          copy_json_file(file_paths[1], file_paths_tmp[1])
          copy_json_file(file_paths[2], file_paths_tmp[2])
          question = generate_phrase(objects_1, places_1, 1)
          print(question)
          # a = agent_executor.stream({"input": question})
          # print(a)
          

          for chunk in agent_executor.stream(
              ({"input": question})
          ):
              chunks.append(chunk)
              #print("------")
              #print(chunk)
          sim2.stopSimulation()
          time.sleep(1)
          sim2.startSimulation()
          # Accessing and printing the content of all messages
             # Accessing and processing each chunk
          for entry in chunks:
              if 'messages' in entry:
                  for message in entry['messages']:
                      # Splitting the content string into lines
                      lines = message.content.split('\n')

                      # Initializing a dictionary to store the separated elements
                      result = {
                         "Query": question,
                          "Thought": "",
                          "Reasoning": "",
                          "Action": "",
                          "Action Input": "",
                          "Tool Answer": ""
                      }

                      # Iterating over the lines and categorizing them
                      for line in lines:
                          if line.startswith("Thought:"):
                              result["Thought"] = line[len("Thought: "):]
                          elif line.startswith("Reasoning:"):
                              result["Reasoning"] = line[len("Reasoning: "):]
                          elif line.startswith("Action:"):
                              result["Action"] = line[len("Action: "):]
                          elif line.startswith("Action Input:"):
                              result["Action Input"] = line[len("Action Input: "):]
                          else:
                              result["Tool Answer"] = line

                      # Append the result to all_results
                      all_results.append(result)

          # Define the header for the CSV file
          header = ['Query', 'Thought', 'Reasoning', 'Action', 'Action Input', 'Tool Answer']

          # Write the results to a CSV file
          with open(f'One_task/results_{i}.csv', 'w', newline='') as file:
              writer = csv.DictWriter(file, fieldnames=header, delimiter=';')
              writer.writeheader()
              writer.writerows(all_results)

          print("Results saved to results.csv") 

                    # Printing the result
                    #print(result)
        
        #print(sim2.callScriptFunction("getCollisionObjects@./objects_detector",sim2.scripttype_childscript,[], [],[]))
        #sim2.simxgetObjectPosition()
        sim2.stopSimulation()
        #print(search("where is the book"))
        #print(search('Where is Eric'))
        # print(pick("plate"))
        # print(place("plate, countertop"))
        #print(move_to('Bed'))


if __name__ == '__main__':
    main()