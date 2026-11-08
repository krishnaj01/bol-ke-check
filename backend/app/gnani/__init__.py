class GnaniError(Exception):
    """A Gnani (or configured LLM) call failed after retries."""


class LLMUnavailable(GnaniError):
    """No LLM endpoint is configured."""
