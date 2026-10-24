"""Unit tests for ORCA configuration."""

from orca.config.settings import Settings


def test_default_settings():
    """Verify default settings initialization."""
    cfg = Settings()
    assert cfg.orca_env in ["development", "testing", "production"]
    assert cfg.default_search_radius_km == 30.0
    assert cfg.max_search_radius_km == 100.0
    assert cfg.restricted_zone_buffer_km == 5.0
    assert cfg.incois_base_url == "https://www.incois.gov.in"
    assert cfg.imd_api_base_url == "https://api.imd.gov.in"


def test_custom_environment_override():
    """Verify custom environment overrides take precedence."""
    cfg = Settings(
        orca_env="testing",
        default_search_radius_km=45.0,
        max_search_radius_km=150.0,
    )
    assert cfg.orca_env == "testing"
    assert cfg.default_search_radius_km == 45.0
    assert cfg.max_search_radius_km == 150.0
