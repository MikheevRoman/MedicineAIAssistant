package gros.medicine.bot.bot_service;

import gros.medicine.bot.bot_service.config.BotConfig;
import gros.medicine.bot.bot_service.templates.MessageTemplates;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.telegram.telegrambots.client.okhttp.OkHttpTelegramClient;
import org.telegram.telegrambots.longpolling.BotSession;
import org.telegram.telegrambots.longpolling.interfaces.LongPollingUpdateConsumer;
import org.telegram.telegrambots.longpolling.starter.AfterBotRegistration;
import org.telegram.telegrambots.longpolling.starter.SpringLongPollingBot;
import org.telegram.telegrambots.longpolling.util.LongPollingSingleThreadUpdateConsumer;
import org.telegram.telegrambots.meta.api.methods.send.SendMessage;
import org.telegram.telegrambots.meta.api.objects.Update;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;
import org.telegram.telegrambots.meta.generics.TelegramClient;

@Component
@Slf4j
public class Bot implements SpringLongPollingBot, LongPollingSingleThreadUpdateConsumer {
    @Autowired
    private MessageTemplates messageTemplates;

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
        if (update.hasMessage() && update.getMessage().hasText()) {
            Long chatId = update.getMessage().getChatId();
            String messageText = update.getMessage().getText();

            if (messageText.equals("/start")) {
                this.sendMessage(chatId, messageTemplates.WELCOME_MESSAGE);
            }
        }
    }

    public void sendMessage(Long userId, String text) {
        SendMessage sendMessage = SendMessage.builder()
                .chatId(userId)
                .text(text)
                .build();

        try {
            telegramClient.execute(sendMessage);
        } catch (TelegramApiException e) {
            log.error("[{}] Cannot send message", userId);
        }
    }
}
