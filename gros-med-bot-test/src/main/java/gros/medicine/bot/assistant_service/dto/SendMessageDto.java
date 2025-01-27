package gros.medicine.bot.assistant_service.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import gros.medicine.bot.assistant_service.Message;
import lombok.*;
import lombok.experimental.FieldDefaults;

import java.util.List;

@Getter @Setter
@Builder
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class SendMessageDto {
    @JsonProperty("prompt")
    List<Message> prompt;

    @JsonProperty("user_id")
    Long userId;

    @JsonProperty("is_start_dialog")
    Boolean isStartDialog;
}
