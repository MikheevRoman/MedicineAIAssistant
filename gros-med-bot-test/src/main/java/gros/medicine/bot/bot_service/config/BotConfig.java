package gros.medicine.bot.bot_service.config;

import lombok.Getter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;

@Getter
@Configuration
@PropertySource("application.properties")
public class BotConfig {
    @Value("${bot.token}")
    private String botToken;
}
