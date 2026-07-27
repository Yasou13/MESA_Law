import contextvars
from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria
from sqlalchemy.pool import Pool
from sqlalchemy import bindparam, text
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

@event.listens_for(Session, "after_begin")
def set_tenant_on_begin(session, transaction, connection):
    tenant_id = get_tenant_id()
    if tenant_id:
        # Use sync execute on the connection wrapper provided by SQLAlchemy
        connection.execute(text("SELECT set_config('app.current_tenant', :tenant, true)"), {"tenant": str(tenant_id)})



