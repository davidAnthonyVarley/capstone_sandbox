import asyncio
import ssl
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived
from aioquic.quic.events import QuicEvent

class WebTransportClient:
    def __init__(self, quic_connection):
        self.quic = quic_connection
        self.h3 = H3Connection(quic_connection)
        self.session_established = asyncio.Event()

    def quic_event_received(self, event: QuicEvent):
        for http_event in self.h3.handle_event(event):
            if isinstance(http_event, HeadersReceived):
                headers = {k.decode(): v.decode() for k, v in http_event.headers}
                print(f"📥 Received Headers: {headers}")
                
                # Check for successful WebTransport negotiation
                if headers.get(":status") == "200":
                    print("✅ WebTransport session established successfully!")
                    self.session_established.set()
                else:
                    print(f"❌ Failed to establish session. Status: {headers.get(':status')}")

            elif isinstance(http_event, DataReceived):
                print(f"📥 Data from server: {http_event.data.decode(errors='ignore')}")

    def establish_session(self, authority, path):
        stream_id = self.quic.get_next_available_stream_id(is_unidirectional=False)
        print(f"🚀 Sending WebTransport CONNECT on stream {stream_id}...")
        
        # WebTransport requires these specific pseudo-headers
        self.h3.send_headers(
            stream_id=stream_id,
            headers=[
                (b":method", b"CONNECT"),
                (b":protocol", b"webtransport"),  # This triggers WebTransport mode
                (b":scheme", b"https"),
                (b":authority", authority.encode()),
                (b":path", path.encode()),
            ]
        )
        # We do NOT end the stream; WebTransport stays open for data
        self.quic.transmit()
        return stream_id

    async def send_data(self, stream_id, message):
        print(f"📤 Sending: {message}")
        self.h3.send_data(stream_id, message.encode(), end_stream=False)
        self.quic.transmit()

async def run_wt_test(ip, port, host, path):
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        verify_mode=ssl.CERT_NONE,  # Equivalent to -k for your self-signed certs
        server_name=host
    )

    async with connect(ip, port, configuration=configuration) as protocol:
        client = WebTransportClient(protocol._quic)
        protocol.quic_event_received = client.quic_event_received

        # Start the handshake
        sid = client.establish_session(host, path)
        
        # Wait for the server to confirm with a 200 OK
        try:
            await asyncio.wait_for(client.session_established.wait(), timeout=5.0)
            
            # Example: Send a test message over the open session
            await client.send_data(sid, "Hello via WebTransport!")
            
            # Keep the connection alive for a few seconds to receive data
            await asyncio.sleep(5)
            
        except asyncio.TimeoutError:
            print("🕒 Timeout: Server did not respond to WebTransport CONNECT.")

if __name__ == "__main__":
    # Update these to match your Gateway IP, Port, and Hostname
    GATEWAY_IP = "192.168.59.109"
    GATEWAY_PORT = 30856
    TARGET_HOST = "www.example.com"
    TARGET_PATH = "/get"

    asyncio.run(run_wt_test(GATEWAY_IP, GATEWAY_PORT, TARGET_HOST, TARGET_PATH))
