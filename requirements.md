# Wellfond BMS — Product Requirements Document | CONFIDENTIAL

WELLFOND PETS HOLDINGS PTE LTD Breeding Management System Product Requirements Document Version 1.0 April 2026 CONFIDENTIAL Prepared for internal development use only

# 1. Executive Summary

Wellfond Pets Holdings Pte Ltd (DB000065X) operates three business entities — Holdings (breeding farm), Katong (retail + import), and Thomson (retail) — managing 483 active breeding dogs across multiple kennel units in Singapore. The current workflow relies entirely on Google Sheets, WhatsApp, and manual paperwork, creating significant operational risk, compliance exposure, and staff inefficiency. This document defines the complete requirements for the Wellfond Breeding Management System (BMS) — a purpose-built web application to replace all Google Sheets workflows. The BMS will consolidate dog records, breeding management, ground staff logging, sales agreements, NParks compliance reporting, customer marketing, and finance exports into a single unified platform.

| Item | Detail |
|:---|:---|
| Project Name | Wellfond Breeding Management System (BMS) |
| Client | Wellfond Pets Holdings Pte Ltd |
| Licence No. | DB000065X |
| Entities | Holdings · Katong · Thomson |
| Active Dogs | 483 breeding dogs |
| Staff Users | ~15 staff across 5 access tiers |
| Document Version | 1.0 — April 2026 |
| Status | Pre-development — design complete, ready to build |

# 2. Business Context & Problem Statement

## 2.1 Current State

The business currently manages all breeding operations through Google Sheets, with the following pain points:

*   No centralised dog records — data spread across multiple spreadsheets with no access control
*   NParks compliance reports generated manually each month — error-prone and time-consuming
*   Sales agreements produced in Word documents, signed on paper, stored physically
*   Ground staff log observations via WhatsApp — no structured data capture
*   No genetics tracking — COI calculations and farm saturation done manually or not at all
*   Customer database maintained in a separate Google Sheet — no integration with sales
*   No vaccine tracking automation — overdue notices sent manually
*   AVS pet licence transfers tracked informally with high risk of missed follow-up

## 2.2 Desired State

A single web application accessible by all staff from desktop and mobile, with:

*   Centralised dog records with full health, breeding, and genetics history
*   Automated NParks report generation — one click to produce compliant Excel exports
*   Digital sales agreements with e-signature, PDF generation, and AVS transfer tracking
*   Mobile-first ground staff interface for logging daily observations
*   Mate checker with COI and farm saturation scoring to guide breeding decisions
*   Customer database with segmented email and WhatsApp marketing capability
*   Role-based access so each staff member only sees what they need

# 3. Technical Architecture

## 3.1 Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| Frontend | Next.js + TypeScript | Web application deployed to Vercel |
| Database | Supabase (PostgreSQL) | Singapore region · RLS policies · real-time |
| File Storage | Cloudflare R2 | Dog photos, media, signed PDFs |
| Email | Resend API | Sales agreements, marketing blasts, reminders |
| WhatsApp | WhatsApp Business API | Marketing blasts, agreement delivery |
| AI | Anthropic Claude API | Vaccine card photo extraction |
| Authentication | Supabase Auth | Role-based access control |
| Deployment | Vercel | Frontend · automatic CI/CD from GitHub |

## 3.2 Database

The database schema (wellfond_schema_v2.sql) is already defined with 19 tables, Row Level Security policies, helper views, and pre-seeded entity data. Key tables include:

*   dogs — master record for all 483 breeding dogs
*   breeding_records — mating logs with sire1_id and sire2_id for AVS dual-sire support
*   litters — whelping records linked to breeding events
*   puppies — individual pup records with confirmed_sire and paternity_method fields
*   health_records — vet visits, treatments, observations
*   vaccinations — vaccine history with due date tracking
*   users — staff accounts with role assignments
*   entities — Holdings, Katong, Thomson pre-seeded
*   sales_agreements — B2C, B2B, and rehoming agreement records
*   customers — buyer database with PDPA consent tracking

