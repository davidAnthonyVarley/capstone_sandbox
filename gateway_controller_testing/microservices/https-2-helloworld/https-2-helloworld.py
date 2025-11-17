import asyncio
import ssl
import os
# --- CORRECTED H2 IMPORTS ---
from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.events import RequestReceived, DataReceived, WindowUpdated
from h2.exceptions import ProtocolError
# -------------------------
import sys
import argparse


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

# Define parameters for local development
#HOST = 'localhost'
#PORT = 30443 

#project_root = "C:\\Users\\david\\capstone_sandbox\\gateway_controller_testing"
#certs_folder = os.path.join(project_root, "certs")
#KEYFILE = os.path.join(certs_folder, 'key.pem')
#CERTFILE = os.path.join(certs_folder, 'cert.pem')

#for k8s cluster
HOST = '0.0.0.0'
PORT = 30002 
args = parse_arguments()
CERTFILE = args.cert
KEYFILE = args.key

print(f"Key File Path: {KEYFILE}")
print(f"Cert File Path: {CERTFILE}")

# --- 1. Define the Protocol Handler ---
class H2Protocol(asyncio.Protocol):
    """
    Handles a single TLS/TCP connection and manages the H2 state machine.
    """
    def __init__(self, loop):
        self.loop = loop
        self.config = H2Configuration(client_side=False)
        self.conn = H2Connection(config=self.config)
        self.transport = None

    def connection_made(self, transport):
        """Called when a new TLS connection is established."""
        self.transport = transport
        self.conn.initiate_connection()
        self.transport.write(self.conn.data_to_send())

    def data_received(self, data):
        """Called when new data arrives from the socket."""
        try:
            events = self.conn.receive_data(data)
        except ProtocolError: 
            self.transport.close()
            return

        for event in events:
            if isinstance(event, RequestReceived): 
                self.handle_request(event.stream_id, event.headers)
            elif isinstance(event, DataReceived):
                pass
            elif isinstance(event, WindowUpdated):
                pass

        self.transport.write(self.conn.data_to_send())

    def handle_request(self, stream_id, headers):
        """Processes a single incoming HTTP/2 request (stream)."""
        path = [v for n, v in headers if n == b':path'][0].decode()
        
        print(f"[{stream_id}] Request received for: {path}")

        # Send Response Headers
        response_headers = [
            (':status', '200'),
            ('content-type', 'text/plain'),
            ('server', 'h2-python-server'),
        ]
        self.conn.send_headers(stream_id, response_headers)

        # Send Response Body
        body = f"Hello world from Python HTTP/2 Server! You requested {path}"
        self.conn.send_data(
            stream_id=stream_id,
            data=body.encode('utf-8'),
            end_stream=True
        )

        self.transport.write(self.conn.data_to_send())

    def connection_lost(self, exc):
        print("Connection lost.")
        
# --- 2. Main Server Setup ---
async def main():
    # 2.1 Configure SSL Context for TLS
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    
    # Load certificates from the new file paths
    ssl_ctx.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
    
    # Crucially, set the ALPN to negotiate 'h2' protocol
    ssl_ctx.set_alpn_protocols(['h2'])

    # 2.2 Start the Server
    server = await asyncio.get_running_loop().create_server(
        lambda: H2Protocol(asyncio.get_running_loop()),
        HOST,
        PORT,
        ssl=ssl_ctx
    )
    
    print(f"🚀 Serving HTTPS on https://{HOST}:{PORT}/")

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except FileNotFoundError:
        print("\n!!! ERROR: TLS key.pem or cert.pem not found. !!!")
        print(f"Please verify the files exist in the path: {certs_folder}")
    except Exception as e:
        print(f"Server initialization error: {e}")