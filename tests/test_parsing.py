import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.parsing.chatgpt_parser import parse_conversation  # noqa: E402


def test_parse_conversation_follows_parent_chain():
    mapping = {
        "root": {"id": "root", "message": None, "parent": None},
        "a": {
            "id": "a",
            "parent": "root",
            "message": {
                "author": {"role": "user"},
                "create_time": 1000,
                "content": {"parts": ["hello"]},
            },
        },
        "b": {
            "id": "b",
            "parent": "a",
            "message": {
                "author": {"role": "assistant"},
                "create_time": 1001,
                "content": {"parts": ["hi there"]},
            },
        },
    }
    conversation = {"id": "conv1", "mapping": mapping, "current_node": "b"}

    rows = parse_conversation(conversation)

    assert [r["role"] for r in rows] == ["user", "assistant"]
    assert [r["text"] for r in rows] == ["hello", "hi there"]
    assert [r["turn"] for r in rows] == [0, 1]


def test_parse_conversation_ignores_unrelated_branch():
    """A retried branch off the same parent should not appear if it isn't on the current_node path."""
    mapping = {
        "root": {"id": "root", "message": None, "parent": None},
        "a": {
            "id": "a",
            "parent": "root",
            "message": {
                "author": {"role": "user"},
                "create_time": 1000,
                "content": {"parts": ["hello"]},
            },
        },
        "b1": {
            "id": "b1",
            "parent": "a",
            "message": {
                "author": {"role": "assistant"},
                "create_time": 1001,
                "content": {"parts": ["first try"]},
            },
        },
        "b2": {
            "id": "b2",
            "parent": "a",
            "message": {
                "author": {"role": "assistant"},
                "create_time": 1002,
                "content": {"parts": ["regenerated reply"]},
            },
        },
    }
    conversation = {"id": "conv1", "mapping": mapping, "current_node": "b2"}

    rows = parse_conversation(conversation)

    assert [r["text"] for r in rows] == ["hello", "regenerated reply"]
