import asyncio


def test_smoke():
    assert True


def test_asyncio_runs():
    async def _coro():
        return True

    assert asyncio.run(_coro()) is True
