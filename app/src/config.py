from dataclasses import dataclass


@dataclass(frozen=True)
class HTTPConfigs:
    """Dataclass to store HTTP configuration parameters.

     Attributes:
         max_concurrent_requests: Maximum number of concurrent HTTP requests.
         retries: Number of retry attempts for failed HTTP requests.
         delay: Initial delay (in seconds) before retrying a failed request.
         backoff: Multiplier applied to delay for each subsequent retry.

     """
    max_concurrent_requests: int = 5
    retries: int = 5
    delay: int = 3
    backoff: int = 3


http_configs = HTTPConfigs()
