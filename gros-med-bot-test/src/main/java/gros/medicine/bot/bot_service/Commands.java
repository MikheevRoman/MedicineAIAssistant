package gros.medicine.bot.bot_service;

public enum Commands {
    START("/start"),
    NEW_CONVERSATION("Начать новое обсуждение ✍️");

    private final String commandText;

    Commands(String commandText) {
        this.commandText = commandText;
    }

    @Override
    public String toString() {
        return this.commandText;
    }

    public boolean equals(String commandText) {
        return this.commandText.equals(commandText);
    }
}
