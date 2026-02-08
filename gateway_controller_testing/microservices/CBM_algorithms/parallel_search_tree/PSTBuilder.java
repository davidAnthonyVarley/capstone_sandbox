import java.util.*;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;

public class PSTBuilder {

    static Node PSTroot;

    public void matchEvents() throws Exception {
                // 1. Read the events file
        String eventContent = new String(Files.readAllBytes(Paths.get("..\\testing_data\\events.json")));
        Map<String, Object> events = SimpleJson.parseObject(eventContent);

        // 2. Iterate through each event and match it
        for (String eventId : events.keySet()) {
            Map<String, Object> eventData = (Map<String, Object>) events.get(eventId);
            System.out.println("--- Processing Event: " + eventId + " ---");
            matchEventToSubscriptions(eventData);
        }
    }

    public void matchEventToSubscriptions(Map<String, Object> eventData) {
            Set<String> results = new HashSet<>();

            // START TIMING
            long startTime = System.nanoTime();

            if (PSTroot != null) PSTroot.match(eventData, results);

            // END TIMING
            long endTime = System.nanoTime();
            long duration = (endTime - startTime); // duration in nanoseconds

            System.out.println("Matched Subs: " + results);
            System.out.println("Processing Time: " + duration + " ns");
    }

    public static void loadSubscriptions() {
        List<Subscription> subs = new ArrayList<>();

        try {
            // 1. Read the JSON file
            String content = new String(Files.readAllBytes(Paths.get("..\\testing_data\\subscriptions.json")));
            
            // 2. Parse using the built-in helper
            Map<String, Object> rootJson = SimpleJson.parseObject(content);
            List<Object> jsonSubs = (List<Object>) rootJson.get("subscriptions");

            // 3. Convert JSON maps into Subscription objects
            for (Object item : jsonSubs) {
                Map<String, Object> subMap = (Map<String, Object>) item;
                Subscription s = new Subscription((String) subMap.get("id"));

                List<Object> predicates = (List<Object>) subMap.get("predicates");
                for (Object pObj : predicates) {
                    Map<String, Object> p = (Map<String, Object>) pObj;
                    String attr = (String) p.get("attribute");
                    String op = (String) p.get("operation");
                    Object val = p.get("value");

                    if ("greaterthan".equalsIgnoreCase(op)) {
                        s.addRange(attr, Double.parseDouble(val.toString()));
                    } else {
                        s.add(attr, val);
                    }
                }
                subs.add(s);
            }

            // 4. Build and Match
            PSTBuilder.PSTroot = PSTCompiler.buildTree(subs);

        } catch (Exception e) {
            System.err.println("JSON Error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public PSTBuilder() {
        loadSubscriptions();

    }
}

/**
 * A minimal, zero-dependency JSON parser for the Capstone Sandbox environment.
 */
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