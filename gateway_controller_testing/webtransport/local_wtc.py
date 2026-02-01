import asyncio
import ssl
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived

class WebTransportClient:
    def __init__(self, quic_connection):
        self.quic = quic_connection
        self.h3 = H3Connection(quic_connection)
        self.session_established = asyncio.Event()

    def quic_event_received(self, event):
        for http_event in self.h3.handle_event(event):
            if isinstance(http_event, HeadersReceived):
                headers = {k.decode(): v.decode() for k, v in http_event.headers}
                print(f"📥 Received Headers: {headers}")
                if headers.get(":status") == "200":
                    print("✅ Connection Success: WebTransport Active!")
                    self.session_established.set()
            elif isinstance(http_event, DataReceived):
                print(f"🔄 Echo from Server: {http_event.data.decode()}")

    def establish_session(self, authority, path):
        stream_id = self.quic.get_next_available_stream_id()
        headers = [
            (b":method", b"CONNECT"),
            (b":protocol", b"webtransport"),
            (b":scheme", b"https"),
            (b":authority", authority.encode()),
            (b":path", path.encode()),
        ]
        self.h3.send_headers(stream_id, headers)
        return stream_id

async def run_wt_test(ip, port, host, path):
    print(f"📡 Attempting to connect to {ip}:{port}...")
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        verify_mode=ssl.CERT_NONE,
        server_name=host
    )

    async with connect(ip, port, configuration=configuration) as protocol:
        print("🔗 QUIC Connection established!")
        client = WebTransportClient(protocol._quic)
        
        # This links the network events to our client logic
        protocol.quic_event_received = client.quic_event_received

        print("🚀 Sending WebTransport CONNECT...")
        sid = client.establish_session(host, path)
        protocol.transmit()

        try:
            print("⏳ Waiting for server response...")
            await asyncio.wait_for(client.session_established.wait(), timeout=5.0)
            
            print("📤 Sending: 'Hello Local Server!'")
            client.h3.send_data(sid, b"Hello Local Server!", end_stream=False)
            protocol.transmit()
            
            # Keep alive to see the echo back
            await asyncio.sleep(2)
        except asyncio.TimeoutError:
            print("🕒 Timeout: Server did not respond to CONNECT.")

if __name__ == "__main__":
    # Test against your local wts.py
    asyncio.run(run_wt_test("127.0.0.1", 3000, "www.example.com", "/get"))