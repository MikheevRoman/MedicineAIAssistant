package gros.medicine.bot.user.entity;

import gros.medicine.bot.assistant_service.Message;
import gros.medicine.bot.user.converter.MessageListConverter;
import jakarta.persistence.*;
import lombok.*;

import java.util.List;

@Entity
@Table(name = "users")
@AllArgsConstructor
@NoArgsConstructor
@Getter @Setter
public class User {
    @Id
    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "is_start_dialog", nullable = false)
    private Boolean isStartDialog;

    @Convert(converter = MessageListConverter.class)
    @Column(name = "messages", columnDefinition = "TEXT")
    private List<Message> messages;
}
