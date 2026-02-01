// No imports needed for Node 22+ with the experimental flag
const CERT_HASH = 'ToGnMyQSwBaCDMrD+FUaHDNl0/8LmrDJmZCgEWC1Hg0=';

async function run() {
  const url = 'https://192.168.59.109:30856/get';
  
  console.log(`🚀 Connecting to ${url}...`);

  try {
    // Check if the flag worked
    if (typeof WebTransport === 'undefined') {
        throw new Error("WebTransport is undefined. You MUST run node with the --experimental-quic flag.");
    }

    const transport = new WebTransport(url, {
      serverCertificateHashes: [
        {
          algorithm: 'sha-256',
          // Convert base64 hash to Uint8Array
          value: Uint8Array.from(Buffer.from(CERT_HASH, 'base64'))
        }
      ]
    });

    // Wait for the connection to open
    await transport.ready;
    console.log('✅ WebTransport is ready!');

    // Create a bidirectional stream
    const stream = await transport.createBidirectionalStream();
    const writer = stream.writable.getWriter();
    const reader = stream.readable.getReader();

    // Send some data
    const data = new TextEncoder().encode('Hello Gateway!');
    await writer.write(data);
    console.log('📤 Data sent to server');

    // Read the response
    const { value } = await reader.read();
    if (value) {
      console.log('📥 Received:', new TextDecoder().decode(value));
    }

    // Close down gracefully
    await writer.close();
    transport.close();
    console.log('🏁 Connection closed.');

  } catch (err) {
    console.error('❌ WebTransport Error:', err);
    process.exit(1);
  }
}

run();