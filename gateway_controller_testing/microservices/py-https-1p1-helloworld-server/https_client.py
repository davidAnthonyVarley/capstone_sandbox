import requests

url = "https://localhost:30080/"
path_to_certs = "C:\\Users\\david\\capstone_sandbox\\gateway_controller_testing\\config_resources\\certs"
cert = path_to_certs + "\\cert.pem"

response = requests.get(url, verify=cert) 
print(response.status_code)
print(response.text)
