from propan.test.redis import build_message

from main import healthcheck

def test_publish(test_broker):
    msg = build_message("ping", queue="ping")
    assert (await healthcheck(msg)) == "pong"