# 4. User Roles & Access

The system supports five access tiers with role-based permissions enforced at both the application and database (RLS) level.

| Role | Who | Key Access |
|:---|:---|:---|
| Management / Admin | Owners, senior management | Full access to all modules, all entities, T&C settings, user management |
| Admin | Office admin staff | All dog records, breeding, sales, NParks, finance — no user management |
| Sales Staff | Sales team | Dog profiles (read-only breeding), sales agreements, customer database, marketing |
| Ground Staff | Kennel workers | Mobile log interface only — chip lookup, 7 log types, photo upload |
| Vet / External | Visiting vets | Health records and vaccination logs only — read-only dog profiles |

# 5. Module Specifications

## 5.1 Master Dog List

The central directory of all 483 breeding dogs across all entities.

### Features

*   Partial microchip search — type last 4–6 digits, full chip, or name — live dropdown results
*   Alert cards at top: vaccines overdue, rehome overdue (6yr+), in heat, 8-week litters, nursing flags, NParks countdown — all with trend indicators vs prior period
*   Filter bar: status chips (active, retired, rehomed) + gender toggle + breed dropdown + entity dropdown — all filters work simultaneously
*   Table columns: chip, name/breed, gender, age with colour dot, unit, last event, dam/sire chips, DNA badge, vaccine due date
*   WhatsApp Copy button per row — generates pre-formatted message for buyers with full dog details; entity-aware (Holdings includes mating/birth data, Katong/Thomson omits breeding data)
*   Clicking any row opens the Dog Profile drawer with 7 tabs
*   CSV export of filtered results

### Business Rules

*   Dogs with age 5–6yr shown with yellow flag, 6yr+ shown with red flag for rehome planning
*   Chip search scans across all units — staff are not restricted to their unit
*   Vaccine due dates calculated automatically from vaccination records

## 5.2 Dog Profile

Full detail view for each dog, accessed by clicking any row in the Master List.

### Profile Tabs

*   Overview — hero strip with name, chip, age dot, status badges, 4 quick stats, action buttons
*   Health & Vaccines — full vaccination history with dates, vet names, due dates, status badges; vet visit log
*   Breeding — heat cycle history, mating records with sire(s), Draminski readings, mating window calculations
*   Litters & Pups — per-litter collapsible sections; per-pup table with chip, sex, birth weight, confirmed sire, paternity method (Visual/DNA/Unconfirmed), health, buyer
*   Media — category-tagged photo/video grid; customer-visible toggle per item
*   Genetics — COI history, farm saturation per sire, DNA test results
*   Activity — full chronological log of all events for this dog

### Role Restrictions

*   Sales Staff and Ground Staff: Breeding, Litters, and Genetics tabs locked (shown with lock icon)
*   All roles can view Health and Overview tabs

## 5.3 Ground Staff Mobile Interface

Phone-optimised interface for kennel workers. Accessible from any device. Designed for outdoor use with high contrast and large tap targets.

### Dog Lookup

*   Search by last 4–6 chip digits, full chip number, or dog name
*   Results from ALL units — no unit restriction (staff rotate between units)
*   Results show name, breed, unit badge, in-heat status
*   Camera scan button to scan microchip barcode

### Log Actions (7 types)

*   In Heat — date/time auto-captured · Draminski reading entry with live interpretation and trend chart · mating window slider (auto-adjusts based on Draminski) · notes · overdue alert if >42 days since last heat
*   Mated — sire chip search (partial chip/name) · Natural or Assisted toggle · optional Sire #2 for AVS dual-sire · date/time auto-captured · on save: expected whelp date (63 days) shown + Draminski reminder for next day
*   Whelped — Natural/C-Section toggle · alive count + stillborn count · per-pup gender entry (tap M/F) · on save: management notified + draft litter record created for admin to complete
*   Health Obs — category selection (Limping/Skin/Not eating/Eye-ear/Injury/Other) · free text description · optional temperature and weight fields · photo required · notifies management on save
*   Weight Check — dam weight in kg · date auto-captured · weight history bar chart shown for reference · no alert triggered
*   Nursing Flag — split into Mum problems and Pup problems sections · pup number selector for pup issues · photo required · serious flags (no milk/rejecting pup/pup not feeding) notify management immediately · other flags logged silently
*   Not Ready — one tap · optional notes · EDD (estimated next heat date) picker · management reminder set 1 week before EDD

