import os
import uuid
import json
import pika
from flask import Flask, request, jsonify

app = Flask(__name__)

# Get RabbitMQ host from environment variable
RMQ_HOST = os.getenv('RABBITMQ_HOST', 'rmq-service')

@app.route('/match', methods=['POST'])
def match_event():
    # 1. Setup connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST))
    channel = connection.channel()

    # 2. Setup the special "Direct Reply-To" queue
    # This queue is built-in and doesn't need to be declared
    result = channel.queue_declare(queue='', exclusive=True, auto_delete=True)
    reply_queue = result.method.queue
    
    corr_id = str(uuid.uuid4())
    response = None

    # Callback function to catch the reply
    def on_response(ch, method, props, body):
        nonlocal response
        if props.correlation_id == corr_id:
            response = json.loads(body)

    # Listen on the temporary reply queue
    channel.basic_consume(queue=reply_queue, on_message_callback=on_response, auto_ack=True)

    # 3. Send the request to the Topic Exchange
    event_data = request.json
    channel.basic_publish(
        exchange='pst_exchange',
        routing_key='pst.matching.key',
        properties=pika.BasicProperties(
            reply_to=reply_queue,
            correlation_id=corr_id,
        ),
        body=json.dumps(event_data)
    )

    # 4. Wait/Block until the worker responds (with a timeout)
    count = 0
    while response is None and count < 50:  # ~5 second timeout
        connection.process_data_events(time_limit=0.1)
        count += 1

    connection.close()

    if response is None:
        return jsonify({"error": "Worker timeout"}), 504
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)