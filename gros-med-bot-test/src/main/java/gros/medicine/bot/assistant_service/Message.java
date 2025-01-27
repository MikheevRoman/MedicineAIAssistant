package gros.medicine.bot.assistant_service;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import lombok.experimental.FieldDefaults;

@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class Message {
    @JsonProperty("role")
    Role role;

    @JsonProperty("content")
    String content;
}
