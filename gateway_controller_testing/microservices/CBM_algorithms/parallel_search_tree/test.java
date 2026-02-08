public class test {
    public static void main(String[] args) {
        System.out.println("=== Starting PST Integration Test ===");

        try {
            // 1. Instantiate the PSTBuilder object
            PSTBuilder builder = new PSTBuilder();

            // 3. Verify the static root was set
            if (PSTBuilder.PSTroot != null) {
                System.out.println("Step 2: Tree built successfully.");
            } else {
                System.err.println("Error: PSTroot is null!");
                return;
            }

            // 4. Run the matching engine against events.json
            System.out.println("Step 3: Running matching engine...");
            builder.matchEvents();

            System.out.println("=== Test Completed Successfully ===");

        } catch (Exception e) {
            System.err.println("Test Failed with Exception:");
            e.printStackTrace();
        }
    }
}