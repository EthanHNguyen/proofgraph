from datetime import datetime


def now():
    return datetime.utcnow().isoformat()


def audit_event(event_type, actor, action, target, timestamp):
    print({
        "event_type": event_type,
        "actor": actor,
        "action": action,
        "target": target,
        "timestamp": timestamp,
    })


def require_mfa(actor):
    return actor.get("mfa_verified") is True


def create_user(target):
    return {"id": target, "status": "active"}


def disable_user(target):
    return {"id": target, "status": "disabled"}


def assign_role(actor, target, role):
    if not require_mfa(actor):
        raise PermissionError("mfa required")
    audit_event(
        event_type="role_change",
        actor=actor["id"],
        action="assign_role",
        target=target,
        timestamp=now(),
    )
    return {"target": target, "role": role}
