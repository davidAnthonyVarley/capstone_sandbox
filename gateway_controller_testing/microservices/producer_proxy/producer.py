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
    # 1. Debug Prints
    print("--- Incoming Request Debug ---", flush=True)
    print(f"Headers: \n{request.headers}", flush=True)
    print("------------------------------", flush=True)

    # 2. Extract and Parse the X-Matched-Subscribers header
    matched_subs_raw = request.headers.get("X-Matched-Subscribers", "")
    # Split by comma, strip whitespace, and remove empty entries
    routing_keys = [s.strip() for s in matched_subs_raw.split(",") if s.strip()]

    if not routing_keys:
        return jsonify({"error": "No subscribers found in X-Matched-Subscribers header"}), 400

    # 3. Prepare data to send
    headers_to_send = dict(request.headers)
    event_data = {
        "payload": request.get_json(silent=True) or {},
        "original_headers": headers_to_send,
        "method": request.method
    }

    # 4. Setup RabbitMQ Connection
    user = 'admin'
    password = 'password123'
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RMQ_HOST,
        credentials=credentials)
    )
    channel = connection.channel()

    # 5. Setup for Multiple Responses
    result = channel.queue_declare(queue='', exclusive=True, auto_delete=True)
    reply_queue = result.method.queue
    corr_id = str(uuid.uuid4())
    
    responses = [] # List to store multiple responses instead of a single variable

    # Callback to collect every response matching the correlation_id
    def on_response(ch, method, props, body):
        if props.correlation_id == corr_id:
            responses.append(json.loads(body))

    channel.basic_consume(queue=reply_queue, on_message_callback=on_response, auto_ack=True)

    # 6. Send a request to EACH routing key extracted from the header
    for key in routing_keys:
        print(f" [->] Sending request to routing_key: {key}", flush=True)
        channel.basic_publish(
            exchange='cbr_exchange', #
            routing_key=key,         # Use the header value as the routing key
            properties=pika.BasicProperties(
                reply_to=reply_queue,
                correlation_id=corr_id,
            ),
            body=json.dumps(event_data)
        )

    # 7. Wait for all responses
    # Loop until the number of responses matches the number of keys sent (with a timeout)
    expected_count = len(routing_keys)
    count = 0
    while len(responses) < expected_count and count < 100:
        connection.process_data_events(time_limit=0.1)
        count += 1

    connection.close()

    # 8. Return the aggregated results
    return jsonify({
        "requested_subscribers": routing_keys,
        "received_responses_count": len(responses),
        "responses": responses
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)