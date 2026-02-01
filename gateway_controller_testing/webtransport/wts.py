import asyncio
from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived
from aioquic.quic.configuration import QuicConfiguration

class WebTransportServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h3 = H3Connection(self._quic)

    def quic_event_received(self, event):
        for http_event in self._h3.handle_event(event):
            if isinstance(http_event, HeadersReceived):
                headers = dict(http_event.headers)
                # Check for WebTransport CONNECT
                if headers.get(b":method") == b"CONNECT" and headers.get(b":protocol") == b"webtransport":
                    print("✅ WebTransport handshake received!")
                    self._h3.send_headers(
                        stream_id=http_event.stream_id,
                        headers=[
                            (b":status", b"200"),
                            (b"sec-webtransport-http3-draft", b"draft02"),
                        ],
                    )
                else:
                    self._h3.send_headers(
                        stream_id=http_event.stream_id,
                        headers=[(b":status", b"404")],
                    )
            
            elif isinstance(http_event, DataReceived):
                print(f"📥 Received data: {http_event.data.decode()}")
                # Echo data back
                self._h3.send_data(http_event.stream_id, b"Echo: " + http_event.data, end_stream=False)
        self.transmit()

async def main():
    configuration = QuicConfiguration(is_client=False, alpn_protocols=H3_ALPN)
    # Use your existing certs here
    configuration.load_cert_chain("..\certs\www.example.com.crt", "..\certs\www.example.com.key")
    
    print("🚀 WebTransport Server running on port 3000...")
    await serve(
        "0.0.0.0", 3000, configuration=configuration, create_protocol=WebTransportServerProtocol
    )
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())