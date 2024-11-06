from dataclasses import dataclass


@dataclass
class WhatsappStatus:
    Connected: bool
    LoggedIn: bool


@dataclass
class WhatsappEvent:
    sender: str
    conversation: str
    type: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            sender=data["event"]["Info"]["Sender"],
            conversation=data.get("event", {}).get("Message", {}).get("conversation"),
            type=data["type"],
        )
