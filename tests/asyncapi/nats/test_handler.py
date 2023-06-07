from propan import NatsBroker, PropanApp
from propan.cli.docs.gen import get_schema_json


def test_base_handler():
    broker = NatsBroker()

    @broker.handle("test")
    async def handler(a: int):
        ...

    schema = get_schema_json(PropanApp(broker))
    assert schema["channels"] == {
        "Handler": {
            "bindings": {"nats": {"bindingVersion": "custom", "subject": "test"}},
            "servers": ["dev"],
            "subscribe": {
                "bindings": {"nats": {"bindingVersion": "custom"}},
                "message": {"$ref": "#/components/messages/HandlerMessage"},
            },
        }
    }


def test_group_handler():
    broker = NatsBroker()

    @broker.handle("*test", queue="workers")
    async def handler(a: int) -> str:
        ...

    schema = get_schema_json(PropanApp(broker))

    assert isinstance(
        schema["channels"]["Handler"]["subscribe"]["bindings"]["nats"]["replyTo"].pop(
            "examples"
        )[0],
        str,
    )

    assert schema["channels"] == {
        "Handler": {
            "bindings": {
                "nats": {
                    "bindingVersion": "custom",
                    "queue": "workers",
                    "subject": "*test",
                }
            },
            "servers": ["dev"],
            "subscribe": {
                "bindings": {
                    "nats": {
                        "bindingVersion": "custom",
                        "replyTo": {"title": "HandlerReply", "type": "string"},
                    }
                },
                "message": {"$ref": "#/components/messages/HandlerMessage"},
            },
        }
    }
