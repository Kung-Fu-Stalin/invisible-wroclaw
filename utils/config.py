from pathlib import Path
from dynaconf import Dynaconf


PROJECT_DIR = Path(__file__).resolve().parent.parent


ENV_PATH = Path(PROJECT_DIR, ".env").resolve()
YAML_PATH = Path(PROJECT_DIR, "settings.yaml").resolve()

settings = Dynaconf(
    envvar_prefix=False,
    root_path=PROJECT_DIR.resolve(),
    load_dotenv=True,
    settings_files=[YAML_PATH],
    env_files=[ENV_PATH],
)
settings.PROJECT_ROOT = PROJECT_DIR
settings.IMAGES_DIR = Path(PROJECT_DIR, settings.IMAGES_DIR).resolve()
settings.DATABASE_PATH = Path(PROJECT_DIR, settings.DATABASE).resolve()
