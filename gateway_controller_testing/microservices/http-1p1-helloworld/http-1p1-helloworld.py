from flask import Flask

app = Flask(__name__)

@app.route("/get")
def hello():
    return "Hello world, from py HTTP 1.1 server", 200

app.run(
    host="0.0.0.0", 
    port=3000
    )

