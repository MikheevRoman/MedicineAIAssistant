package gros.medicine.bot.bot_service.controller;

import gros.medicine.bot.bot_service.Bot;
import gros.medicine.bot.bot_service.dto.NewAppointmentDto;
import gros.medicine.bot.bot_service.templates.MessageTemplates;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;

import java.time.format.DateTimeFormatter;

@Slf4j
@Controller
@RequestMapping("/bot")
public class BotController {
    @Autowired
    private Bot bot;
    @Autowired
    private MessageTemplates messageTemplates;

    @PostMapping("/new-appointment")
    public ResponseEntity<String> sendNewAppointmentMessage(@RequestBody final NewAppointmentDto newAppointmentDto) {
        bot.sendMessage(
                newAppointmentDto.getUserId(),
                String.format(
                        messageTemplates.NEW_APPOINTMENT_MESSAGE_TEMPLATE,
                        newAppointmentDto.getSpecialist(),
                        newAppointmentDto.getSpecialisation(),
                        newAppointmentDto.getTime().format(DateTimeFormatter.ofPattern("dd.MM.yyyy в HH:mm")),
                        newAppointmentDto.getInstitutionName(),
                        newAppointmentDto.getInstitutionAddress()
                )
        );
        return new ResponseEntity<>(HttpStatus.OK);
    }
}
