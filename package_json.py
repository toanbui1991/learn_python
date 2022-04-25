import json

dictionary = {'one': 1, 'two': 2, 'three': 3}
jsonString = json.dumps(dictionary) #return String
print(f'type of jsonString: {type(jsonString)}')

#use dump method to conver object into stream
with open('dictionary.json', 'w') as file:
    json.dump(dictionary, file) 

#json.loads vs json.load
otherDict = json.loads(jsonString) #user loads when dezerialize json string into python object
print(f'type of otherDict: {type(otherDict)}')

with open('dictionary.json', 'r') as file:
    secondDict = json.load(file)
print(f'type of secondDict: {type(secondDict)}')