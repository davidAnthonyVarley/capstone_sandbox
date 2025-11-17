import socket
import ssl
import h2.config
import h2.connection
import h2.events

# --- Configuration ---
SERVER_HOST = 'localhost'
SERVER_PORT = 30002

project_root = "C:\\Users\\david\\capstone_sandbox\\gateway_controller_testing"
certs_folder = project_root + "\\certs"
CERTFILE = certs_folder + '\\cert.pem'

# --- 1. Establish Secure Connection (TLS) ---
def connect_secure_socket(host, port):
    """
    Creates a secure, non-blocking socket and performs the TLS handshake,
    negotiating the HTTP/2 protocol via ALPN.
    """
    print(f"1. Attempting to connect to {host}:{port}...")

    # Set up SSL Context
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    
    # CRITICAL: We need to negotiate the 'h2' protocol via ALPN
    ssl_context.set_alpn_protocols(['h2'])

    # NOTE: Disabling certificate verification for simplicity with self-signed certificates. 
    # This is INSECURE for production use!
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Create a raw socket
    sock = socket.create_connection((host, port))
    
    # Wrap the socket with the SSL context
    secure_sock = ssl_context.wrap_socket(sock, server_hostname=host)

    # Verify that h2 was successfully negotiated
    negotiated_protocol = secure_sock.selected_alpn_protocol()
    if negotiated_protocol != 'h2':
        raise Exception(f"Failed to negotiate HTTP/2 (ALPN negotiated: {negotiated_protocol})")
    
    print("   -> TLS handshake successful. Protocol negotiated: h2")
    return secure_sock
# --- 2. H2 Client Logic ---


def query_http2_server(sock, path='/'):
    """
    Sends an HTTP/2 request over the secure socket and processes the response.
    
    Args:
        sock (ssl.SSLSocket): The established and ALPN-negotiated secure socket.
        path (str): The URL path to request.
    
    Returns:
        str: The decoded body of the HTTP/2 response, or an error message.
    """
    # Initialize the client-side H2 state machine
    config = h2.config.H2Configuration(client_side=True)
    conn = h2.connection.H2Connection(config=config)

    responses = {}
    
    # 1. Initiate Connection
    # Send initial connection frames (like SETTINGS)
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())

    # --- Construct and Send Request Headers (The Message Trigger) ---
    print(f"\n2. Sending GET request for path: {path}")
    
    # Define HTTP/2 pseudo-headers (Note: SERVER_HOST must be accessible)
    headers = [
        (b':method', b'GET'),  # Use byte strings for pseudo-headers
        (b':authority', SERVER_HOST.encode('utf-8')),
        (b':scheme', b'https'),
        (b':path', path.encode('utf-8')),
        (b'user-agent', b'h2-python-client'),
    ]
    
    # Generate the binary HEADERS frame for a new stream
    stream_id = conn.get_next_available_stream_id()
    conn.send_headers(
        stream_id, 
        headers, 
        end_stream=True  # Marks the end of the request (no body data)
    )
    
    # Flush the buffered frame onto the network socket
    sock.sendall(conn.data_to_send())

    print("3. Receiving data and processing H2 frames...")
    
    while True:
        try:
            # Receive raw binary data from the network
            data = sock.recv(65535)
        except ssl.SSLWantReadError:
            # Non-blocking read error (in a synchronous context, this usually means stop trying)
            break

        if not data:
            # Connection closed cleanly by the server
            break

        # Feed data into the H2 state machine and get high-level events
        # 'events' is guaranteed to be defined here.
        events = conn.receive_data(data)

        # Process events
        for event in events:
            if isinstance(event, h2.events.ResponseReceived):
                
                # --- FIX: Extract status using byte string lookup or iteration ---
                status_bytes = [v for n, v in event.headers if n == b':status'][0]
                status = status_bytes.decode('utf-8')
                
                print(f"   -> Response Headers received on stream {event.stream_id}: Status {status}")
            
            elif isinstance(event, h2.events.DataReceived):
                # Accumulate the response body data
                responses[event.stream_id] = responses.get(event.stream_id, b'') + event.data
                
                # Update flow control window to allow more data
                conn.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
            
            elif isinstance(event, h2.events.StreamEnded):
                print(f"   -> Stream {event.stream_id} finished.")
                if event.stream_id == stream_id:
                    # Request is complete. Close connection and return result.
                    sock.close()
                    return responses.get(stream_id, b'').decode('utf-8')

            elif isinstance(event, h2.events.PushedStreamReceived):
                print(f"   -> Server Push detected (Stream ID: {event.pushed_stream_id}).")
                
        # Send any control frames generated by event processing (e.g., WINDOW_UPDATE)
        sock.sendall(conn.data_to_send())
    
    return "Connection closed before full response received."
# --- Main Execution ---
if __name__ == '__main__':
    try:
        # 1. Establish connection and ALPN negotiation
        secure_socket = connect_secure_socket(SERVER_HOST, SERVER_PORT)

        # 2. Send request and receive response
        response_body = query_http2_server(secure_socket, path='/')
        
        print("\n4. Final Response Body:")
        print("-----------------------------------")
        print(response_body)
        print("-----------------------------------")

    except FileNotFoundError:
        print("\n!!! ERROR: Key or certificate file not found. !!!")
        print(f"Ensure key.pem and cert.pem are in the same directory.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print(f"\n*** Check the Node.js HTTP/2 server is running on https://localhost:{SERVER_PORT}/ ***")