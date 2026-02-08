import pika
import json
import threading
import time  # Added for sleep
from flask import Flask, request

app = Flask(__name__)

# --- RABBITMQ WORKER LOGIC ---
def start_rabbitmq_consumer():
    user = 'admin'
    password = 'password123'
    credentials = pika.PlainCredentials(user, password)

    connection = None
    # 1. RETRY LOOP: Keep trying to connect until RabbitMQ is ready
    while connection is None:
        try:
            print(" [?] Attempting to connect to RabbitMQ (rmq-service)...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='rmq-service',
                credentials=credentials,
                connection_attempts=3,
                retry_delay=5)
            )
        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ not reachable yet. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f" [!] Unexpected error during connection: {e}")
            time.sleep(5)

    channel = connection.channel()

    # Declare the exchange and queue to listen to
    channel.exchange_declare(exchange='pst_exchange', exchange_type='topic', durable=True)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='pst_exchange', queue=queue_name, routing_key='pst.matching.key')

    def on_request(ch, method, props, body):
        # Improved debug printing
        print(f" [x] Received request: {body.decode()}")
        
        response_data = {
            "message": "Hello from PST Worker!",
            "status": "matched",
            "received_payload": json.loads(body)
        }

        if props.reply_to:
            print(f" [->] Replying to {props.reply_to} (ID: {props.correlation_id})")
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=json.dumps(response_data)
            )
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_request)

    print(" [*] RabbitMQ Worker successfully connected. Waiting for messages...")
    channel.start_consuming()

# --- FLASK ENDPOINTS ---
@app.route("/status")
def status():
    return {"status": "Worker is running"}, 200

if __name__ == "__main__":
    # Start RabbitMQ in a background thread
    worker_thread = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    worker_thread.start()
    
    # Run Flask
    app.run(host="0.0.0.0", port=3000)