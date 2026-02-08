import java.util.*;




interface Node {
    void match(Map<String, Object> event, Set<String> results);
}

class Constraint {
    String attr;
    Object val;
    boolean isRange; // true if it's a "greater than" test

    Constraint(String attr, Object val, boolean isRange) {
        this.attr = attr; this.val = val; this.isRange = isRange;
    }
}

class Subscription {
    String id;
    List<Constraint> constraints = new ArrayList<>();

    Subscription(String id) { this.id = id; }
    void add(String attr, Object val) { constraints.add(new Constraint(attr, val, false)); }
    void addRange(String attr, double val) { constraints.add(new Constraint(attr, val, true)); }
}

class PSTCompiler {
    public static Node buildTree(List<Subscription> subs) {
        Node root = null;
        for (Subscription sub : subs) {
            // Weave each subscription into the current root's STAR path
            root = weaveSubscription(sub, root);
        }
        return root;
    }

    private static Node weaveSubscription(Subscription sub, Node currentTree) {
        // Create the leaf for this specific subscriber
        Node leaf = new LeafNode(sub.id);
        
        // Build the AND chain for the constraints (backwards)
        Node chain = leaf;
        for (int i = sub.constraints.size() - 1; i >= 0; i--) {
            Constraint c = sub.constraints.get(i);
            
            // The very first node in the chain gets the "currentTree" in its STAR path
            // This ensures the rest of the waterfall is preserved.
            Node starPath = (i == 0) ? currentTree : null;

            if (c.isRange) {
                chain = new RangePSTNode(c.attr, (double)c.val, chain, null, starPath);
            } else {
                chain = new PSTNode(c.attr, c.val, chain, null, starPath);
            }
        }
        return chain;
    }
}

class PSTNode implements Node {
    String attribute;
    Object targetValue; // PST usually compares against a specific constant

    Node ifMatch;    // Successor if event[attr] == targetValue
    Node ifNoMatch;  // Successor if event[attr] != targetValue
    Node star;       // ALWAYS follow this (Don't Care path)

    public void match(Map<String, Object> event, Set<String> results) {
        // --- THE PARALLEL STEP ---
        // In a PST, we always explore the Star branch because it contains 
        // subscriptions that don't care about the current 'attribute'.
        if (star != null) {
            star.match(event, results);
        }

        // --- THE CONDITIONAL STEP ---
        if (event.containsKey(attribute)) {
            Object val = event.get(attribute);
            if (val.equals(targetValue)) {
                if (ifMatch != null) ifMatch.match(event, results);
            } else {
                if (ifNoMatch != null) ifNoMatch.match(event, results);
            }
        }
    }

    public PSTNode(String attribute, Object targetValue, Node ifMatch, Node ifNoMatch, Node star) {
        this.attribute = attribute;
        this.targetValue = targetValue;
        this.ifMatch = ifMatch;
        this.ifNoMatch = ifNoMatch;
        this.star = star;
    }
}

class LeafNode implements Node {
    private String subscriptionId;

    public LeafNode(String id) { this.subscriptionId = id; }

    @Override
    public void match(Map<String, Object> event, Set<String> results) {
        results.add(subscriptionId); // This is where the match is recorded
    }
}

class CollectionNode implements Node {
    private List<Node> children = new ArrayList<>();
    
    public void addChild(Node n) { children.add(n); }

    @Override
    public void match(Map<String, Object> event, Set<String> results) {
        for (Node child : children) {
            child.match(event, results);
        }
    }
}

class RangePSTNode implements Node {
    String attribute;
    double threshold;
    Node ifGreater;
    Node ifLessEqual;
    Node star; // The "Parallel" Don't-Care path

    public RangePSTNode(String attr, double threshold, Node gt, Node le, Node star) {
        this.attribute = attr;
        this.threshold = threshold;
        this.ifGreater = gt;
        this.ifLessEqual = le;
        this.star = star;
    }

    @Override
    public void match(Map<String, Object> event, Set<String> results) {
        // 1. Parallel Step: Always check filters that don't care about this attribute
        if (star != null) star.match(event, results);

        // 2. Conditional Step: Check filters that DO care about this attribute
        if (event.containsKey(attribute)) {
            Object val = event.get(attribute);
            if (val instanceof Number num) {
                if (num.doubleValue() > threshold) {
                    if (ifGreater != null) ifGreater.match(event, results);
                } else {
                    if (ifLessEqual != null) ifLessEqual.match(event, results);
                }
            }
        }
    }
}

public class PSTBuilder {
    public static void main(String[] args) {
        List<Subscription> subs = new ArrayList<>();

        // Add 100 simple subscriptions dynamically
        for (int i = 1; i <= 20; i++) {
            Subscription s = new Subscription("Sub_" + i);
            s.add("attribute_" + i, "value_" + i);
            subs.add(s);
        }

        // Add specific complex subscriptions
        Subscription complex = new Subscription("Complex_01");
        complex.addRange("price", 500.0);
        complex.add("category", "hardware");
        subs.add(complex);

        Subscription s_triple = new Subscription("Triple_Match_Sub");
        s_triple.add("location", "NewYork");   // Predicate 1
        s_triple.addRange("severity", 5.0);    // Predicate 2
        s_triple.add("status", "active");      // Predicate 3
        subs.add(s_triple);

        Subscription s_weather = new Subscription("Weather_Sub");
        s_weather.add("type", "rain");
        subs.add(s_weather);

        // Subscription B cares about stock prices
        Subscription s_stock = new Subscription("Stock_Sub");
        s_stock.addRange("price", 150.0);
        subs.add(s_stock);

        Node root = PSTCompiler.buildTree(subs);

        Map<String, Object> event = new HashMap<>();
        event.put("attribute_5", "value_5");
        event.put("price", 600.0);
        event.put("category", "hardware");

        event.put("location", "NewYork");
        event.put("severity", 10.0);
        event.put("status", "active");

        event.put("type", "rain");

        Set<String> results = new HashSet<>();
        if (root != null) root.match(event, results);

        System.out.println("Matched: " + results);
    }
}
