from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello world, from py HTTPS 1.1 server", 200

path_to_certs = "C:\\Users\\david\\capstone_sandbox\\gateway_controller_testing\\config_resources\\certs"
cert = path_to_certs + "\\cert.pem"
key = path_to_certs + "\\key.pem"

app.run(
    host="0.0.0.0", 
    port=30080,
    ssl_context=(cert, key)
    )

