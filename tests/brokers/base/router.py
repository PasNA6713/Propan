import asyncio
from typing import Type

import pytest

from propan.broker.core.asyncronous import BrokerAsyncUsecase
from propan.broker.router import BrokerRoute, BrokerRouter
from propan.types import AnyCallable
from tests.brokers.base.middlewares import LocalMiddlewareTestcase
from tests.brokers.base.parser import LocalCustomParserTestcase


@pytest.mark.asyncio
@pytest.mark.rabbit
class RouterTestcase(LocalMiddlewareTestcase, LocalCustomParserTestcase):
    build_message: AnyCallable
    route_class: Type[BrokerRoute]

    def patch_broker(
        self, br: BrokerAsyncUsecase, router: BrokerRouter
    ) -> BrokerAsyncUsecase:
        br.include_router(router)
        return br

    @pytest.fixture
    def raw_broker(self, broker):
        return broker

    @pytest.fixture
    def pub_broker(self, broker):
        return broker

    async def test_empty_prefix(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        @router.subscriber(queue)
        def subscriber(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_not_empty_prefix(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        router.prefix = "test_"

        @router.subscriber(queue)
        def subscriber(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_empty_prefix_publisher(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        @router.subscriber(queue)
        @router.publisher(queue + "resp")
        def subscriber(m):
            return "hi"

        @router.subscriber(queue + "resp")
        def response(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_not_empty_prefix_publisher(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        router.prefix = "test_"

        @router.subscriber(queue)
        @router.publisher(queue + "resp")
        def subscriber(m):
            return "hi"

        @router.subscriber(queue + "resp")
        def response(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_manual_publisher(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        router.prefix = "test_"

        p = router.publisher(queue + "resp")

        @router.subscriber(queue)
        async def subscriber(m):
            await p.publish("resp")

        @router.subscriber(queue + "resp")
        def response(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_delayed_handlers(
        self,
        event: asyncio.Event,
        router: BrokerRouter,
        queue: str,
        pub_broker: BrokerAsyncUsecase,
    ):
        def response(m):
            event.set()

        r = type(router)(prefix="test_", handlers=(self.route_class(response, queue),))

        pub_broker.include_router(r)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_nested_routers_sub(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        core_router = type(router)(prefix="test1_")
        router.prefix = "test2_"

        @router.subscriber(queue)
        def subscriber(m):
            event.set()
            return "hi"

        core_router.include_routers(router)
        pub_broker.include_routers(core_router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(
                    pub_broker.publish("hello", f"test1_test2_{queue}")
                ),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        subscriber.mock.assert_called_with("hello")

    async def test_nested_routers_pub(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        core_router = type(router)(prefix="test1_")
        router.prefix = "test2_"

        @router.subscriber(queue)
        @router.publisher(queue + "resp")
        def subscriber(m):
            return "hi"

        @pub_broker.subscriber("test1_" + "test2_" + queue + "resp")
        def response(m):
            event.set()

        core_router.include_routers(router)
        pub_broker.include_routers(core_router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(
                    pub_broker.publish("hello", f"test1_test2_{queue}")
                ),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()


@pytest.mark.asyncio
class RouterLocalTestcase(RouterTestcase):
    @pytest.fixture
    def pub_broker(self, test_broker):
        return test_broker

    async def test_publisher_mock(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        pub = router.publisher(queue + "resp")

        @router.subscriber(queue)
        @pub
        def subscriber(m):
            event.set()
            return "hi"

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        pub.mock.assert_called_with("hi")

    async def test_subscriber_mock(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        @router.subscriber(queue)
        def subscriber(m):
            event.set()
            return "hi"

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        subscriber.mock.assert_called_with("hello")

    async def test_manual_publisher_mock(
        self, router: BrokerRouter, queue: str, pub_broker: BrokerAsyncUsecase
    ):
        publisher = router.publisher(queue + "resp")

        @pub_broker.subscriber(queue)
        async def m(m):
            await publisher.publish("response")

        pub_broker.include_router(router)
        await pub_broker.start()
        await pub_broker.publish("hello", queue)
        publisher.mock.assert_called_with("response")
