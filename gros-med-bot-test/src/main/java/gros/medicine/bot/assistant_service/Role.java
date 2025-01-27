package gros.medicine.bot.assistant_service;

public enum Role {
    user,
    assistant;

    @Override
    public String toString() {
        return this.name();
    }
}
