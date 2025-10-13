async function testHttp3() {
    try {
        // Create a WebTransport session to the HTTP/3 server
        const transport = new WebTransport("https://127.0.0.1:4433/");

        // Wait until the connection is ready
        await transport.ready;
        console.log("Connected via HTTP/3 / QUIC!");

        // Open a bidirectional stream
        const stream = await transport.createBidirectionalStream();
        const writer = stream.writable.getWriter();
        const reader = stream.readable.getReader();

        // Send a GET request (HTTP/3 style)
        await writer.write(new TextEncoder().encode("GET / HTTP/3\r\n\r\n"));
        writer.close();

        // Read response
        const { value, done } = await reader.read();
        if (value) {
            console.log("Response:", new TextDecoder().decode(value));
        }

        transport.close();
    } catch (err) {
        console.error("HTTP/3 request failed:", err);
    }
}

testHttp3();
