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
from System_prompt import*
from React_prompt import prompt_base_react
from groq import Groq

from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

client       = Groq(api_key='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')
GROQ_API_KEY = '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'

rooms = {
    "Kitchen": [2.95, 4.125],
    "DiningRoom": [2.025, 2.15],
    "Livingroom": [2.725, -1.75],
    "Toilet": [5.2, 4.15],
    "Bedroom": [1.06, 2.95],
    "Corridor": [6.2, 0.7],
    "Bathroom": [8, 4.4]
}

objects = {
    "DinerTable": [1.955, 1.955],
    "Coffe_maker": [3.375, 3.090],
    "Fridge": [0.295, 4.195],
    "Countertop": [1.875, 2.735],
    "Sink": [3.1, 4.056],
    "Microwave": [1.76, 4.0],
    "Kitchen_drawer": [2.845, 1.225],
    "Kitchnet": [2.25, 4.13],
    "Stove": [1.57, 4.23],
    "Bed": [9.625, 3.675],
    "ToiletBowl": [4.9, 4.5],
    "HandBasin": [5.3, 4.25],
    "Sofa[0]": [0.625, 2.42],
    "Sofa[1]": [1.8, 2.42],
    "SmallTable": [2.3, 1.5],
    "TV_Stand": [1.25, -0.66],
    "Rack": [3.775, -1.7]
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

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def find_name_in_files(name, file_paths):
    for file_path in file_paths:
        data = load_json(file_path)
        if file_path == 'objects.json':
          for item in data['objects']:
              if item['name'] == name:
                  return file_path, item
        if file_path == 'rooms.json':
          for item in data['rooms']:
              if item['name'] == name:
                  return file_path, item
        if file_path == 'agents.json':
          for item in data['agents']:
              if item['name'] == name:
                  return file_path, item
    return None, None

def look_around(input):
  res, handles, retFloats, objects_close, retBuffer = sim.simxCallScriptFunction(clientID,'/P3DX/objects_detector',sim.sim_scripttype_childscript,'getCollisionObjects',[], [],[],bytearray(),sim.simx_opmode_blocking)
  #print(res, handles, retFloats, objects_close, retBuffer)
  if res != 0:
    return "Error while using the tool, try again"
  return "You have the following objects: " + ", ".join(objects_close)

def move_to(target):
  file_path, item = find_name_in_files(target, file_paths)

  if item:
    #pose = item['pose'][0:2] ##mudar para pegar a informação do infront of
    #pose.append(0.0)
    #res, retInts, retFloats, retStrings, retBuffer = sim.simxCallScriptFunction(clientID, 'remoteApiFunctions', sim.sim_scripttype_childscript, 'moveTo', [], [], ['P3DX', target], bytearray(), sim.simx_opmode_blocking)
    #ret = sim.simxGetObjectPosition(clientID, robot.robotHandle,-1, item['pose'][0:2], sim.simx_opmode_blocking)
   
    if file_path == 'objects.json':
      pose = objects[target]
      pose.append(+0.13868)
      ret, robotHandle = sim.simxGetObjectHandle(clientID, "/P3DX", sim.simx_opmode_blocking)
      retCode = sim.simxSetObjectPosition(clientID, robotHandle ,-1,pose,sim.simx_opmode_blocking )

      if retCode == 0:
        return f"Now you are in front of the {target}"
      return f"Error while going to the {target}. try again"
    if file_path == 'rooms.json':
      return f"Now you are in the {target}"
    if file_path == 'agents.json':
      return f"Now you are in front of the {target}"
  else:
        return "This is not a valid target to go."

clientID = 0

def pick(target):
  file_path, item = find_name_in_files(target, file_paths)
  print('oi')
  
  #res, handles, retFloats, objects_close, retBuffer = sim.simxCallScriptFunction(clientID, 'remoteApiFunctions',sim.sim_scripttype_childscript,'getRobotCloseObjects',[], [],[],bytearray(),sim.simx_opmode_blocking)
  res, handles, retFloats, objects_close, retBuffer = sim.simxCallScriptFunction(clientID,'/P3DX/objects_detector',sim.sim_scripttype_childscript,'getCollisionObjects',[], [],[],bytearray(),sim.simx_opmode_blocking)
  print(res, handles, retFloats, objects_close, retBuffer)
  if res == 0:
    if item and file_path == 'objects.json':
      if item['resources']['pickeable']:
        if target in objects_close:
          res, retInts, retFloats, retStrings, retBuffer = sim.simxCallScriptFunction(clientID, 'remoteApiFunctions', sim.sim_scripttype_childscript, 'pick', [], [], [target], bytearray(), sim.simx_opmode_blocking)
          res, object_handle = sim.simxGetObjectHandle(clientID, "/"+target, sim.simx_opmode_blocking)
          ret, robotHandle = sim.simxGetObjectHandle(clientID, "/P3DX", sim.simx_opmode_blocking)
          res = sim.simxSetObjectParent(clientID, object_handle, robotHandle, True ,sim.simx_opmode_blocking)
          if res != 0:
            return "Error while using the tool, try again"
          return f"Now you have the {target} object with you"
        return f"The {target} is not close enough to be picked"
      return f"This {target} cannot be picked"
    return f'{target} is not an object, so cannot be picked'
  return 'Error'

def place(target, place):
  file_path, item = find_name_in_files(target, file_paths)
  file_path, place_item = find_name_in_files(place, file_paths)
  ###CRIAR UMA TABELA COM AS POSIÇÕES ACIMA DAS COISAS PARA COLOCAR
  if item and file_path == 'objects.json':
    if True:
      if item['resources']['placeable']:
        res, handles, retFloats, objects_close, retBuffer = sim.simxCallScriptFunction(clientID,'/P3DX/objects_detector',sim.sim_scripttype_childscript,'getCollisionObjects',[], [],[],bytearray(),sim.simx_opmode_blocking)
        if item['name'] in objects_close:
          res, obj = sim.simxGetObjectHandle(clientID, target, sim.simx_opmode_blocking)
          # Start by getting the initial parent handle
          res, parentHandle = sim.simxGetObjectParent(clientID, obj, sim.simx_opmode_blocking)
          print(parentHandle)
          # Loop until the parent handle is -1
          while parentHandle != -1:
              # Call the script function with the current parent handle
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
              
              # Print the returned strings for debugging
              print(retStrings)
              
              # Check if "Left_Hand" is in the returned strings
              if "P3DX" in retStrings:
                  break
              
              # Get the next parent handle
              res, parentHandle = sim.simxGetObjectParent(clientID, parentHandle, sim.simx_opmode_blocking)

          if retStrings[0] == 'P3DX':
            res, collision_state, retFloats, objects_close, retBuffer = sim.simxCallScriptFunction(clientID,'/PioneerP3DX/objects_detector',sim.sim_scripttype_childscript,'getCollisionObjects',[], [],[],bytearray(),sim.simx_opmode_blocking )
            res, object_handle = sim.simxGetObjectHandle(clientID, "/"+target, sim.simx_opmode_blocking)
            res, retInts, retFloats, retStrings, retBuffer = sim.simxCallScriptFunction(clientID, 'remoteApiFunctions', sim.sim_scripttype_childscript, 'place', [], places[place], [target], bytearray(), sim.simx_opmode_blocking)
            if res != 0:
                return "Error while using the tool, try again"
            return f"You just placed the {target} on top of the {place}"
          return f"You are not with the {target}"
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
   sim.simxFinish(-1) # just in case, close all opened connections
   clientID=sim.simxStart('127.0.0.1',19982,True,True,5000,5) # Connect to CoppeliaSim
   print(clientID)
   if clientID!=-1:
        print ('Connected to remote API server')

        search_tool = Tool(
            name="Search",
            func=search,
            description="This tool provides information about the house enviroment that you are in. If you have any doubts about ojects location, rooms or agents, you SHOULD use this tool."
                        "Provides summarized context to answer the questions. "
                        "Use a detailed plain text question as input to the tool."
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
                        "Use the name of the object or room desired as input to the tool."
        )


        pick_tool = Tool(
            name="Manipulation_Pick",
            func=pick,
            description="Pick up an object if is close to the robot. "
                        "Use the name of the desired object as input to the tool."
        )

        place_tool = Tool(
            name = "Manipulation_Place",
            func = place,
            description = "Place an object on top of another object, if it possible "
                        "Use the name of the desired object and where it put as input to the tool."
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
        agent_executor = AgentExecutor(agent=agent, tools = [search_tool, look_around_tool, move_to_tool, pick_tool, place_tool, say_tool], verbose = True, handle_parsing_errors=True, max_iterations= 50)
        question = "Can you get me the Banana?"
        agent_executor.invoke({
                "input": question
            })
        #print(search("where is the book"))
        #print(search('Where is Eric'))
        #print(pick("Cup"))
        #print(move_to('Rack'))

if __name__ == '__main__':
    main()