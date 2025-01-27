package gros.medicine.bot.bot_service.templates;

import org.springframework.stereotype.Component;

@Component
public class MessageTemplates {
    public final String NEW_APPOINTMENT_MESSAGE_TEMPLATE = """
            Вы успешно записаны к %s (<i>%s</i>)
            <b>🕐 Дата и время записи:</b> %s
            
            <b>🏥 Медорганизация:</b> %s
            <b>🗺 Адрес:</b> %s
            """;

    public final String WELCOME_MESSAGE = """
            Здравствуйте, здесь вы можете получить бесплатную консультацию по вопросам здоровья, а также записаться на прием к врачу
            """;

    public final String NEW_CONVERSATION = """
            Для начала нового диалога нажмите
            <b>"Начать новое обсуждение ✍️"</b>
            """;
}
