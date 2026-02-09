import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.util.*;
import java.io.*;

public class Server {
    // Fixed: Removed double 'public'
    public void startServer() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        
        // This triggers PSTBuilder's constructor, which calls loadSubscriptions()
        PSTBuilder builder = new PSTBuilder();

        server.createContext("/match", (exchange) -> {
            // 1. Read the incoming JSON event
            InputStream is = exchange.getRequestBody();
            Scanner s = new Scanner(is).useDelimiter("\\A");
            String eventJson = s.hasNext() ? s.next() : "";

            // 2. Parse using the helper in PSTBuilder.java
            Map<String, Object> eventData = SimpleJson.parseObject(eventJson);

            // 3. Match against the static PSTroot
            Set<String> results = new HashSet<>();
            if (PSTBuilder.PSTroot != null) {
                PSTBuilder.PSTroot.match(eventData, results);
            }

            List<String> resultList = new ArrayList<>(results);

            // 4. Build the JSON Response manually to match the requested schema
            StringBuilder sb = new StringBuilder();
            sb.append("{\n");
            sb.append("  \"match_count\": ").append(resultList.size()).append(",\n");
            sb.append("  \"subscriber_ids\": [");

            for (int i = 0; i < resultList.size(); i++) {
                sb.append("\"").append(resultList.get(i)).append("\"");
                if (i < resultList.size() - 1) {
                    sb.append(", ");
                }
            }
            sb.append("]\n");
            sb.append("}");
            // --- FIX END ---

            String response = sb.toString();

            // Set Content-Type to application/json so Go recognizes it correctly
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.getBytes().length);
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        });

        System.out.println("Server started on port 8080. Use /match to test events.");
        server.start();
    }

    public static void main(String args[]) {
        try {
            // Fixed: Create instance to call non-static method
            new Server().startServer();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}