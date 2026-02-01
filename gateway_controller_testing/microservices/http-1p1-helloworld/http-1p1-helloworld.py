from flask import Flask, request

app = Flask(__name__)

@app.route("/get")
def hello():
    # 1. Get all headers as a dictionary-like object
    all_headers = dict(request.headers)
    
    # 2. Get a specific header (e.g., User-Agent)
    user_agent = request.headers.get('User-Agent')
    
    print(f"User-Agent: {user_agent}")
    print(f"All Headers: {all_headers}")

    return {
        "message": "Hello world, from py HTTP 1.1 server",
        "your_headers": all_headers
    }, 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", 
        port=3000
    )