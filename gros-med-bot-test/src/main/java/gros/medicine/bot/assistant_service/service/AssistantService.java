package gros.medicine.bot.assistant_service.service;

import gros.medicine.bot.assistant_service.dto.SendImageDto;
import gros.medicine.bot.assistant_service.dto.SendMessageDto;
import gros.medicine.bot.assistant_service.dto.ResponseDto;

public interface AssistantService {
    ResponseDto sendMessage(SendMessageDto sendMessageDto);

    ResponseDto sendImage(SendImageDto sendMessageDto);
}
