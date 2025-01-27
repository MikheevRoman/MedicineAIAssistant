package gros.medicine.bot.assistant_service;

import lombok.*;
import lombok.experimental.FieldDefaults;

import java.util.List;

@Getter @Setter
@AllArgsConstructor
@Builder
@FieldDefaults(level = AccessLevel.PRIVATE)
public class PatientInfo {
    Integer age;
    Boolean hasChronicDiseases;
    List<String> chronicDiseases;
    Boolean hasAllergies;
    List<String> allergies;
}
