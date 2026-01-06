from .user_base_dialog import UserBaseDialog


class ClaudeDialog(UserBaseDialog):

    @property
    def service_name(self):
        return "Claude"

    @property
    def models(self):
        return [
            "claude-haiku-4-5",
            "claude-sonnet-4-5",
            "claude-opus-4-5",
            "claude-opus-4-1",
            "claude-sonnet-4-0",
            "claude-3-7-sonnet-latest",
            "claude-3-5-haiku-latest",
            "claude-3-haiku-20240307",
        ]

    @property
    def base_url(self):
        return "https://api.anthropic.com/v1/messages"

    @property
    def system_prompt_description(self):
        return (
            'Enter the System Prompt to give Claude a "role".\n'
            "This is where you should give very specific instructions, examples, and "
            'do "prompt engineering".\n'
            "This is also where you tell the model which output to return.\n\n"
            "For more examples, see:\n"
            "https://docs.anthropic.com/en/prompt-library/library"
        )

    @property
    def system_prompt_placeholder(self):
        return (
            "You are an experienced German teacher who is helping me practice grammar. "
            "You will be provided with a German word. Respond with:\n"
            "- an 'exampleSentence' at A2 or B1 level about 10-15 words long using the "
            "provided German word, and\n"
            "- the 'translation' of that sentence into English\n\n"
            "As you are helping me practice grammar, be sure that your example "
            "sentences use a variety of different subjects, declensions, and word "
            "order patterns at the A2 or B1 level."
        )

    @property
    def user_prompt_description(self):
        return (
            "Enter the prompt that will be created and sent for each card.\n"
            "Use the field name surrounded by braces to substitute in a field from the card."
        )

    @property
    def user_prompt_placeholder(self):
        return "Example:\n" "{german_word}"
