from app.core.config import get_settings
from app.core.security import validate_password_strength


def test_doubt_similarity_threshold_defaults_to_085():
    assert get_settings().doubt_similarity_threshold == 0.85


def test_password_rejects_values_over_bcrypt_limit():
    password = "a" * 73
    is_valid, error = validate_password_strength(password)

    assert is_valid is False
    assert "72 bytes or fewer" in error
