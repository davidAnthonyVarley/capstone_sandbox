import pika
import json
import threading
from flask import Flask, request

app = Flask(__name__)

# --- RABBITMQ WORKER LOGIC ---
def start_rabbitmq_consumer():
    # Connect to RabbitMQ (Update host for Kubernetes)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    # Declare the exchange and queue to listen to
    channel.exchange_declare(exchange='pst_exchange', exchange_type='topic')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='pst_exchange', queue=queue_name, routing_key='pst.matching.key')

    def on_request(ch, method, props, body):
        print(f" [x] Received request: {body}")
        
        # 1. Prepare the response
        response_data = {
            "message": "Hello from PST Worker!",
            "status": "matched"
        }

        # 2. Check if the Producer requested a reply
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