### Draminski DOD2 Integration

*   Staff enter the raw number shown on the device display via a large numpad
*   App interprets reading against that dog's own historical readings (per-dog, not global thresholds)
*   Interpretation: <200 early · 200-400 rising (daily readings) · 400+ rising fast · peak = highest recorded for this dog · post-peak drop = MATE NOW
*   7-day trend chart shows historical readings with today's reading plotted live
*   Mating window slider auto-adjusts based on interpretation

## 5.4 Mate Checker

Genetics tool to evaluate proposed mating pairs before committing.

### Inputs

*   Dam selection (chip/name search)
*   Sire #1 (chip/name search)
*   Optional Sire #2 for AVS dual-sire — runs as a separate check

### Outputs

*   Pairing COI % — coefficient of inbreeding between proposed sire and dam — with bar gauge and shared ancestors list
*   Farm Saturation % — what percentage of active farm dogs share ancestry with the proposed sire

### Thresholds

| Score | COI | Farm Saturation | Verdict |
|:---|:---|:---|:---|
| Safe | Below 6.25% | Below 15% | Green — proceed |
| Caution | 6.25% – 12.5% | 15% – 30% | Yellow — review |
| High Risk | Above 12.5% | Above 30% | Red — not recommended |

### Override

*   Admin can always override any verdict — warning never hard-blocks a mating
*   Override requires reason selection + notes and is logged permanently with staff name and timestamp
*   Override log visible in check history table

### Business Rules

*   COI runs only between proposed sire and dam — not against offspring
*   2-sire data feeds NParks mating sheet and monthly inbreeding audit only — does not affect mate checker strictness

## 5.5 Sales Agreements

Three agreement types, each with a 5-step wizard flow and document preview panel.

### B2C — Individual Buyer

*   Step 1: Dog selection via chip search · entity selector · collection date
*   Step 2: Buyer details — name, NRIC, DOB, mobile, email, full address, housing type (HDB/Condo/Landed/Other) · HDB warning shown if applicable · PDPA opt-in checkbox
*   Step 3: Dog health disclosure — full editable dog details card (DOB, chip, sire, dam, colour) · editable vaccination record rows (vaccine name, date given, vet, due date, add/remove rows) · editable health check fields · seller's remarks field (printed on agreement) · buyer counter-signature to acknowledge dog condition
*   Step 4: Pricing — sale price (GST inclusive) · deposit (non-refundable — prominently displayed) · balance auto-calculated · GST component extracted (9/109 formula) · payment method · deposit non-refundable and no medical bills highlighted as mandatory notices
*   Step 5: T&Cs and Signature — standard T&Cs shown read-only (editable in Settings by admin) · special conditions per deal · signature method: In Person (finger on screen) / Remote (link to buyer device) / Paper Document (checklist + mark as signed manually)
*   Step 6: Send — signed PDF generated and sent as email attachment + WhatsApp file · AVS pet licence transfer link auto-sent to buyer · 3-day follow-up reminder if not transferred

### B2B — Pet Shop / Outlet

*   Multiple dogs as editable line items (tap price to edit) · subtotal, GST component, and invoice total auto-update
*   Business details: company name, UEN, AVS pet shop licence, GST status, contact person
*   Payment terms: Full Upfront (new buyers) or Credit Terms (existing partners — configurable credit period and due date)
*   Standard T&Cs + special conditions + dual counter-signatures (Wellfond rep + buyer rep)
*   Combined PDF (invoice + agreement in one file) sent via email + WhatsApp
*   AVS transfer tracked per dog with 3-day follow-up

### Rehoming — Shelter / VFA / Individual

