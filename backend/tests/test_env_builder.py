import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.env_builder import build_env


def test_always_includes_openai_key():
    result = build_env([], {}, "none")
    assert "OPENAI_API_KEY=" in result


def test_openrouter_key_filled_from_input():
    result = build_env(["openrouter"], {"openrouter": "sk-test-123"}, "none")
    assert "OPENROUTER_API_KEY=sk-test-123" in result


def test_openrouter_key_placeholder_when_not_provided():
    result = build_env(["openrouter"], {}, "none")
    assert "OPENROUTER_API_KEY=your-openrouter-key-here" in result


def test_tavily_key_filled_from_input():
    result = build_env(["tavily"], {"tavily": "tvly-abc"}, "none")
    assert "TAVILY_API_KEY=tvly-abc" in result


def test_postgres_adds_database_url():
    result = build_env([], {}, "postgres")
    assert "DATABASE_URL=" in result
    assert "postgres://" in result


def test_firebase_adds_multiple_keys():
    result = build_env([], {}, "firebase")
    assert "FIREBASE_PROJECT_ID=" in result
    assert "FIREBASE_API_KEY=" in result


def test_no_db_no_database_keys():
    result = build_env([], {}, "none")
    assert "DATABASE_URL" not in result
    assert "FIREBASE" not in result


def test_multiple_apis_and_db():
    result = build_env(["openrouter", "tavily"], {"openrouter": "sk-or"}, "postgres")
    assert "OPENROUTER_API_KEY=sk-or" in result
    assert "TAVILY_API_KEY=your-tavily-key-here" in result
    assert "DATABASE_URL=" in result


def test_result_is_string():
    result = build_env(["openrouter"], {}, "postgres")
    assert isinstance(result, str)
