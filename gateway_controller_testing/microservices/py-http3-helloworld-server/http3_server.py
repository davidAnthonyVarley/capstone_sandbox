import asyncio
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

async def main():
    # It's important to use a good certificate and private key here
    # Use your existing paths if they are valid
    configuration = QuicConfiguration(
        is_client=False,
        # Use a list of protocols for better compatibility
        alpn_protocols=H3_ALPN_LIST, 
    )
    
    # NOTE: You MUST replace these with valid paths to your certificate and key
    # Ensure 'certs/pk_cert.pem' and 'certs/private_key.pem' exist and are correct
    try:
        configuration.load_cert_chain("certs/pk_cert.pem", "certs/private_key.pem")
    except FileNotFoundError as e:
        print(f"FATAL ERROR: Certificate or key file not found: {e.filename}")
        print("Please ensure you have a valid certificate chain for the server.")
        return

    print("HTTP/3 server running on https://127.0.0.1:4433")

    await serve(
        host="127.0.0.1",
        port=4433,
        configuration=configuration,
        create_protocol=Http3ServerProtocol
    )

    await asyncio.Future() # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")