# SECURITY.md

> **Status:** PLACEHOLDER — TODO
>
> This document describes the security architecture, policies, and procedures
> for the Wellfond BMS platform.

## Security Architecture

- **BFF Pattern:** Next.js proxy with HttpOnly cookies, zero JWT in browser
- **Session Auth:** Redis-backed sessions with 15-min access / 7-day refresh
- **CSRF Protection:** HttpOnly CSRF cookie with token rotation
- **Entity Scoping:** Multi-tenant data isolation at queryset level
- **PDPA:** Hard consent filtering, no override path

## TODO

- [ ] Credential rotation procedures
- [ ] Vulnerability disclosure policy
- [ ] Penetration test findings and remediation
- [ ] Data classification matrix
- [ ] Incident response contacts
- [ ] Compliance certification status (SOC 2, ISO 27001)