import asyncio

from quantresearch_api.jobs import job_queue
from quantresearch_api.settings import get_settings


async def run_once() -> None:
    await job_queue.run_next()


def main() -> None:
    settings = get_settings()
    print(
        "QuantResearch worker placeholder started "
        f"(env={settings.env}, redis={settings.redis_url}, "
        f"job_store={job_queue.store.backend_name})"
    )
    asyncio.run(run_once())


if __name__ == "__main__":
    main()
