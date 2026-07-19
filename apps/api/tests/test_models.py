from quantresearch_api.models import Base
from sqlalchemy import create_engine, inspect


def test_model_metadata_contains_initial_platform_tables() -> None:
    expected_tables = {
        "audit_records",
        "datasets",
        "organizations",
        "research_runs",
        "strategies",
        "users",
        "workspaces",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_model_metadata_creates_tables_in_sqlite() -> None:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    tables = set(inspect(engine).get_table_names())
    assert "datasets" in tables
    assert "audit_records" in tables
