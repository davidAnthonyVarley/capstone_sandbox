import os
import uuid
import json
import pika
from flask import Flask, request, jsonify

app = Flask(__name__)

# Get RabbitMQ host from environment variable
RMQ_HOST = os.getenv('RABBITMQ_HOST', 'rmq-service')

@app.route('/mq', methods=['GET'])
def match_event():
    # 1. Debug Prints (Run first)
    print("--- Incoming Request Debug ---", flush=True)
    print(f"Method: {request.method}", flush=True)
    print(f"Path: {request.path}", flush=True)
    print(f"Headers: \n{request.headers}", flush=True)
    print(f"Raw Data: {request.get_data(as_text=True)}", flush=True)
    print("------------------------------", flush=True)
    #headers_to_send = {k: v for k, v in request.headers.items()}
    headers_to_send = dict(request.headers)
    
    event_data = {
        "payload": request.get_json(silent=True) or {},
        "original_headers": headers_to_send,
        "method": request.method
    }
    # 2. Handle incoming data safely
    if event_data is None:
        event_data = {"status": "default_payload_because_no_json_sent, or because 'event_data' was None"}

    # 3. Setup RabbitMQ Connection
    user = 'admin'
    password = 'password123'
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='rmq-service',
        credentials=credentials)
    )
    channel = connection.channel()

    # 4. Setup variables for the Reply-To pattern
    # result and reply_queue MUST be defined before basic_publish
    result = channel.queue_declare(queue='', exclusive=True, auto_delete=True)
    reply_queue = result.method.queue
    corr_id = str(uuid.uuid4())
    response = None

    #yoooooooo

    # Callback function to catch the reply
    def on_response(ch, method, props, body):
        nonlocal response
        if props.correlation_id == corr_id:
            response = json.loads(body)

    # Start listening for the reply
    channel.basic_consume(queue=reply_queue, on_message_callback=on_response, auto_ack=True)

    # 5. Send the request (Now reply_queue is defined!)
    channel.basic_publish(
        exchange='pst_exchange',
        routing_key='pst.matching.key',
        properties=pika.BasicProperties(
            reply_to=reply_queue,
            correlation_id=corr_id,
        ),
        body=json.dumps(event_data)
    )

    # 6. Wait for worker response
    count = 0
    while response is None and count < 50:
        connection.process_data_events(time_limit=0.1)
        count += 1

    connection.close()

    if response is None:
        return jsonify({"error": "Worker timeout"}), 504
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)