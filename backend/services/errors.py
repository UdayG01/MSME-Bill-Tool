class ServiceError(Exception):
    """Business-layer error translated to an HTTP response by main.py."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail

