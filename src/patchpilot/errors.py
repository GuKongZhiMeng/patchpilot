class PatchPilotError(Exception):
    """Stable, user-facing harness error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

