import siena.*;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.util.*;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;

public class SienaServer implements Notifiable {
    private ThinClient sienaClient;
    private List<String> activeMatches;

    public static void main(String[] args) {
        try {
            new SienaServer().runServer();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    void connectToDVDServer(String address) {
        // 1. Initialize Siena Connection
        int maxRetries = 10;
        int retryIntervalMs = 2000; // 2 seconds
        boolean connected = false;

        for (int i = 1; i <= maxRetries; i++) {
            try {
                System.err.println("Connecting to Siena (Attempt " + i + "/" + maxRetries + ")...");

                // Attempt to initialize the client
                this.sienaClient = new ThinClient(address);

                // Note: Some clients don't throw an error until you actually try to use them.
                // If ThinClient has a 'ping' or 'get' method, call it here to verify the connection.

                System.err.println("Successfully connected to Siena.");
                connected = true;
                break; 
            } catch (Exception e) {
                System.err.println("Siena not available yet: " + e.getMessage());
                if (i < maxRetries) {
                    try {
                        Thread.sleep(retryIntervalMs);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }
        }

        if (!connected) {
            System.err.println("Failed to connect to Siena after " + maxRetries + " attempts. Exiting.");
            System.exit(1);
        }

    }

    public void runServer() throws Exception {

        connectToDVDServer("tcp:127.0.0.1:1111");
        // 2. Load Subscriptions from JSON file
        loadSubscriptionsFromJson("./testing_data/subscriptions.json");

        // 3. Start HTTP Server
        HttpServer server = HttpServer.create(new InetSocketAddress(8081), 0);
        
        server.createContext("/match", (exchange) -> {
            // Use a synchronized list to collect matches from the async notify threads
            List<String> currentMatches = Collections.synchronizedList(new ArrayList<>());
            
            // We temporarily store the collector in a way the notify method can find it
            // For a single-user test, a simple field works; for concurrency, use a Map or ThreadLocal.
            this.activeMatches = currentMatches;

            try {
                // 1. Read incoming JSON
                InputStream is = exchange.getRequestBody();
                Scanner sc = new Scanner(is).useDelimiter("\\A");
                String eventJson = sc.hasNext() ? sc.next() : "";

                // 2. Parse JSON to Map
                Map<String, Object> eventData = SimpleJson.parseObject(eventJson);

                // 3. Convert Map to Siena Notification
                Notification n = new Notification();
                for (Map.Entry<String, Object> entry : eventData.entrySet()) {
                    Object val = entry.getValue();
                    if (val instanceof Number) {
                        n.putAttribute(entry.getKey(), ((Number) val).doubleValue());
                    } else {
                        n.putAttribute(entry.getKey(), val.toString());
                    }
                }

                // 4. Publish and Wait
                try {
                    sienaClient.publish(n);
                    
                    // Siena is async; wait 500ms for notify() to be called
                    Thread.sleep(500); 

                    // 5. Build Response from collected matches
                    StringBuilder sb = new StringBuilder();
                    sb.append("Matches found: ").append(currentMatches.size()).append("\n");
                    for (String match : currentMatches) {
                        sb.append(" - ").append(match).append("\n");
                    }

                    String response = sb.toString();
                    exchange.sendResponseHeaders(200, response.length());
                    OutputStream os = exchange.getResponseBody();
                    os.write(response.getBytes());
                    os.close();

                    // 6. Print to console AFTER the response is sent
                    //System.out.println("HTTP Response sent. Details:\n" + response);

                } catch (SienaException se) {
                    System.err.println("Siena Publication Error: " + se.getMessage());
                    String errorResponse = "Siena Error: " + se.getMessage();
                    exchange.sendResponseHeaders(500, errorResponse.length());
                    exchange.getResponseBody().write(errorResponse.getBytes());
                    exchange.getResponseBody().close();
                }

            } catch (Exception e) {
                e.printStackTrace();
                exchange.sendResponseHeaders(400, 0);
                exchange.getResponseBody().close();
            } finally {
                this.activeMatches = null; // Clean up the collector
            }
        });

        //System.out.println("HTTP Server started on port 8081. Waiting for events...");
        server.start();
    }

    @SuppressWarnings("unchecked")
    private void loadSubscriptionsFromJson(String path) throws Exception {
        //System.out.println("Loading subscriptions from: " + path);
        String content = new String(Files.readAllBytes(Paths.get(path)));
        Map<String, Object> rootJson = SimpleJson.parseObject(content);
        List<Object> jsonSubs = (List<Object>) rootJson.get("subscriptions");

        for (Object item : jsonSubs) {
            Map<String, Object> subMap = (Map<String, Object>) item;
            String subId = (String) subMap.get("id"); // Get the ID from JSON
            Filter f = new Filter();
            
            List<Object> predicates = (List<Object>) subMap.get("predicates");
            //System.out.println("Registering Subscription: " + subMap.get("id"));

            for (Object pObj : predicates) {
                Map<String, Object> p = (Map<String, Object>) pObj;
                String attr = (String) p.get("attribute");
                String opStr = (String) p.get("operation");
                Object val = p.get("value");

                // Map JSON operations to Siena Ops
                short op = Op.EQ;
                if ("greaterthan".equalsIgnoreCase(opStr)) {
                    op = Op.GT;
                }
                else if ("lessthan".equalsIgnoreCase(opStr)) {
                    op = Op.LT;
                }

                //f.addConstraint("sub_id", Op.EQ, subId);
                if (val instanceof Number) {
                    //System.out.println("'" + attr + "'" + "attribute is seen as a number");
                    f.addConstraint(attr, op, ((Number) val).doubleValue());
                } else {
                    //System.out.println("'" + attr + "'" + "attribute is seen as a string");
                    f.addConstraint(attr, op, val.toString());
                }
            }
            
            // 2. Subscribe ONCE after the filter is fully built
            sienaClient.subscribe(f, new Notifiable() {
                @Override
                public void notify(Notification n) {
                    // Pass the subId from the loop context to our new helper
                    SienaServer.this.notify(n, subId); 
                }
                @Override
                public void notify(Notification[] ns) {
                    for (Notification n : ns) notify(n);
                }
            });
        }
    }

    public void notify(Notification n, String subId) {
        // Format the string to include the ID for the HTTP response
        String matchDetail = "Sub ID: " + subId + " -> " + n.toString();
        
        // Add to the list that the HTTP handler is waiting for
        if (activeMatches != null) {
            activeMatches.add(matchDetail);
        }

        //System.out.println("\n[!] SIENA       MATCH SUCCESS!");
        //System.out.println(matchDetail);     
    }

    // 2. UPDATE THIS EXISTING METHOD to use the helper
    @Override
    public void notify(Notification n) {
        // Redirect to our helper with "Unknown" as a fallback
        notify(n, "Unknown");
    }

    @Override
    public void notify(Notification[] s) {
        for (Notification n : s) notify(n);
    }
}

class SimpleJson {
    public static Map<String, Object> parseObject(String json) {
        json = json.trim();
        if (json.startsWith("{")) json = json.substring(1, json.length() - 1);
        Map<String, Object> map = new LinkedHashMap<>();
        int i = 0;
        while (i < json.length()) {
            i = skipWhitespace(json, i);
            if (i >= json.length()) break;
            
            // Key
            int keyEnd = json.indexOf(":", i);
            String key = json.substring(i, keyEnd).replace("\"", "").trim();
            i = keyEnd + 1;
            
            // Value
            i = skipWhitespace(json, i);
            int valEnd = findValueEnd(json, i);
            String valStr = json.substring(i, valEnd).trim();
            map.put(key, parseValue(valStr));
            
            i = valEnd + 1; // skip comma
        }
        return map;
    }

    private static Object parseValue(String val) {
        val = val.trim();
        if (val.startsWith("{")) return parseObject(val);
        if (val.startsWith("[")) return parseArray(val);
        if (val.startsWith("\"")) return val.substring(1, val.length() - 1);
        if (val.equals("true")) return true;
        if (val.equals("false")) return false;
        try { return Double.parseDouble(val); } catch (Exception e) { return val; }
    }

    private static List<Object> parseArray(String json) {
        json = json.trim().substring(1, json.length() - 1);
        List<Object> list = new ArrayList<>();
        int i = 0;
        while (i < json.length()) {
            i = skipWhitespace(json, i);
            int end = findValueEnd(json, i);
            list.add(parseValue(json.substring(i, end)));
            i = end + 1;
        }
        return list;
    }

    private static int skipWhitespace(String s, int i) {
        while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++;
        return i;
    }

    private static int findValueEnd(String s, int start) {
        int braces = 0, brackets = 0;
        boolean inQuotes = false;
        for (int i = start; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\"') inQuotes = !inQuotes;
            if (!inQuotes) {
                if (c == '{') braces++;
                else if (c == '}') braces--;
                else if (c == '[') brackets++;
                else if (c == ']') brackets--;
                else if (c == ',' && braces == 0 && brackets == 0) return i;
            }
        }
        return s.length();
    }
}