class SafetyPolicy:
    @staticmethod
    def sanitize_llm_output(text: str) -> str:
        sanitized = text

        phrases_to_remove = ["guaranteed profit", "sure win"]
        for phrase in phrases_to_remove:
            sanitized = sanitized.replace(phrase, "")
            sanitized = sanitized.replace(phrase.upper(), "")
            sanitized = sanitized.replace(phrase.capitalize(), "")

        disclaimer = "\n\nResearch output only. Not financial advice. Manual execution required."
        if disclaimer not in sanitized:
            sanitized = sanitized + disclaimer

        return sanitized
