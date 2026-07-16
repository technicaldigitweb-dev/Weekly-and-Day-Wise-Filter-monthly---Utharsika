"""
UAWSO database connection manager.

Single place responsible for opening/closing a psycopg2 connection.
Credentials are never logged; config.redact() must be used for any
log line that touches the DBConfig object.
"""

from contextlib import contextmanager

from config.config import load_db_config, redact


@contextmanager
def get_connection(readonly: bool = True):
    """
    Yields a psycopg2 connection. readonly=True (the default) sets the
    session to READ ONLY at the database level as a second line of
    defense on top of the query logic itself - a read-only dry run
    cannot accidentally write even if a bug puts a write statement in
    the wrong code path.
    """
    import psycopg2

    cfg = load_db_config()
    conn = psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.dbname,
        user=cfg.user,
        password=cfg.password,
    )
    try:
        if readonly:
            conn.set_session(readonly=True, autocommit=False)
        yield conn
    finally:
        conn.close()


def connection_summary(cfg) -> str:
    """Safe-to-log summary of a DBConfig - host/db name only, never credentials."""
    return f"host={cfg.host} port={cfg.port} db={cfg.dbname} user={cfg.user} password={redact(cfg.password)}"
