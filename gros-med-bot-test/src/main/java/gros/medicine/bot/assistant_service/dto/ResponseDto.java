package gros.medicine.bot.assistant_service.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@JsonIgnoreProperties(ignoreUnknown = true)
@Getter @Setter
@AllArgsConstructor
@NoArgsConstructor
public class ResponseDto {
    @JsonProperty("conversation_state")
    private ConversationState conversationState;

    @JsonProperty("response")
    private String response;
}

