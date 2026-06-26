"""Flatten a ChatGPT `conversations.json` export (mapping tree) into a tidy table."""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import PROCESSED_DIR, RAW_DIR  # noqa: E402


def _extract_text(message: dict) -> str:
    content = message.get("content", {})
    parts = content.get("parts", [])
    texts = [p for p in parts if isinstance(p, str)]
    return "\n".join(texts).strip()


def _walk_branch(mapping: dict, leaf_id: str) -> list[dict]:
    """Follow parent pointers from current_node back to the root, then reverse to chronological order."""
    nodes = []
    node_id = leaf_id
    while node_id is not None:
        node = mapping.get(node_id)
        if node is None:
            break
        nodes.append(node)
        node_id = node.get("parent")
    nodes.reverse()
    return nodes


def parse_conversation(conversation: dict) -> list[dict]:
    conversation_id = conversation.get("id") or conversation.get("conversation_id")
    mapping = conversation.get("mapping", {})
    leaf_id = conversation.get("current_node")
    nodes = _walk_branch(mapping, leaf_id)

    rows = []
    turn = 0
    for node in nodes:
        message = node.get("message")
        if message is None:
            continue
        role = message.get("author", {}).get("role")
        if role not in ("user", "assistant"):
            continue
        text = _extract_text(message)
        if not text:
            continue
        rows.append(
            {
                "conversation_id": conversation_id,
                "turn": turn,
                "role": role,
                "timestamp": message.get("create_time"),
                "text": text,
            }
        )
        turn += 1
    return rows


def parse_export(export_path: Path) -> pd.DataFrame:
    with open(export_path, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    rows = []
    for conv in conversations:
        rows.extend(parse_conversation(conv))

    df = pd.DataFrame(rows, columns=["conversation_id", "turn", "role", "timestamp", "text"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
    return df


if __name__ == "__main__":
    export_file = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_DIR / "conversations.json"
    df = parse_export(export_file)
    out_path = PROCESSED_DIR / "conversations.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Parsed {len(df)} messages from {df['conversation_id'].nunique()} conversations -> {out_path}")
