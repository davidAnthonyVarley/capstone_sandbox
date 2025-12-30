import requests

#host = "192.168.49.2"
#port = "30443"
#host = "minikube.local"
port = "30001"
host = "localhost" #NOTE, this can't be 127.0.0.1 because the cert is only designed to accept connection from 1
#port = "61449"



url = f"https://{host}:{port}/"
path_to_certs = "C:\\Users\\david\\capstone_sandbox\\gateway_controller_testing\\certs"
cert = path_to_certs + "\\cert.pem"

response = requests.get(url, verify=cert) 
print(response.status_code)
print(response.text)
