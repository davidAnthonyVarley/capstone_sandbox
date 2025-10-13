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
        stream_id = self.quic.get_next_available_stream_id(is_unidirectional=False)

        # send GET request
        self.h3.send_headers(
            stream_id=stream_id,
            headers=[
                (b":method", b"GET"),
                (b":scheme", b"https"),
                (b":authority", b"localhost"),
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
async def fetch():
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        verify_mode=ssl.CERT_NONE
    )

    # 'connect' returns an AioQuicConnectionProtocol instance
    async with connect("127.0.0.1", 4433, configuration=configuration) as protocol:
        
        # 1. Instantiate the H3 client with the QUIC connection
        client = H3ClientProtocol(protocol._quic)

        # 2. **Override the protocol's event handler** to direct events to your H3 client
        # When the AioQuicConnectionProtocol receives a QUIC event, it now calls your handler.
        protocol.quic_event_received = client.quic_event_received

        # 3. Send the request
        client.send_request()

        # 4. Wait for the response to complete
        await client.response_complete.wait()
        
        # The 'async with' block will automatically close the connection upon exit

asyncio.run(fetch())