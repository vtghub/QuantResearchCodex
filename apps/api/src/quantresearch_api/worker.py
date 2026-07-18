from quantresearch_api.settings import get_settings


def main() -> None:
    settings = get_settings()
    print(
        "QuantResearch worker placeholder started "
        f"(env={settings.env}, redis={settings.redis_url})"
    )


if __name__ == "__main__":
    main()
