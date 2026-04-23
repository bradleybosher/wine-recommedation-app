from model import generate


def test_model_returns_string():
    result = generate("Hello")
    assert isinstance(result, str)
