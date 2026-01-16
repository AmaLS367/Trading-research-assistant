class PipelineTrace:
    """
    Pipeline trace output for verbose mode.

    Emits human-readable trace events in a consistent format.
    Only active when enabled=True, otherwise does nothing.
    """

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def emit(self, message: str) -> None:
        """
        Emit a trace message.

        Args:
            message: Message in format "stage | event | details"
        """
        if not self.enabled:
            return

        print(f"TRACE | {message}")
