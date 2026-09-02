from app.services.short_code import ALPHABET, generate_short_code


def test_generated_code_has_default_length():
    code = generate_short_code()
    assert len(code) == 7


def test_generated_code_uses_only_base62_alphabet():
    code = generate_short_code(length=50)
    assert all(c in ALPHABET for c in code)


def test_generated_codes_are_not_trivially_repeated():
    codes = {generate_short_code() for _ in range(200)}
    # 62^7 possibilities — 200 draws colliding would indicate a broken RNG.
    assert len(codes) == 200


def test_custom_length_respected():
    assert len(generate_short_code(length=12)) == 12
