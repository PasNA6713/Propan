import pytest

from propan import RabbitBroker
from tests.brokers.base.connection import BrokerConnectionTestcase


@pytest.mark.rabbit
class TestRabbitConnection(BrokerConnectionTestcase):
    broker = RabbitBroker

    @pytest.mark.asyncio
    async def test_init_connect_by_raw_data(self, settings):
        broker = self.broker(
            host=settings.host,
            login=settings.login,
            password=settings.password,
            port=settings.port,
        )
        assert await broker.connect()
        await broker.close()

    @pytest.mark.asyncio
    async def test_connection_by_params(self, settings):
        broker = self.broker()
        assert await broker.connect(
            host=settings.host,
            login=settings.login,
            password=settings.password,
            port=settings.port,
        )
        await broker.close()
