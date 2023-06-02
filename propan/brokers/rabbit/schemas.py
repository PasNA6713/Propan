from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from aio_pika.abc import ExchangeType, TimeoutType
from pydantic import Field

from propan.asyncapi.bindings import (
    AsyncAPIChannelBinding,
    AsyncAPIOperationBinding,
    amqp,
)
from propan.asyncapi.channels import AsyncAPIChannel
from propan.asyncapi.message import AsyncAPICorrelationId, AsyncAPIMessage
from propan.asyncapi.subscription import AsyncAPISubscription
from propan.brokers._model.schemas import BaseHandler, NameRequired, Queue

__all__ = (
    "RabbitQueue",
    "RabbitExchange",
    "Handler",
    "ExchangeType",
)


class RabbitQueue(Queue):
    name: str = ""
    durable: bool = False
    exclusive: bool = False
    passive: bool = False
    auto_delete: bool = False
    arguments: Optional[Dict[str, Any]] = None
    timeout: TimeoutType = None
    robust: bool = True

    bind_arguments: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    routing_key: str = Field(default="", exclude=True)

    @property
    def routing(self) -> Optional[str]:
        return self.routing_key or self.name or None

    def __init__(
        self,
        name: str,
        durable: bool = False,
        exclusive: bool = False,
        passive: bool = False,
        auto_delete: bool = False,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: TimeoutType = None,
        robust: bool = True,
        bind_arguments: Optional[Dict[str, Any]] = None,
        routing_key: str = "",
    ):
        super().__init__(
            name=name,
            durable=durable,
            exclusive=exclusive,
            bind_arguments=bind_arguments,
            routing_key=routing_key,
            robust=robust,
            passive=passive,
            auto_delete=auto_delete,
            arguments=arguments,
            timeout=timeout,
        )


class RabbitExchange(NameRequired):
    type: ExchangeType = ExchangeType.DIRECT
    durable: bool = False
    auto_delete: bool = False
    internal: bool = False
    passive: bool = False
    arguments: Optional[Dict[str, Any]] = None
    timeout: TimeoutType = None
    robust: bool = True

    bind_to: Optional["RabbitExchange"] = Field(default=None, exclude=True)
    bind_arguments: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    routing_key: str = Field(default="", exclude=True)

    def __init__(
        self,
        name: str,
        type: ExchangeType = ExchangeType.DIRECT,
        durable: bool = False,
        auto_delete: bool = False,
        internal: bool = False,
        passive: bool = False,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: TimeoutType = None,
        robust: bool = True,
        bind_to: Optional["RabbitExchange"] = None,
        bind_arguments: Optional[Dict[str, Any]] = None,
        routing_key: str = "",
    ):
        super().__init__(
            name=name,
            type=type,
            durable=durable,
            auto_delete=auto_delete,
            routing_key=routing_key,
            bind_to=bind_to,
            bind_arguments=bind_arguments,
            robust=robust,
            internal=internal,
            passive=passive,
            timeout=timeout,
            arguments=arguments,
        )


@dataclass
class Handler(BaseHandler):
    queue: RabbitQueue
    exchange: Optional[RabbitExchange] = field(default=None, kw_only=True)  # type: ignore

    def get_schema(self) -> Dict[str, AsyncAPIChannel]:
        body = self.get_message_object()

        return {
            self.title: AsyncAPIChannel(
                subscribe=AsyncAPISubscription(
                    description=self.description or self.callback.__doc__,
                    bindings=AsyncAPIOperationBinding(
                        amqp=amqp.AsyncAPIAmqpOperationBinding(
                            cc=None
                            if (
                                self.exchange
                                and self.exchange.type
                                in (ExchangeType.FANOUT, ExchangeType.HEADERS)
                            )
                            else self.queue.name
                        )
                    ),
                    message=AsyncAPIMessage(
                        payload=body,
                        correlation_id=AsyncAPICorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=AsyncAPIChannelBinding(
                    amqp=amqp.AsyncAPIAmqpChannelBinding(
                        is_="routingKey",
                        queue=amqp.AsyncAPIAmqpQueue(
                            name=self.queue.name,
                            durable=self.queue.durable,
                            exclusive=self.queue.exclusive,
                            auto_delete=self.queue.auto_delete,
                        ),
                        exchange=(
                            amqp.AsyncAPIAmqpExchange(type="default")
                            if self.exchange is None
                            else amqp.AsyncAPIAmqpExchange(
                                type=self.exchange.type.value,
                                name=self.exchange.name,
                                durable=self.exchange.durable,
                                auto_delete=self.exchange.auto_delete,
                            )
                        ),
                    )
                ),
            ),
        }
