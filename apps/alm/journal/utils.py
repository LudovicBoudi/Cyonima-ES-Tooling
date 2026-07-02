from apps.alm.journal.models import AuditLog


def log_audit(project, user, action, entity_type, entity_id, summary, details=''):
    if not user or user.is_anonymous:
        return
    AuditLog.objects.create(
        project=project,
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        details=details,
    )
