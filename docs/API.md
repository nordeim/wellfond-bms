# API.md

> **Status:** PLACEHOLDER — TODO
>
> This document provides the API reference for the Wellfond BMS platform.
> All endpoints are accessed through the Next.js BFF proxy at `/api/proxy/[...path]`.

## Base URL

- **Development:** `http://localhost:3000/api/proxy`
- **Production:** `https://[domain]/api/proxy`

## Authentication

All endpoints require HttpOnly session cookie. The BFF proxy handles
cookie forwarding automatically. No JWT tokens are exposed to the browser.

## API Sections

| Section | Path Prefix | Description |
|---------|-------------|-------------|
| Auth | `/auth` | Login, logout, session refresh |
| Users | `/users` | User management |
| Dogs | `/dogs` | Dog CRUD, health records, vaccinations |
| Operations | `/operations` | Ground logs, SSE alerts |
| Breeding | `/breeding` | COI, saturation, litters |
| Sales | `/sales` | Agreements, AVS transfers |
| Compliance | `/compliance` | NParks, GST, PDPA |
| Customers | `/customers` | CRM, segments, blasts |
| Finance | `/finance` | P&L, GST reports, transactions |

## TODO

- [ ] Full endpoint documentation with request/response schemas
- [ ] Authentication flow diagrams
- [ ] Rate limiting details
- [ ] Error code reference
- [ ] WebSocket/SSE documentation