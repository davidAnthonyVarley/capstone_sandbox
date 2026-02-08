@RestController
public class ProducerController {

    @Autowired
    private RabbitTemplate rabbitTemplate;

    @PostMapping("/match")
    public ResponseEntity<?> matchEvent(@RequestBody Map<String, Object> event) {
        // convertSendAndReceive handles:
        // 1. Creating a correlationId
        // 2. Setting the 'replyTo' header to 'amq.rabbitmq.reply-to'
        // 3. Blocking the HTTP thread until the worker responds
        Object response = rabbitTemplate.convertSendAndReceive(
            "pst_exchange", 
            "pst.matching.key", // Ensure this matches your worker's binding
            event
        );

        if (response == null) {
            // If the worker is down or the algorithm is too slow (> 5s)
            return ResponseEntity.status(504).body("Timeout: No worker responded in time.");
        }

        return ResponseEntity.ok(response);
    }
}