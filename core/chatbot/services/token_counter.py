import tiktoken


class TokenCounter:

    def __init__(self, model: str = "gpt-4o-mini"):

        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback tokenizer; may not match the target model exactly.
            self.encoder = tiktoken.get_encoding("o200k_base")

    def count_text(self, text: str):
        return len(self.encoder.encode(text=text))

    def count_messages(self, messages: list[dict]):

        total = 0

        for message in messages:

            total += self.count_text(message.get("role", ""))
            total += self.count_text(message.get("content", ""))

        return total
