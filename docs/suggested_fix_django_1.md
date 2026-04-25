Two clear targets. Let me apply both fixes now.

**Fix 1:** Update `users.py` to import `List` from typing and change `list_users` response type.

**Fix 2:** Update `auth.py` to use `UserResponse.model_validate(user)` instead of the deprecated `from_orm`.

```bash
cd /home/project/wellfond-bms/backend
```

First, read the relevant lines to make precise edits:

```bash
sed -n '14,22p' /home/project/wellfond-bms/backend/apps/core/routers/users.py
sed -n '45,50p' /home/project/wellfond-bms/backend/apps/core/routers/auth.py
```

Then apply the edits:

```bash
# Fix users.py - change import and response type
sed -i 's/from typing import Optional/from typing import List, Optional/' /home/project/wellfond-bms/backend/apps/core/routers/users.py
sed -i 's/from ..schemas import UserCreate, UserListResponse, UserResponse, UserUpdate/from ..schemas import UserCreate, UserResponse, UserUpdate/' /home/project/wellfond-bms/backend/apps/core/routers/users.py
sed -i 's/@router.get("\/", response=UserListResponse)/@router.get("\/", response=List[UserResponse])/' /home/project/wellfond-bms/backend/apps/core/routers/users.py

# Fix auth.py - change from_orm to model_validate
sed -i 's/UserResponse.from_orm(user)/UserResponse.model_validate(user, from_attributes=True)/' /home/project/wellfond-bms/backend/apps/core/routers/auth.py
```

Verify the changes took effect:

```bash
# Verify fixes
grep -n "List\[UserResponse\]" /home/project/wellfond-bms/backend/apps/core/routers/users.py
grep -n "model_validate" /home/project/wellfond-bms/backend/apps/core/routers/auth.py
```

Then restart the server and test the CSRF endpoint again.

