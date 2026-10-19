"""The owner-approved server protections must remain enabled."""
import configparser
from pathlib import Path


def test_streamlit_cross_origin_and_xsrf_protection_enabled():
    settings = configparser.ConfigParser()
    settings.read(Path(__file__).resolve().parents[1] / ".streamlit/config.toml")
    assert settings.getboolean("server", "enableCORS")
    assert settings.getboolean("server", "enableXsrfProtection")
