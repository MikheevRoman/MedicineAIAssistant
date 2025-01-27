package gros.medicine.bot.assistant_service.service;

import gros.medicine.bot.assistant_service.dto.SendImageDto;
import gros.medicine.bot.assistant_service.dto.SendMessageDto;
import gros.medicine.bot.assistant_service.dto.ResponseDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

@Service
@Slf4j
public class AssistantServiceImpl implements AssistantService {
    @Autowired
    @Qualifier(value = "aiServiceApiClient")
    private WebClient serviceClient;

    @Override
    public ResponseDto sendMessage(SendMessageDto sendMessageDto) {
        try {
            ResponseEntity<ResponseDto> responseEntity = serviceClient
                    .post()
                    .uri("/check-uc-sync")
                    .header("Content-Type", "application/json")
                    .accept(MediaType.APPLICATION_JSON)
                    .bodyValue(sendMessageDto)
                    .retrieve()
                    .toEntity(ResponseDto.class)
                    .block();

            assert responseEntity != null;
            if (responseEntity.getStatusCode() == HttpStatus.OK) {
                return responseEntity.getBody();
            } else {
                log.error("unexpected HTTP status code = " + responseEntity.getStatusCode());
                return null;
            }
        } catch (WebClientResponseException e) {
            log.error("WebClientResponseException occurred: {}", e.getMessage());
            e.printStackTrace();
            return null;
        } catch (Exception e) {
            log.error("Error occurred: {}", e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    @Override
    public ResponseDto sendImage(SendImageDto sendMessageDto) {
        try {
            ResponseEntity<ResponseDto> responseEntity = serviceClient
                    .post()
                    .uri("/check-uc-sync-image")
                    .header("Content-Type", "application/json")
                    .accept(MediaType.APPLICATION_JSON)
                    .bodyValue(sendMessageDto)
                    .retrieve()
                    .toEntity(ResponseDto.class)
                    .block();

            assert responseEntity != null;
            if (responseEntity.getStatusCode() == HttpStatus.OK) {
                return responseEntity.getBody();
            } else {
                log.error("unexpected HTTP status code = " + responseEntity.getStatusCode());
                return null;
            }
        } catch (WebClientResponseException e) {
            log.error("WebClientResponseException occurred: {}", e.getMessage());
            e.printStackTrace();
            return null;
        } catch (Exception e) {
            log.error("Error occurred: {}", e.getMessage());
            e.printStackTrace();
            return null;
        }
    }
}