*   Organisation type selection: Shelter / VFA / Individual
*   No price field — transfer form only, price auto-set to $0
*   Reason for rehoming dropdown (age policy, health, behaviour, other)
*   Transfer conditions free text
*   Dual signatures
*   Transfer form PDF sent (no invoice) via email + WhatsApp
*   NParks breeding dog movement record updated automatically
*   AVS transfer tracked with 3-day follow-up

### T&C Settings

*   Admin-only settings panel — separate tab in the Sales Agreement module
*   Three editable T&C templates: B2C, B2B, Rehoming
*   Changes apply to all future agreements immediately
*   Existing signed agreements are not affected
*   All staff can view T&Cs in the agreement flow (read-only)

## 5.6 NParks Compliance Reports

Automated generation of all 5 monthly NParks submission documents for each entity.

### Documents

| Document | Holdings | Katong | Thomson |
|:---|:---|:---|:---|
| Mating Sheet | Yes | Yes | N/A |
| Retail Puppy Movement | Yes | Yes | Yes |
| Vet Treatments | Yes | Yes | Yes |
| Puppies Bred In-House | Yes | Yes | N/A |
| Breeding Dog Movement | Yes | Yes | N/A |

### Workflow

*   Select entity (Holdings / Katong / Thomson)
*   Select month
*   System auto-generates all applicable documents from live database data
*   Quality check shown — errors (non-blocking) and warnings highlighted
*   Preview table displayed
*   Download as Excel — immediate, no CSV option
*   Mark as submitted button

### Business Rules

*   Farm details (name, licence DB000065X, address) pre-filled permanently — never need re-entry
*   Mating sheet always shows both sire columns for dual-sire AVS compliance
*   Generate All button packages all applicable documents for that entity in one action
*   "Mark submitted" button records submission date and locks that month's report

## 5.7 Customer Database & Marketing

Centralised customer database with segmented mass marketing capability.

### Customer Records

*   Auto-populated from completed B2C sales agreements
*   CSV import from Google Sheets — column mapping screen on upload, duplicate detection by mobile number
*   Manual add form
*   Admin-only access for all functions

### Customer List View

*   Sortable columns: customer name, breed, entity, last purchase date, PDPA status
*   Filters: search (name/email/mobile), breed, entity, PDPA status, date range — any combination
*   Expandable row → full profile: personal details, purchase history, communications log, notes
*   PDPA status editable inline — click badge in table or toggle in expanded profile · opt-out requires confirmation · stats bar updates live

### Mass Marketing

*   Select recipients: all filtered customers OR manually selected rows
*   Recipient summary shows: total selected, PDPA opted in, excluded count with warning
*   Channel options: Email (Resend API) · WhatsApp (WA Business API) · Both
*   Compose window with subject line (email), message body, merge tags ({{name}}, {{breed}}, {{entity}}, {{mobile}})
*   Send progress bar with live count · success confirmation
*   All sends logged in each customer's communication history
*   PDPA enforced automatically — non-opted customers excluded with warning, cannot be overridden

## 5.8 Dashboard

Role-aware daily command centre — the first screen staff see on login.

### Management / Admin View

*   NParks countdown card (days to month-end submission, pending records flagged) — blue gradient
*   Quick Mate Checker widget — run a check without navigating away
*   7 alert cards with trend indicators: vaccines overdue, rehome overdue, in heat, 8-week litters, nursing flags, unsigned agreements, missing parent microchips
*   Vaccine overdue list with dog names, chips, and Log Now buttons
*   Active nursing flags with immediate visibility
*   Age alerts — dogs approaching or past rehome age (5yr+ and 6yr+)
*   Recent activity feed — last 10 ground staff and admin logs
*   Month-to-date revenue by entity with bar chart
*   Upcoming collections this week with confirmation status

### Ground Staff View

*   Alert banner if active nursing flags exist in any unit
*   Large chip scanner hero — immediate dog lookup on open
*   Unit summary stats (in heat, nursing flags, litters, pups, vaccine due)
*   Quick log buttons for the selected dog
*   My recent logs (last 5 entries)

