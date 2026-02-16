import pika
import json, time
import threading
from flask import Flask, request

app = Flask(__name__)

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
    channel.queue_bind(exchange='pst_exchange', queue=queue_name, routing_key='pst.matching.key')

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
            "message": "Hello from subscriber that got the message from the message queue!",
            "status": "matched",
            "worker_debug": {
                "headers_received": original_headers,
                "original_body": incoming_data.get("payload", {})
            }
        }

        # 4. Check if the Producer requested a reply
        if props.reply_to:
            print(f" [->] Replying to {props.reply_to}")
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=json.dumps(response_data)
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_request)

    print(" [*] RabbitMQ Worker started. Waiting for messages...")
    channel.start_consuming()

# --- FLASK ENDPOINTS (For Health Checks/Debug) ---
@app.route("/status")
def status():
    return {"status": "Worker is running"}, 200

if __name__ == "__main__":
    # Start RabbitMQ in a background thread so Flask can still run
    threading.Thread(target=start_rabbitmq_consumer, daemon=True).start()
    
    app.run(host="0.0.0.0", port=3000)