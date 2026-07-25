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
def set_tenant_on_checkout(dbapi_connection, connection_record, connection_proxy):
    tenant_id = current_tenant_id.get()
    cursor = dbapi_connection.cursor()
    try:
        if tenant_id:
            # Safely set the config. Using parameterized query is better but SET LOCAL doesn't always support it in some drivers.
            cursor.execute(f"SET LOCAL app.current_tenant = '{tenant_id}';")
        else:
            # Clear it if no tenant is set
            cursor.execute("SET LOCAL app.current_tenant = '';")
    except Exception as e:
        import logging
        logging.error(f"Failed to set RLS tenant: {e}")
    finally:
        cursor.close()
