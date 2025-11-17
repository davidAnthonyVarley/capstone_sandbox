import requests

url = "https://localhost:3443/"

response = requests.get(url, verify="cert.pem")  # path to your self-signed cert
print(response.status_code)
print(response.text)
