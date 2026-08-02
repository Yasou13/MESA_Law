"""Fail closed on multiple Alembic heads or an invalid offline upgrade chain."""

import contextlib
import io
import os

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    os.environ.setdefault("MESA_LAW_ENVIRONMENT", "test")
    config = Config("alembic.ini")
    heads = ScriptDirectory.from_config(config).get_heads()
    if len(heads) != 1:
        print(f"Expected exactly one Alembic head, found {len(heads)}: {heads}")
        return 1

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        command.upgrade(config, "head", sql=True)
    rendered = output.getvalue()
    if not rendered.strip() or heads[0] not in rendered:
        print("Alembic offline upgrade did not render the complete head")
        return 1
    print(f"Alembic has one head ({heads[0]}) and a valid offline upgrade chain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
