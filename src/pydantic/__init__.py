class BaseModel:
    """Minimal stub of pydantic.BaseModel for testing without dependency."""
    def __init__(self, **data):
        for k, v in data.items():
            setattr(self, k, v)

    def dict(self, *args, **kwargs):
        return self.__dict__
