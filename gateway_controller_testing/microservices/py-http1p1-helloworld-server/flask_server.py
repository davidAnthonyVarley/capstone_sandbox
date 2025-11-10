from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello world, from py http1.1 server", 200

app.run(host="0.0.0.0", port=30080)

