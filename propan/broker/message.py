from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, Union
from uuid import uuid4

from typing_extensions import TypeVar

from propan.types import AnyDict, DecodedMessage

Msg = TypeVar("Msg")


@dataclass
class PropanMessage(Generic[Msg]):
    raw_message: Msg

    body: Union[bytes, Any]
    decoded_body: Optional[DecodedMessage] = None

    content_type: Optional[str] = None
    reply_to: str = ""
    headers: AnyDict = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid4()))  # pragma: no cover
    correlation_id: str = field(
        default_factory=lambda: str(uuid4())
    )  # pragma: no cover

    processed: bool = False

    @abstractmethod
    def ack(self, **kwargs: AnyDict) -> None:
        raise NotImplementedError()

    @abstractmethod
    def nack(self, **kwargs: AnyDict) -> None:
        raise NotImplementedError()

    @abstractmethod
    def reject(self, **kwargs: AnyDict) -> None:
        raise NotImplementedError()
