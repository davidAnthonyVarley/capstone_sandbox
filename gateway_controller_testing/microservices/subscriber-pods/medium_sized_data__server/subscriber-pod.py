import pika
import json, time
import threading, os
from flask import Flask, request
import base64

app = Flask(__name__)

SUB_ID = os.getenv("SUB_ID")

# 1. Create a global variable to hold the cached data
CACHED_FILE_DATA = None

def load_data_to_memory():
    global CACHED_FILE_DATA
    file_path = "TBD"
    if (SUB_ID == "small-sized-data-server--1mb"):
        file_path = "/mnt/testing-data/1mb_test.bin"
    elif (SUB_ID == "medium-sized-data-server--10mb"):
        file_path = "/mnt/testing-data/10mb_test.bin"
    elif (SUB_ID == "large-sized-data-server--10mb"):
        file_path = "/mnt/testing-data/100mb_test.bin"
    else:
        print("*")
        print("*")
        print("*")
        print(f"ERROR: VOLUME DATA NOT FOUND FOR SUB_ID == {SUB_ID}")
        print("*")
        print("*")
        print("*")

    
    try:
        if os.path.exists(file_path):
            print(f"--- Loading {file_path} into memory ---", flush=True)
            with open(file_path, "rb") as f:
                # Store as Base64 string to be ready for JSON responses 
                CACHED_FILE_DATA = base64.b64encode(f.read()).decode('utf-8')
            print(f"--- Successfully cached {len(CACHED_FILE_DATA)} bytes ---", flush=True)
        else:
            print(f"--- Warning: File not found at {file_path} ---", flush=True)
    except Exception as e:
        print(f"--- Error during boot-load: {e} ---", flush=True)

# --- RABBITMQ WORKER LOGIC ---
def start_rabbitmq_consumer():
    # Connect to RabbitMQ (Update host for Kubernetes)

    user = 'admin'
    password = 'password123'
    credentials = pika.PlainCredentials(user, password)
    
    connection = None
    while connection is None:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='rmq-service', credentials=credentials))
        except pika.exceptions.AMQPConnectionError:
            print(" [!] Waiting for RabbitMQ... retrying in 5s", flush=True)
            time.sleep(3)
    channel = connection.channel()

    # Declare the exchange and queue to listen to
    channel.exchange_declare(exchange='cbr_exchange', exchange_type='topic', durable=True)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='cbr_exchange', queue=queue_name, routing_key=SUB_ID)

    def on_request(ch, method, props, body):
        # 1. Parse the JSON sent by the Producer
        incoming_data = {"message": "you should not be seeing this data, there has been an error"}
        try:
            incoming_data = json.loads(body)
        except Exception:
            incoming_data = {"raw": body.decode()}

        # 2. Get the headers the Producer (hopefully) passed along
        # If the Producer isn't sending them yet, this stays as an empty dict
        original_headers = incoming_data.get("original_headers", {})

        print("--- Received from RabbitMQ ---", flush=True)
        print(f"Original Method (from Producer): {incoming_data.get('method', 'N/A')}", flush=True)
        print(f"Captured Headers: {original_headers}", flush=True)
        print("------------------------------", flush=True)

        # 3. Prepare the response
        response_data = {
            "message": f"Hello from subscriber {SUB_ID}!",
            "status": "success" if CACHED_FILE_DATA else "no_data_cached",
            "file_data": CACHED_FILE_DATA, # Fast memory access
            "worker_debug": {
                "original_headers": original_headers,
                "source": "memory_cache"
            }
        }

        if props.reply_to:
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=json.dumps(response_data)
            )

        print("the message has been sent off from the server")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_request)

    print(" [*] RabbitMQ Worker started. Waiting for messages...")
    channel.start_consuming()

# --- FLASK ENDPOINTS (For Health Checks/Debug) ---
@app.route("/status")
def status():
    return {"status": "Worker is running"}, 200



# Add this near the top of subscriber-pod.py
def check_storage():
    mount_path = "/mnt/testing_data"  # This is where we will mount it in K8s
    if os.path.exists(mount_path):
        print(f"--- Storage Found at {mount_path} ---", flush=True)
        print(f"Files: {os.listdir(mount_path)}", flush=True)
    else:
        print(f"--- Storage NOT Found at {mount_path} ---", flush=True)

# Call it in your main block
if __name__ == "__main__":
    check_storage() # Run the check on startup
    load_data_to_memory() # Run the check on startup
    threading.Thread(target=start_rabbitmq_consumer, daemon=True).start()
    app.run(host="0.0.0.0", port=3000)