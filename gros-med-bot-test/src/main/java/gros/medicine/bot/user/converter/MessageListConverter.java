package gros.medicine.bot.user.converter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import gros.medicine.bot.assistant_service.Message;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Converter
public class MessageListConverter implements AttributeConverter<List<Message>, String> {
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(List<Message> messages) {
        if (messages == null) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(messages);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Error converting messages to JSON", e);
        }
    }

    @Override
    public List<Message> convertToEntityAttribute(String messagesJson) {
        if (messagesJson == null || messagesJson.isEmpty()) {
            return new ArrayList<>();
        }
        try {
            return objectMapper.readValue(
                    messagesJson,
                    objectMapper.getTypeFactory().constructCollectionType(List.class, Message.class)
            );
        } catch (IOException e) {
            throw new IllegalArgumentException("Error converting JSON to messages", e);
        }
    }
}
