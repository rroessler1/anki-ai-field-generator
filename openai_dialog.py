from .user_base_dialog import UserBaseDialog


class OpenAIDialog(UserBaseDialog):

    @property
    def service_name(self):
        return "OpenAI"

    @property
    def models(self):
        return [
            "gpt-5-nano",
            "gpt-5-mini",
            "gpt-5",
            "gpt-5.1",
            "gpt-4.1-nano",
            "gpt-4.1-mini",
            "gpt-4.1",
            "gpt-4o-mini",
            "gpt-4o",
            "o3-mini",
            "o1",
            "o3-deep-research",
            "o4-mini-deep-research",
        ]

    @property
    def base_url(self):
        return "https://api.openai.com/v1"

    @property
    def system_prompt_description(self):
        return (
            "Enter the System Prompt that is the overall system instructions.\n"
            'This is where you should give very specific instructions, examples, and do "prompt engineering".\n'
            "This is also where you tell the model which output to return.\n\n"
            "For more examples, see:\n"
            "https://platform.openai.com/docs/guides/prompt-engineering/strategy-write-clear-instructions"
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
