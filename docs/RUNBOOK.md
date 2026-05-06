# RUNBOOK.md

> **Status:** PLACEHOLDER — TODO
>
> This document will contain operational runbooks for the Wellfond BMS platform,
> including startup/shutdown procedures, health check monitoring, backup/restore,
> and incident response flows.

## Quick Reference

| Operation | Command |
|-----------|---------|
| Start all services | `docker compose up -d` |
| Check service health | `docker compose ps` |
| View logs | `docker compose logs -f [service]` |
| Restart service | `docker compose restart [service]` |

## TODO

- [ ] Detailed startup/shutdown procedures
- [ ] Backup and restore procedures
- [ ] Redis failover procedures
- [ ] Database maintenance (VACUUM, reindex)
- [ ] Certificate renewal
- [ ] Incident response playbook