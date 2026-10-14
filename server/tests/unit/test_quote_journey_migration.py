"""quote_journey_events migration must keep FK types aligned with production."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import dialect as pg_dialect

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "c8e4a91d2b7f_add_quote_journey_events.py"
)


def _column_type_name(source: str, column_name: str) -> str | None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "Column"):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.Constant) or first.value != column_name:
            continue
        if len(node.args) < 2:
            return None
        typ = node.args[1]
        if isinstance(typ, ast.Call) and isinstance(typ.func, ast.Attribute):
            return typ.func.attr
        if isinstance(typ, ast.Attribute):
            return typ.attr
    return None


def _fk_pairs(source: str) -> list[tuple[str, str]]:
    """Return (local_col, referred_table.col) pairs from ForeignKeyConstraint calls."""
    tree = ast.parse(source)
    pairs: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "ForeignKeyConstraint"):
            continue
        if len(node.args) < 2:
            continue
        locals_node, remotes_node = node.args[0], node.args[1]
        if not (
            isinstance(locals_node, ast.List)
            and isinstance(remotes_node, ast.List)
        ):
            continue
        for local, remote in zip(locals_node.elts, remotes_node.elts):
            if isinstance(local, ast.Constant) and isinstance(remote, ast.Constant):
                pairs.append((local.value, remote.value))
    return pairs


@pytest.mark.unit
def test_migration_file_and_revision_id_unchanged():
    assert MIGRATION_PATH.is_file()
    source = MIGRATION_PATH.read_text()
    assert 'revision: str = "c8e4a91d2b7f"' in source
    module = ast.parse(source)
    assigned: dict[str, object] = {}
    for node in module.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and isinstance(node.value, ast.Constant)
        ):
            assigned[node.target.id] = node.value.value
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
        ):
            assigned[node.targets[0].id] = node.value.value
    assert assigned.get("revision") == "c8e4a91d2b7f"
    assert assigned.get("down_revision") == "f4318b2b2f9a"


@pytest.mark.unit
def test_location_id_is_uuid_to_match_locations_id():
    source = MIGRATION_PATH.read_text()
    assert _column_type_name(source, "location_id") == "Uuid"
    assert _column_type_name(source, "user_id") == "String"
    compiled = Uuid().compile(dialect=pg_dialect())
    assert compiled.lower() == "uuid"


@pytest.mark.unit
def test_foreign_keys_match_referenced_column_types():
    """location_id -> locations.id (uuid); user_id -> users.id (varchar)."""
    source = MIGRATION_PATH.read_text()
    fks = dict(_fk_pairs(source))
    assert fks["location_id"] == "locations.id"
    assert fks["user_id"] == "users.id"
    assert _column_type_name(source, "location_id") == "Uuid"
    assert _column_type_name(source, "user_id") == "String"
