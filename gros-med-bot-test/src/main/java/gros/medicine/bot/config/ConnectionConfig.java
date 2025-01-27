package gros.medicine.bot.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
@PropertySource("application.properties")
public class ConnectionConfig {
    @Value("${ai.service.connection.url}")
    private String aiServiceConnectionUrl;

    @Bean
    public WebClient aiServiceApiClient() {
        return WebClient.create(aiServiceConnectionUrl);
    }
}
