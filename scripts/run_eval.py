from ap_skill_generator.config import Settings
from ap_skill_generator.eval_suite import run_offline_eval
from ap_skill_generator.storage import Storage


def main() -> None:
    settings = Settings()
    storage = Storage(settings.database_url)
    metrics = run_offline_eval(storage)
    print(metrics)


if __name__ == "__main__":
    main()
