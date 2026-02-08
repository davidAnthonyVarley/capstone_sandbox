import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitConfig {

    // This must match the exchange name used in your controller
    @Bean
    public TopicExchange pstExchange() {
        return new TopicExchange("pst_exchange");
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        
        // IMPORTANT: This enables the "Direct Reply-To" feature automatically
        // and sets how long the Producer waits for the Worker to finish the PST match.
        template.setReplyTimeout(5000); // 5 seconds
        
        return template;
    }
}
