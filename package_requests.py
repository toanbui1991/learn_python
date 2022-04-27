import requests

response = requests.get('https://api.github.com/events')
result = response.json() #return python object or deserialized 
print(f'type of result: {type(result)}')
print('result: ', len(result))
print('first element of result: ')
print(result[0])

