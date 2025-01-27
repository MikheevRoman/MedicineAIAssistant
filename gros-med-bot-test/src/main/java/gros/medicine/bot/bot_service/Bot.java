package gros.medicine.bot.bot_service;

import gros.medicine.bot.assistant_service.Message;
import gros.medicine.bot.assistant_service.Role;
import gros.medicine.bot.assistant_service.dto.SendImageDto;
import gros.medicine.bot.assistant_service.dto.SendMessageDto;
import gros.medicine.bot.assistant_service.dto.ResponseDto;
import gros.medicine.bot.assistant_service.service.AssistantServiceImpl;
import gros.medicine.bot.bot_service.config.BotConfig;
import gros.medicine.bot.bot_service.templates.MessageTemplates;
import gros.medicine.bot.user.entity.User;
import gros.medicine.bot.user.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.telegram.telegrambots.client.okhttp.OkHttpTelegramClient;
import org.telegram.telegrambots.longpolling.BotSession;
import org.telegram.telegrambots.longpolling.interfaces.LongPollingUpdateConsumer;
import org.telegram.telegrambots.longpolling.starter.AfterBotRegistration;
import org.telegram.telegrambots.longpolling.starter.SpringLongPollingBot;
import org.telegram.telegrambots.longpolling.util.LongPollingSingleThreadUpdateConsumer;
import org.telegram.telegrambots.meta.api.methods.GetFile;
import org.telegram.telegrambots.meta.api.methods.ParseMode;
import org.telegram.telegrambots.meta.api.methods.send.SendMessage;
import org.telegram.telegrambots.meta.api.objects.File;
import org.telegram.telegrambots.meta.api.objects.PhotoSize;
import org.telegram.telegrambots.meta.api.objects.Update;
import org.telegram.telegrambots.meta.api.objects.replykeyboard.ReplyKeyboardMarkup;
import org.telegram.telegrambots.meta.api.objects.replykeyboard.buttons.KeyboardButton;
import org.telegram.telegrambots.meta.api.objects.replykeyboard.buttons.KeyboardRow;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;
import org.telegram.telegrambots.meta.generics.TelegramClient;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.List;

import static gros.medicine.bot.bot_service.Commands.NEW_CONVERSATION;
import static gros.medicine.bot.bot_service.Commands.START;

@Component
@Slf4j
public class Bot implements SpringLongPollingBot, LongPollingSingleThreadUpdateConsumer {
    @Autowired
    private MessageTemplates messageTemplates;

    @Autowired
    private AssistantServiceImpl assistantService;

    @Autowired
    private UserService userService;

    private final TelegramClient telegramClient;

    private final BotConfig botConfig;

    public Bot(BotConfig botConfig) {
        this.botConfig = botConfig;
        telegramClient = new OkHttpTelegramClient(this.botConfig.getBotToken());
    }

    @Override
    public String getBotToken() {
        return this.botConfig.getBotToken();
    }

    @Override
    public LongPollingUpdateConsumer getUpdatesConsumer() {
        return this;
    }

    @AfterBotRegistration
    private void afterRegistration(BotSession botSession) {
        log.info("Registered bot running state is: {}", botSession.isRunning());
    }

    @Override
    public void consume(Update update) {
        if (update.hasMessage() && (update.getMessage().hasText() || update.getMessage().hasPhoto())) {
            Long chatId = update.getMessage().getChatId();
            String messageText = update.getMessage().hasText() ? update.getMessage().getText() : "";
            log.info(messageText);

            if (START.equals(messageText)) {
                if (userService.getUserById(chatId).isEmpty()) {
                    userService.saveUser(new User(chatId, true, new ArrayList<>()));
                    log.info("[{}] user registered", chatId);
                }
                sendMessage(chatId, messageTemplates.WELCOME_MESSAGE);
                showMenu(chatId);
            } else if (NEW_CONVERSATION.equals(messageText)) {
                log.info("[{}] new conversation have been started", chatId);
                sendMessage(chatId, "Новый диалог начат, слушаю вас");
                userService.saveUser(new User(chatId, true, new ArrayList<>()));
            } else {
                User user = userService.getUserById(chatId).get();

                if (!messageText.isEmpty()) {
                    Message userMessage = new Message(Role.user, messageText);
                    user.getMessages().add(userMessage);
                }

                ResponseDto responseDto;
                if (!update.getMessage().hasPhoto()) {
                    SendMessageDto sendMessageDto = SendMessageDto.builder()
                            .userId(chatId)
                            .isStartDialog(user.getIsStartDialog())
                            .prompt(user.getMessages())
                            .build();
                    responseDto = assistantService.sendMessage(sendMessageDto);
                } else {
                    String a = processImage(update);
                    SendImageDto sendImageDto = SendImageDto.builder()
                            .userId(chatId)
                            .isStartDialog(user.getIsStartDialog())
                            .prompt(user.getMessages())
                            .image("data:image/jpeg;base64," + a)
                            .build();
                    responseDto = assistantService.sendImage(sendImageDto);
                }

                sendMessage(chatId, responseDto.getResponse());

                user.getMessages().add(new Message(Role.assistant, responseDto.getResponse()));
                user.setIsStartDialog(false);
                userService.saveUser(user);
            }
        }
    }

    private String processImage(Update update) {
        PhotoSize largestPhoto = update.getMessage().getPhoto().stream()
                .max(Comparator.comparingInt(PhotoSize::getFileSize))
                .orElse(null);

        if (largestPhoto != null) {
            try {
                GetFile getFile = new GetFile(largestPhoto.getFileId());
                File file = telegramClient.execute(getFile);

                InputStream fileStream = telegramClient.downloadFileAsStream(file);

                return convertToBase64(fileStream);
            } catch (TelegramApiException e) {
                e.printStackTrace();
            }
        }
        return "";
    }

    private String convertToBase64(InputStream inputStream) {
        try (ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[1024];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }
            byte[] fileBytes = outputStream.toByteArray();
            return Base64.getEncoder().encodeToString(fileBytes);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public void sendMessage(Long userId, String text) {
        SendMessage sendMessage = SendMessage.builder()
                .chatId(userId)
                .text(text)
                .parseMode(ParseMode.HTML)
                .build();

        try {
            telegramClient.execute(sendMessage);
            log.info("[{}] Message have been sent to user", userId);
        } catch (TelegramApiException e) {
            log.error("[{}] Cannot send message", userId);
        }
    }

    private void showMenu(Long userId) {
        KeyboardButton startNewDialogBtn = new KeyboardButton(NEW_CONVERSATION.toString());
        ReplyKeyboardMarkup replyKeyboardMarkup = new ReplyKeyboardMarkup(List.of(
                new KeyboardRow(List.of(startNewDialogBtn))
        ));

        SendMessage sendMessage = SendMessage.builder()
                .chatId(userId)
                .text(messageTemplates.NEW_CONVERSATION)
                .replyMarkup(replyKeyboardMarkup)
                .parseMode(ParseMode.HTML)
                .build();

        try {
            telegramClient.execute(sendMessage);
        } catch (TelegramApiException e) {
            log.error("[{}] Cannot send message", userId);
        }
    }
}
