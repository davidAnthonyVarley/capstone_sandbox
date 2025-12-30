import requests

url = "http://localhost:30080/"

response = requests.get(url) 
print(response.status_code)
print(response.text)
