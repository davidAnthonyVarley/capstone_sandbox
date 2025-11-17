import asyncio
import sys
import argparse
import os

from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import StreamDataReceived, QuicEvent
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived, H3Event

# ALPN should use the latest stable h3 version
H3_ALPN_LIST = ["h3", "h3-32", "h3-31", "h3-30", "h3-29"] 

class Http3ServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the HTTP/3 layer
        self.h3 = H3Connection(self._quic)

    def quic_event_received(self, event: QuicEvent):
        # 1. Pass the QUIC event to the HTTP/3 layer
        # Iterate over the resulting HTTP/3 events
        for http_event in self.h3.handle_event(event):
            self.handle_http3_event(http_event)

    def handle_http3_event(self, event: H3Event):
        if isinstance(event, HeadersReceived):
            # This is the start of a request
            # Check if this is a simple GET request on a bidirectional stream
            if not event.stream_id % 2 and event.headers:
                
                # Simple check for headers (you'd need a more robust parser normally)
                method = next((v.decode() for k, v in event.headers if k == b':method'), None)
                path = next((v.decode() for k, v in event.headers if k == b':path'), None)
                
                if method == "GET" and path == "/":
                    self.send_response(event.stream_id)

        # In a real server, you'd also handle DataReceived for POST requests
        elif isinstance(event, DataReceived):
             # You could process the data here, but for a simple GET, we ignore it
             pass

    def send_response(self, stream_id: int):
        # 1. Send response headers (using the H3 layer)
        self.h3.send_headers(
            stream_id=stream_id,
            headers=[
                (b":status", b"200"),
                (b"content-type", b"text/plain"),
                (b"server", b"aioquic-h3-server"),
            ],
            end_stream=False # Headers always come first
        )
        
        # 2. Send response body (Data Frame)
        self.h3.send_data(
            stream_id=stream_id,
            data=b"HTTP/3 Hello World!\n",
            end_stream=True # Set end_stream=True to close the stream after the body
        )
        
        # 3. Flush the H3 data to the underlying QUIC connection
        #self.quic.transmit()

def parse_arguments():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="A simple HTTP/3 server")
    
    # Define --cert and --key arguments, which will be passed from K8s
    parser.add_argument(
        "--cert",
        type=str,
        required=True,
        help="Path to the TLS certificate file (e.g., /certs/tls.crt)"
    )
    parser.add_argument(
        "--key",
        type=str,
        required=True,
        help="Path to the TLS private key file (e.g., /certs/tls.key)"
    )
    # Add other arguments if necessary (like --host or --port)
    parser.add_argument(
        "--port",
        type=int,
        default=30433,
        help="Port to listen on"
    )

    # Parse args, excluding the script name itself (sys.argv[0])
    # Note: When run via K8s args, you may receive the script name, but argparse handles this well.
    return parser.parse_args(sys.argv[1:])


async def main():

    
    
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=H3_ALPN_LIST, 
    )
    
    # arguments for kubernetes deployment
    host = "0.0.0.0"
    args = parse_arguments()
    port = args.port
    cert_path = args.cert
    key_path = args.key

    #for local dev
    #host = "localhost"
    #port = 30003
#
    #project_root = "C:\\Users\\david\\capstone_sandbox\\gateway_controller_testing"
    #certs_folder = os.path.join(project_root, "certs")
    #key_path = os.path.join(certs_folder, 'key.pem')
    #cert_path = os.path.join(certs_folder, 'cert.pem')

    try:
        # Load the certificate chain using the provided paths
        configuration.load_cert_chain(cert_path, key_path)
    except FileNotFoundError:
        # FileNotFoundError directly includes the name of the file it couldn't find
        print(f"FATAL ERROR: Certificate or key file not found at '{cert_path}' or '{key_path}'")
        print("Please ensure the Secret volume mount is correct in the Kubernetes deployment.")
        return

    print(f"HTTP/3 server running on https://{host}:{port}")

    await serve(
        host=host,
        port=port,
        configuration=configuration,
        create_protocol=Http3ServerProtocol # Ensure this class is correctly defined/imported
    )

    await asyncio.Future() # run forever

if __name__ == "__main__":
    try:
        # Ensure sys.argv is properly cleaned up before running asyncio.run
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")