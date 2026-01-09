from .user_base_dialog import UserBaseDialog


class DeepSeekDialog(UserBaseDialog):

    @property
    def service_name(self):
        return "DeepSeek"

    @property
    def models(self):
        return ["deepseek-chat", "deepseek-reasoner"]

    @property
    def base_url(self):
        return "https://api.deepseek.com/chat/completions"

    @property
    def system_prompt_description(self):
        return (
            "Enter the System Prompt that is the overall system instructions.\n"
            "This is where you should give very specific instructions, examples, and "
            'do "prompt engineering". \n'
            "This is also where you tell the model which output to return.\n\n"
            "The response will be in JSON key-value pairs. "
            "Include an example response in your prompt. "
            "For an example, see:\n"
            "https://api-docs.deepseek.com/guides/json_mode"
        )

    @property
    def system_prompt_placeholder(self):

        return (
            "Example:\n"
            "You are an experienced German teacher who is helping me practice grammar. "
            "You will be provided with a German word. Respond with:\n"
            "- an 'exampleSentence' at A2 or B1 level about 10-15 words long using the "
            "provided German word, and\n"
            "- the 'translation' of that sentence into English\n\n"
            "EXAMPLE JSON OUTPUT:\n"
            "{\n"
            '"exampleSentence": "Mein Bruder kommt aus den USA.",\n'
            '"translation": "My brother is from the USA."\n'
            "}"
        )

    @property
    def user_prompt_description(self):
        return (
            "Enter the prompt that will be created and sent for each card.\n"
            "Use the field name surrounded by braces to substitute in a field from the card."
        )

    @property
    def user_prompt_placeholder(self):
        return "Example:\n" '"""{german_word}"""\n\n{german_sentence}\n'
