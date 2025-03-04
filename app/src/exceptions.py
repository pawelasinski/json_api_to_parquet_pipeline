from aiohttp import ClientError


class MaximumRetryException(ClientError):
    """Exception raised when the maximum number of retries has been reached."""

    def __init__(self, message: str) -> None:
        """Initialize the MaximumRetryException exception.

        Args:
            message: Error message.

        """
        super().__init__(message)
