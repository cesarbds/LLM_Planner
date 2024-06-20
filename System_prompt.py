import json
import os 

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
def initialize_prompt():
    prompt_base = [
        {
            "role": "system",
            "content": """You are a tool to help a master summarize the data from a house sent to you in a few words after a query.

    In the objects documents, each object is represented as:

    id: number in the database
    name: object name
    localization: local in the house
    pose: pose in the house frame
    category: object category
    on-top: if it is on top of another object the value will not be null
    on-top: if it is on top of another object or agent the value will not be null
    resources: possible actions to do with the object (these three definitions are crucial)
    * pickeable: (if you can pick it up)
    * placeable: (if you can put it down again)
    * surface: (if it has a surface to put something on)

    You have the following documents:"""
        }
    ]

    # Append the loaded JSON data as a new document
    prompt_base.append({
        "role": "system",
        "content": f"\n# Objects:\n{json.dumps(load_json('objects.json'), indent=4)}"
    })

    # prompt_base.append({
    #     "role": "system",
    #     "content": f"\n# Rooms:\n{json.dumps(load_json('Projeto/agents.json'), indent=4)}"
    # })

    prompt_base.append({
        "role": "system",
        "content": f"\n# Agents:\n{json.dumps(load_json('agents.json'), indent=4)}"
    })
    return prompt_base