### Sales Staff View

*   Same structure as management but without: revenue, NParks, age alerts, mate checker
*   Unsigned agreements and pending AVS transfers shown prominently

## 5.9 Finance Exports

Financial reporting and export module (to be detailed in a subsequent sprint).

*   P&L by entity — monthly and YTD
*   GST report — sales and GST components by entity (Holdings 9%, Katong 9%, Thomson 0%)
*   Sales summary — by breed, by entity, by period
*   Intercompany transfers
*   Export to Excel

# 6. Key Business Rules

## 6.1 GST

*   All prices are GST-inclusive
*   GST component extracted using 9/109 formula
*   Holdings: 9% GST · Katong: 9% GST · Thomson: No GST

## 6.2 Two-Sire System (AVS Compliance)

*   `breeding_records` table stores `sire1_id` and `sire2_id`
*   `puppies` table stores `confirmed_sire` (1 or 2) and `paternity_method` (visual/dna/unconfirmed)
*   Paternity determined by visual identification (primary) or EasyDNA SG DNA test
*   NParks mating sheet always shows both sire columns
*   Mate checker COI runs sire × dam only — 2-sire history does not affect strictness

## 6.3 Rehoming Policy

*   Dogs aged 6 years and above are flagged as overdue for rehoming
*   Dogs aged 5–6 years are flagged for planning
*   Rehoming logged in NParks breeding dog movement report automatically

## 6.4 AVS Licence Transfer

*   Required for all sales (B2C, B2B) and rehoming
*   Link auto-sent to buyer on agreement signing
*   Automatic reminder sent after 3 days if not completed
*   Staff notified to follow up manually if reminder sent

## 6.5 PDPA

*   Collected at point of sale via checkbox in sales agreement
*   Opt-in customers: can receive all marketing communications
*   Opt-out customers: stored in database but excluded from all blasts automatically
*   PDPA status editable by admin at any time with confirmation prompt on opt-out

## 6.6 Mate Checker Overrides

*   Override is always available — system never hard-blocks a mating
*   Override requires: reason selection + free text notes
*   Logged permanently with staff name, timestamp, and reason
*   Visible in check history table for audit purposes

# 7. Non-Functional Requirements

| Requirement | Target |
|:---|:---|
| Availability | 99.5% uptime · Vercel managed hosting |
| Performance | Page load < 2 seconds on standard Singapore broadband |
| Mobile | Ground staff interface fully functional on iPhone and Android · minimum 390px viewport |
| Data region | Supabase Singapore region — all data stays in Singapore |
| Security | RLS at database level · HTTPS only · Supabase Auth · role-based access enforced server-side |
| Backup | Daily automated backups via Supabase · point-in-time recovery |
| Browser support | Chrome, Safari, Edge — latest 2 versions |
| File storage | Cloudflare R2 · max 500MB per upload · JPG/PNG/MP4/MOV accepted |
| Audit trail | All data changes timestamped with user ID · overrides permanently logged |
| Offline | Not required — online connection assumed for all functions |

# 7a. Mobile Requirements

All roles require mobile access. The application must be fully responsive — the same screens adapt to mobile viewports rather than maintaining separate mobile views.

## 7a.1 Approach

*   Responsive design — single codebase, screens adapt to all screen sizes
*   Sidebar collapses to a bottom navigation bar on mobile (Home / Dogs / Sales / Reports / More)
*   Tables reflow to card-based layouts on small screens
*   All forms remain fully functional on mobile
*   Touch targets minimum 44px × 44px throughout
*   PWA-ready — installable on iPhone and Android home screen

## 7a.2 Role-Specific Mobile Priorities

| Role | Primary Mobile Use | Priority |
|:---|:---|:---|
| Ground Staff | Chip lookup · 7 log types · photo upload · nursing flags | Critical — already built as mobile-first |
| Management / Admin | Dashboard alerts · approve overrides · view reports | High |
| Sales Staff | View agreements · send via WhatsApp · customer lookup | High |
| Admin | Dog profiles · health records · litter records | Medium |

