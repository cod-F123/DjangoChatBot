import tiktoken


class TokenCounter:

    def __init__(self, model: str = "gpt-4o-mini"):

        self.encoder = tiktoken.encoding_for_model(model_name=model)

    def count_text(self, text: str):
        return len(self.encoder.encode(text=text))

    def count_messages(self, messages: dict):

        total = 0

        for message in messages:

            total += self.count_text(message.get("content", ""))

        return total
