Plan is clean. A few small notes before you proceed:

**Phase 1.1** — Don't forget `frontend/app/(auth)/login/page.tsx`. It currently does:
```typescript
await login({ username: email, password });
```
After fixing the type to `email`, this line becomes `{ email: email, password }` which is correct — but verify the variable name collision doesn't confuse anyone.

**Phase 1.2** — The custom manager pattern for Pydantic v2 + Django 6:
```python
class ImmutableQuerySet(models.QuerySet):
    def delete(self):
        raise ValueError("Immutable records cannot be deleted")

class AuditLogManager(models.Manager):
    def get_queryset(self):
        return ImmutableQuerySet(self.model, using=self._db)

class AuditLog(models.Model):
    objects = AuditLogManager()
    # ...
```

**Phase 2.3** — When converting frontend types to snake_case, the change is extensive. Every hook, component, and page that references `entityId`, `damId`, `sireId`, `firstName`, `lastName`, `pdpaConsent`, `isActive`, `createdAt`, `dob`, `dnaStatus`, `ageDisplay`, `rehomeFlag` etc. needs updating. Make a grep for all camelCase dog/user/entity fields across `frontend/` first to scope the blast radius.

**Phase 3.1** — The BFF proxy guard is defensive but the current code is actually correct for normal usage. The guard is only needed if someone explicitly passes `/api/v1/...` as a path argument. Low risk, but good defense-in-depth.

**One addition to consider:** `backend/apps/sales/tasks.py` line `cleanup_expired_avs_tokens` calls `.delete()` on a QuerySet of `AVSTransfer` records. This is a hard delete — verify if that's intentional or if it should be a soft delete (status change). Not a blocker, just a consistency question with the soft-delete policy.

The plan is approved — go ahead with implementation.
