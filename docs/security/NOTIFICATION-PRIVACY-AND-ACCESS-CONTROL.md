# ChhatraLekha Notification Privacy and Access Control
## Authorization Policies, Tenant Isolation & DPDP Compliance

- **Document Version:** 1.0.0
- **Status:** Security Baseline
- **Date:** November 2026

---

## 1. Security Principles

The ChhatraLekha communication engine enforces four core privacy and security principles:
1. **Strict User Ownership**: Users have exclusive access to their personal alerts, read receipts, and preferences. No user can view, mark, or delete another user's private notification.
2. **Tenant Boundary Enforcement**: Institution notices are strictly confined to the publishing institution's members. Cross-tenant leakage or modification is prevented at the database query level.
3. **Fail-Closed Security Delivery**: Critical account security events (such as password updates, MFA changes, or unrecognized session logins) cannot be suppressed or disabled by any user preference setting.
4. **Data Minimization & Purpose Limitation**: In accordance with the Digital Personal Data Protection Act (DPDP Act 2023), notification payloads exclude unneeded PII, masking sensitive identifiers like 12-digit APAAR numbers.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Endpoint | Action | Minimum Permission / Role | Ownership Check |
| :--- | :--- | :--- | :--- |
| `GET /api/notifications` | List user notifications | Any authenticated user | Enforces `user_id == principal.subject` |
| `GET /api/notifications/paged` | List paginated notifications | Any authenticated user | Enforces `user_id == principal.subject` |
| `GET /api/notifications/unread-count` | Unread count | Any authenticated user | Scoped to caller |
| `POST /api/notifications/{id}/read` | Mark notice as read | Any authenticated user | Strict ownership match or 404 |
| `POST /api/notifications/read-all` | Mark all read | Any authenticated user | Scoped to caller |
| `DELETE /api/notifications/{id}` | Dismiss notice | Any authenticated user | Strict ownership match or 404 |
| `GET /api/notifications/preferences` | Get user preferences | Any authenticated user | Caller subject only |
| `PUT /api/notifications/preferences` | Update preferences | Any authenticated user | Caller subject only; `SECURITY` enforced |
| `POST /api/notifications/devices` | Register push device | Any authenticated user | Bound to `principal.subject` |
| `DELETE /api/notifications/devices/{token}` | Revoke push device | Any authenticated user | Must belong to caller or 404 |
| `POST /api/notifications/broadcast` | Broadcast notice | `MANAGE_ANNOUNCEMENTS` | Authorized staff only |
| `POST /api/announcements` | Publish circular | `MANAGE_ANNOUNCEMENTS` | Scoped to `principal.institution_id` |
| `PUT /api/announcements/{id}` | Edit notice | `MANAGE_ANNOUNCEMENTS` | Author or same-tenant admin |
| `GET /api/announcements/{id}/delivery-summary` | View delivery stats | `MANAGE_ANNOUNCEMENTS` | Same-tenant admin |
| `POST /api/announcements/{id}/acknowledge` | Acknowledge notice | `VIEW_ANNOUNCEMENTS` | Records caller's subject ID |

---

## 3. IDOR Mitigation & Ownership Verification

### 3.1 Mitigation Pattern
Insecure Direct Object Reference (IDOR) attacks are eliminated by never querying solely on external IDs like `notification_id` or `token`. Every mutation query couples the identifier with the caller's verified JWT subject:

```python
filter_query = {
    "notification_id": notification_id,
    "$or": [
        {"user_id": principal.subject},
        {"user_id": None, "institution_id": {"$in": [principal.institution_id, "INST-ALL", None]}},
    ],
}
res = await self.db["notifications"].delete_one(filter_query)
if res.deleted_count == 0:
    raise HTTPException(status_code=404, detail="Notification not found or access denied.")
```

If User A attempts to delete or mark User B's notification, the query returns zero modified records and responds with `404 Not Found`, giving zero information about whether the targeted ID exists for another user.

---

## 4. Mandatory Non-Disableable Security Alerts

### 4.1 Rationale
Users may customize their notification preferences to reduce noise (e.g. disabling assignment reminders or general circulars). However, account security notices alert users to potential account takeovers, unauthorized browser sessions, password resets, and suspicious credential usage. Permitting users or malicious actors to disable these alerts would create a severe security blindspot.

### 4.2 Implementation
- **Frontend**: The `SECURITY` category checkbox is disabled and rendered with a visible `[Required]` badge.
- **Backend Invariant**: `NotificationService.update_preferences` ensures `"SECURITY"` is always retained:
  ```python
  if "subscribed_categories" in payload_dict and payload_dict["subscribed_categories"] is not None:
      categories = list(payload_dict["subscribed_categories"])
      if "SECURITY" not in categories:
          categories.append("SECURITY")
      payload_dict["subscribed_categories"] = categories
  ```
- **Quiet Hours Bypass**: Security-critical alerts bypass quiet hour silencers and are dispatched immediately across all active channels.

---

## 5. Device Token Security & Revocation

1. **Token Scoping**: Device tokens received from Android FCM or Apple APNs are stored alongside `user_id` and the client's source IP address.
2. **Session Cleanup**: When a user logs out, the native client invokes `DELETE /api/notifications/devices/{token}` to purge the token, preventing future alerts from being delivered to shared or reassigned handsets.
3. **No Cross-User Leakage**: Device lookup for push dispatch filters strictly by `user_id in target_recipients`.

---

## 6. DPDP Act 2023 Compliance

1. **Purpose Limitation**: Contact details (email and device tokens) collected for notifications are utilized solely for educational and institutional alerts authorized by the academic institution.
2. **Right to Withdraw Consent**: Users can independently toggle off in-app, email, and push channels (except mandatory security alerts) at any time through the Notification Preferences panel.
3. **Auditability**: All preference modifications, device registrations, and notice broadcasts generate immutable audit entries in the `audit_events` collection via `AuditRepository`.
