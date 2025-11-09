from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "hi there from python app", 200

app.run(host="0.0.0.0", port=30080)

