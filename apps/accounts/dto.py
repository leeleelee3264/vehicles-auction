from dataclasses import dataclass

@dataclass(frozen=True)
class LoginDTO:
    username: str
    password: str