## 7a.3 Responsive Breakpoints

| Breakpoint | Width | Layout |
|:---|:---|:---|
| Mobile | < 768px | Bottom nav · stacked cards · full-width forms |
| Tablet | 768px – 1024px | Collapsible sidebar · simplified tables |
| Desktop | > 1024px | Full sidebar · all columns visible |

# 8. Design System

| Element | Specification |
|:---|:---|
| Theme | Tangerine Sky — light blue background with teal-navy sidebar |
| Primary Font | Figtree — 14px base size · no slashed zero |
| Monospace | Figtree (replaces JetBrains Mono to eliminate dotted zero) |
| Background | #DDEEFF (light blue) |
| Sidebar | #E8F4FF (very light blue-white) |
| Card Background | #FFFFFF (white) |
| Primary Accent | #F97316 (tangerine orange) |
| Secondary Accent | #0891B2 (teal) |
| Border Color | #C0D8EE |
| Text Primary | #0D2030 (dark navy) |
| Text Muted | #4A7A94 |
| Success | #4EAD72 |
| Warning | #D4920A |
| Error | #D94040 |
| Active Nav Item | Orange background (#F97316) · white text |
| Role Bar | #FFF0E6 with orange border |

# 9. Data Migration

## 9.1 Dog Master CSV

483 active breeding dogs to be imported from master CSV. Mapping:

| CSV Column | Database Field | Notes |
|:---|:---|:---|
| Microchip | dogs.microchip | Primary identifier — must be unique |
| Name | dogs.name | |
| Breed | dogs.breed | Mapped to breed lookup table |
| Date of Birth | dogs.date_of_birth | ISO 8601 format |
| Gender | dogs.gender | M or F |
| Colour | dogs.colour | |
| Unit/Pen | dogs.unit | e.g. H#01-13 |
| Entity | dogs.entity_id | Mapped to entities table |
| Status | dogs.status | active / retired / rehomed / deceased |
| Dam Chip | dogs.dam_id | Foreign key lookup by chip |
| Sire Chip | dogs.sire_id | Foreign key lookup by chip |

## 9.2 Customer Import

*   Existing customer data imported via CSV upload from Google Sheets
*   Column mapping screen presented on upload
*   Duplicate detection by mobile number
*   PDPA consent status imported from CSV

## 9.3 Historical Litter Data (5 Years)

Five years of historical litter records should be imported to maximise the accuracy of the Mate Checker genetics tools. COI calculations require ancestry data going back at least 3-5 generations to produce meaningful inbreeding coefficients.

### Why This Matters

*   COI accuracy — without historical litters, Mate Checker COI scores will be incomplete or zero for many pairs
*   Farm saturation accuracy — historical sire usage improves saturation scoring
*   Full breeding history per dam — buyers and management see complete reproductive records
*   NParks historical records available in system if audited

### Import Options

| Data Available | What to Import | Benefit |
|:---|:---|:---|
| Full litter records with pup chips | Litter record + individual pup records linked to chip | Full COI and complete dog profiles for all historical pups |
| Litter records without pup chips | Litter-level only: dam, sire, whelp date, pup count | COI and farm saturation still improved significantly |
| Partial records | Import what exists, flag gaps for manual completion | Best available accuracy with room to fill gaps |

### Import Mapping

| Field | Required | Notes |
|:---|:---|:---|
| Dam microchip | Yes | Must match existing dog record |
| Sire 1 microchip | Yes | Must match existing dog record |
| Sire 2 microchip | No | For AVS dual-sire litters |
| Whelp date | Yes | ISO 8601 format |
| Delivery method | No | Natural or C-Section |
| Alive count | No | |
| Stillborn count | No | |
| Pup microchip | No | Creates individual dog record if provided |
| Pup gender | No | M or F |
| Pup colour | No | |

Recommendation: import all available data even if incomplete. The system will flag missing fields and allow admin to fill gaps progressively.

# 10. Development Phases

| Phase | Scope | Priority |
|:---|:---|:---|
| Phase 1 — Foundation | Supabase setup · CSV import (483 dogs + 5yr litter history) · Master List · Dog Profile · Auth & roles | Critical |
| Phase 2 — Ground Operations | Ground Staff mobile interface · All 7 log types · Draminski integration · Nursing flags | High |
| Phase 3 — Breeding & Genetics | Mate Checker · COI calculation · Farm saturation · Breeding records · Litters | High |
| Phase 4 — Sales | Sales Agreements (B2C/B2B/Rehoming) · PDF generation · E-signature · AVS tracking | High |
| Phase 5 — Compliance | NParks report generation · Excel export · Monthly submission tracking | High |
| Phase 6 — Customers & Marketing | Customer database · CSV import · Segmentation · Email/WhatsApp blast via API | Medium |
| Phase 7 — Finance | Finance exports · P&L · GST report · Sales summary | Medium |
| Phase 8 — Dashboard | Role-aware dashboard · Alert cards · Activity feed · Revenue charts | Medium |

# 11. Design Mockups

Interactive HTML mockups have been produced for all major screens. These serve as the definitive visual specification for development.

| Screen | File | Status |
|:---|:---|:---|
| Dashboard | wellfond_dashboard.html | Complete |
| Master List | wellfond_masterlist_v3.html | Complete |
| Dog Profile | wellfond_dogprofile_v2.html | Complete |
| Mate Checker | wellfond_matechecker.html | Complete |
| NParks Reports | wellfond_nparks_v2.html | Complete |
| Ground Staff Mobile | wellfond_groundstaff_v2.html | Complete |
| Ground Staff — In Heat (Draminski) | wellfond_inheat_draminski.html | Complete |
| Ground Staff — Mated | wellfond_mated_log.html | Complete |
| Ground Staff — Whelped | wellfond_whelped_log.html | Complete |
| Ground Staff — Health Obs | wellfond_healthobs_log.html | Complete |
| Ground Staff — Weight / Nursing / Not Ready | wellfond_remaining_logs.html | Complete |
| Sales Agreement (B2C / B2B / Rehoming) | wellfond_sales_agreement.html | Complete |
| Customer Database & Marketing | wellfond_customers.html | Complete |
| Finance Exports | — | Pending |

# 12. Appendix

## 12.1 Reference Files

*   WPH_App_Project_Summary.docx — original project brief
*   wellfond_schema_v2.sql — complete PostgreSQL schema with 19 tables, RLS policies, helper views, and pre-seeded entity data

## 12.2 External Dependencies

*   Resend account — email delivery API (resend.com)
*   WhatsApp Business API — approved WhatsApp Business account required
*   Anthropic API key — for vaccine card AI extraction
*   Cloudflare R2 bucket — media storage
*   Vercel account — frontend deployment
*   Supabase project — Singapore region, already planned

## 12.3 Glossary

| Term | Definition |
|:---|:---|
| COI | Coefficient of Inbreeding — probability that two alleles at a given locus are identical by descent |
| Farm Saturation | Percentage of active farm dogs that share ancestry with a proposed sire |
| AVS | Animal & Veterinary Service — Singapore government body managing pet licensing |
| NParks | National Parks Board — regulatory body overseeing licensed animal facilities |
| PDPA | Personal Data Protection Act — Singapore data privacy law governing marketing consent |
| Draminski DOD2 | Electronic dog ovulation detector measuring vaginal mucus resistance in units |
| RLS | Row Level Security — database-level access control in Supabase/PostgreSQL |
| EDD | Estimated Due Date — predicted next heat date for a breeding dog |
| GST | Goods and Services Tax — 9% in Singapore (Thomson entity exempt) |
| VFA | Voluntary Welfare Organisation for Animals — shelter/rescue organisation type |

Wellfond Pets Holdings Pte Ltd | DB000065X Page

Wellfond BMS — Product Requirements Document | CONFIDENTIAL

---

The document has been converted to markdown format, preserving all the original content and formatting, including headers, lists, and tables.

