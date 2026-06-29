import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.parsing.chatgpt_parser import parse_conversation, parse_exports  # noqa: E402


def _make_conversation(conv_id, text, create_time):
    return {
        "id": conv_id,
        "current_node": "a",
        "mapping": {
            "a": {
                "id": "a",
                "parent": None,
                "message": {
                    "author": {"role": "user"},
                    "create_time": create_time,
                    "content": {"parts": [text]},
                },
            }
        },
    }


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
    assert [r["edit_count"] for r in rows] == [0, 1]  # "hello" had no siblings; the reply had 1 abandoned sibling (b1)


def test_parse_conversation_edit_count_zero_when_no_branching():
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
    }
    conversation = {"id": "conv1", "mapping": mapping, "current_node": "a"}

    rows = parse_conversation(conversation)

    assert [r["edit_count"] for r in rows] == [0]


def test_parse_exports_dedupes_conversations_repeated_across_files(tmp_path):
    """Overlapping exports (same conversation present in two files) shouldn't double-count messages."""
    shared = _make_conversation("conv_shared", "shared text", 1000)
    only_in_file_a = _make_conversation("conv_a", "only in file a", 2000)
    only_in_file_b = _make_conversation("conv_b", "only in file b", 3000)

    file_a = tmp_path / "export_a.json"
    file_b = tmp_path / "export_b.json"
    file_a.write_text(json.dumps([shared, only_in_file_a]), encoding="utf-8")
    file_b.write_text(json.dumps([shared, only_in_file_b]), encoding="utf-8")

    df = parse_exports([file_a, file_b])

    assert df["conversation_id"].nunique() == 3
    assert len(df) == 3
