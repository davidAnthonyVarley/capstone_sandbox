import asyncio
import ssl
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived
from aioquic.quic.events import StreamDataReceived, QuicEvent # Import QuicEvent

# --- Client Implementation Class ---
# This class will handle the HTTP/3 layer on top of QUIC
class H3ClientProtocol:
    def __init__(self, quic_connection):
        self.quic = quic_connection
        self.h3 = H3Connection(quic_connection)
        self.response_complete = asyncio.Event()

    # This method is what the AioQuicConnectionProtocol calls when it gets a QUIC event
    # This method is what the AioQuicConnectionProtocol calls when it gets a QUIC event
    def quic_event_received(self, event: QuicEvent):
        # Pass the QUIC event to the H3 layer and iterate over the yielded HTTP/3 events
        for http_event in self.h3.handle_event(event): # CORRECTED LINE: iterate over results of handle_event
            if isinstance(http_event, HeadersReceived):
                print("Headers:", [(k.decode(), v.decode()) for k, v in http_event.headers])
            elif isinstance(http_event, DataReceived):
                print("Body:", http_event.data.decode(errors='ignore'))
                if http_event.stream_ended:
                    self.response_complete.set()
    
    # Method to send the request
    def send_request(self):
        # allocate stream
        print("allocating stream")
        stream_id = self.quic.get_next_available_stream_id(is_unidirectional=False)

        # send GET request
        print("sending get request")
        self.h3.send_headers(
            stream_id=stream_id,
            headers=[
                (b":method", b"GET"),
                (b":scheme", b"https"),
                (b":authority", b"hello-app.local"),
                (b":path", b"/"),
            ]
        )
        # Send an empty body and close the stream
        self.h3.send_data(stream_id, b"", end_stream=True)
        # H3 data needs to be flushed by the QUIC connection
        #self.quic.transmit() 
        # Note: In aioquic.asyncio.connect, the transport loop 
        # should handle sending packets automatically once quic.transmit() is called.


# --- Main Fetch Function ---
async def fetch(ip, port):
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        verify_mode=ssl.CERT_NONE
    )

    print(f"before trying to connect to server at {ip}:{port}")
    
    # Everything inside this 'async with' block must be indented (4 spaces)
    async with connect(ip, port, configuration=configuration) as protocol:
        
        # 1. Instantiate the H3 client with the QUIC connection
        client = H3ClientProtocol(protocol._quic)

        # 2. Override the protocol's event handler
        protocol.quic_event_received = client.quic_event_received

        # 3. Send the request
        client.send_request()
        
        # --- THE FIX ---
        # Explicitly transmit the buffered data to the network
        protocol.transmit()
        # ----------------

        # 4. Wait for the response to complete
        await client.response_complete.wait()
#asyncio.run(fetch("127.0.0.1",65297))
#http://127.0.0.1:63813/
#http://127.0.0.1:49701/
#asyncio.run(fetch("localhost", 30003))
#asyncio.run(fetch("192.168.49.2", 30003))
#asyncio.run(fetch("192.168.59.107", 10433))
asyncio.run(fetch("192.168.59.107", 30856))
#asyncio.run(fetch("127.0.0.1", 10433))