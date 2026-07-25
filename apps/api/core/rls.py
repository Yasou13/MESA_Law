import contextvars
from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria
from sqlalchemy.pool import Pool
from sqlalchemy import bindparam
from .models import TenantAwareMixin

current_tenant_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_tenant_id", default=None)

def set_tenant_id(tenant_id: str | None):
    current_tenant_id.set(tenant_id)

def get_tenant_id() -> str | None:
    return current_tenant_id.get()

# Application-level RLS (WHERE clauses)
@event.listens_for(Session, "do_orm_execute")
def _add_tenant_criteria(execute_state: ORMExecuteState):
    if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
        def filter_tenant(cls):
            def get_tenant_or_raise():
                tid = get_tenant_id()
                if tid is None:
                    raise RuntimeError("RLS Guard: Attempted to query tenant-specific data without an active tenant context")
                return tid
                
            return cls.tenant_id == bindparam("current_tenant_id_bind", callable_=get_tenant_or_raise)

        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(TenantAwareMixin, filter_tenant, include_aliases=True)
        )

# Database-level RLS (PostgreSQL Row Level Security)
@event.listens_for(Pool, "checkout")
def reset_tenant_on_checkout(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT set_config('app.current_tenant', '', false);")
    except Exception as e:
        import logging
        logging.error(f"CRITICAL: Failed to reset RLS tenant on pool checkout: {e}")
        raise
    finally:
        cursor.close()

@event.listens_for(Pool, "checkin")
def reset_tenant_on_checkin(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT set_config('app.current_tenant', '', false);")
    except Exception as e:
        import logging
        logging.error(f"Failed to reset RLS tenant on pool checkin: {e}")
    finally:
        cursor.close()

