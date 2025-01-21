package gros.medicine.bot.bot_service.templates;

import org.springframework.stereotype.Component;

@Component
public class MessageTemplates {
    public final String NEW_APPOINTMENT_MESSAGE_TEMPLATE = """
            Вы успешно записаны к %s (%s)
            Дата и время записи: %s
            Медорганизация: %s
            Адрес: %s
            """;

    public final String WELCOME_MESSAGE = """
            Здравствуйте, здесь вы можете получить бесплатную консультацию по вопросам здоровья, а также записаться на прием к врачу
            """;
}
