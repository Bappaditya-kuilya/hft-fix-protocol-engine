import asyncio
import threading

from fix_engine import auth


def setup_function(_):
    with auth._lock:
        auth._sessions.clear()


def test_sync_register_validate_deregister():
    assert auth.validate_session("s1") is False
    auth.register_session("s1")
    assert auth.validate_session("s1") is True
    auth.deregister_session("s1")
    assert auth.validate_session("s1") is False


def test_threaded_contention():
    n = 50
    ids = [f"t-{i}" for i in range(n)]
    threads = [threading.Thread(target=auth.register_session, args=(i,)) for i in ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all(auth.validate_session(i) for i in ids)


def test_asyncio_tasks():
    async def main():
        ids = [f"a-{i}" for i in range(20)]

        async def reg(sid):
            auth.register_session(sid)
            return auth.validate_session(sid)

        results = await asyncio.gather(*(reg(i) for i in ids))
        assert all(results)
        assert all(auth.validate_session(i) for i in ids)

    asyncio.run(main())
