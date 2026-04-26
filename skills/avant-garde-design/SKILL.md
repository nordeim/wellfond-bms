---
name: avant-garde-design
description: |
  Elite web design skill for producing distinctive, production-grade frontend interfaces.
  Use when: (1) Building new web UI from scratch, (2) Creating luxury/premium brand experiences,
  (3) Designing landing pages, marketing sites, or product showcases, (4) Reviewing UI designs for Anti-Generic compliance,
  (5) Establishing design direction for a project, (6) Migrating from Tailwind v3 to v4,
  (7) Debugging mobile navigation issues, (8) User asks for "avant-garde", "distinctive", "non-generic", "luxury", or "premium" design.
  Triggers on phrases like "create a beautiful website", "design a landing page", "build a luxury UI",
  "make it distinctive", "avoid generic design", "mobile nav not working", "tailwind v4 migration".
---

# Avant-Garde Web Design

Produce distinctive, production-grade frontend interfaces that reject generic "AI slop" aesthetics.

## Core Philosophy

**Anti-Generic Mandate:** Every interface must have a distinctive conceptual direction. Reject:
- Bootstrap-style predictable grids
- Safe "Inter/Roboto" pairings without typographical hierarchy
- Purple-gradient-on-white clichés
- Predictable card grids and hero sections
- The homogenized "AI slop" aesthetic

**Intentional Minimalism:** Whitespace is structural, not empty space. Every element earns its place through calculated purpose. If you cannot justify an element's existence, delete it.

---

## The 40-Minute Pre-Design Ritual

**Before any visual work, complete this process:**

### Step 1: Audience Psychographic Assessment (15 min)

Answer these four questions:

| Question | If Leans Toward... | Then Design For... |
|----------|-------------------|-------------------|
| What is their primary fear? | "Wasting money on bad decision" | **Institutional Clarity** (reduce risk, build trust) |
| | "Missing out on the next big thing" | **Dynamic Modernism** (amplify FOMO, create desire) |
| What decision-making style? | Rational, research-heavy | Provide data, comparisons, transparency |
| | Emotional, intuitive | Create visceral impact, aspirational imagery |
| Who do they trust? | Established institutions | Signal legacy, credentials, certifications |
| | Innovators, peers | Signal community, social proof, outcomes |
| Relationship with category? | New, needs education | Build confidence, explain clearly |
| | Experienced, seeking best | Differentiate, highlight premium |

### Step 2: Strategic Positioning (10 min)

Place your project on this matrix:

```
AUDIENCE: RISK-AVERSE          │  Q1: THE GUARDIAN          │  Q2: LEGACY INNOVATOR
                                │  (iTrust Academy)          │  (Harvard AI Program)
                                │  Perfect execution         │  Trusted + bold accents
                                │  of classic forms          │  
────────────────────────────────┼────────────────────────────
                                │  Q3: TRUSTWORTHY           │  Q4: THE VISIONARY
                                │  UPSTART                   │  
                                │  Modern + ultra-           │  Full commitment to
                                │  clear + trust signals     │  bold, experience-driven
                                │                            │  aesthetic
AUDIENCE: ASPIRATION-DRIVEN     
```

### Step 3: Anti-Generic Litmus Test (10 min)

For every major design decision, answer all three:

| Question | Purpose | Passing Answer |
|----------|---------|----------------|
| **Why?** | Tie element to strategy | "This exists because [specific user need/psychological state]" |
| **Only?** | Challenge defaults | "This is the only way because [unique constraint/opportunity]" |
| **Without?** | Enforce minimalism | "Without this, [core experience] would be diminished" |

### Step 4: Technical Commitment (5 min)

Based on your quadrant:

| Position | Must Have | Can Deprioritize |
|----------|-----------|------------------|
| **Institutional Clarity** | Lighthouse 95+, WCAG AAA, semantic HTML | Complex animations, WebGL |
| **Dynamic Modernism** | Expert animation, performance budgets, reduced-motion | Pixel-perfect legacy browsers |

---

## Aesthetic Direction Selection

Choose ONE direction. Execute with precision.

| Direction | Characteristics | When to Use |
|-----------|----------------|-------------|
| **Brutally Minimal** | Extreme whitespace, single focal point, near-monochrome | Premium services, art, architecture |
| **Editorial/Magazine** | Asymmetric layouts, bold headlines, grid breaks | Media, journalism, thought leadership |
| **Luxury/Refined** | Serif fonts, gold accents, subtle gradients | High-end retail, hospitality, finance |
| **Retro-Futuristic** | Neon, chrome, geometric patterns | Tech products, gaming, entertainment |
| **Organic/Natural** | Soft curves, earthy tones, fluid shapes | Wellness, sustainability, lifestyle |
| **Brutalist/Raw** | Exposed structure, monospace, high contrast | Developer tools, technical products |
| **Art Deco/Geometric** | Symmetry, gold/black, stepped forms | Luxury events, premium memberships |

---

## Design Implementation Patterns

### Typography System

| Strategy | Fonts | Best For |
|----------|-------|----------|
| **Single Family** | DM Sans only | Corporate, fast-loading, cohesive |
| **Display + Body** | Space Grotesk + Inter | Modern tech, personality + readability |
| **With Mono Labels** | Either + JetBrains Mono | Technical/data-heavy interfaces |

**H1 Scale:** 60-77px for impact. Line-height: 1.0-1.1 tight.

**Anti-Pattern:** Never use Inter/Roboto without distinct typographical hierarchy.

### Color Strategy

| Strategy | Palette | Psychology |
|----------|---------|------------|
| **Trust-Focused** | Single accent (orange/blue) + white | Authority, reliability |
| **Innovation-Focused** | Multi-accent + gradients | Energy, dynamism |
| **Premium** | Deep backgrounds, metallic accents | Exclusivity, sophistication |

**Implementation:**

```css
/* Trust-Focused (iTrust-inspired) */
--primary: #F27A1A;
--bg: #FFFFFF;
--text: #111827;
--text-secondary: #6B7280;

/* Innovation-Focused (AI Academy-inspired) */
--primary: #4F46E5;
--bg: #FAFAF9;
--accent-cyan: #06B6D4;
--accent-emerald: #10B981;
--accent-amber: #F59E0B;
```

### Layout Patterns

| Element | Institutional Clarity | Dynamic Modernism |
|---------|----------------------|-------------------|
| **Max Width** | 1140px | 1140px (same constraint) |
| **Grid** | Strict 12-column, symmetric | Flexible, asymmetric |
| **Hero** | Text-focused, centered | Two-column, floating elements |
| **Whitespace** | Structural separator | Dramatic isolation |
| **Cards** | Subtle shadows, borders | Colored tops, illustrations |

---

## Tailwind CSS v4 (CSS-First Architecture)

**CRITICAL:** No `tailwind.config.js` — use CSS-only configuration.

```css
@import "tailwindcss";

@theme {
  --color-primary: oklch(0.84 0.18 117.33);
  --font-display: "Space Grotesk", sans-serif;
}
```

**Key Changes from v3:**
- `bg-gradient-to-r` → `bg-linear-to-r`
- `bg-opacity-50` → `bg-red-500/50`
- `bg-[--color]` → `bg-(--color)`
- `shadow-sm` → `shadow-xs`

**References:**
- [`tailwind-v4-migration.md`](references/tailwind-v4-migration.md) — Setup, utility mappings, syntax changes
- [`tailwind-v4-pitfalls.md`](references/tailwind-v4-pitfalls.md) — Common pitfalls, performance, browser requirements

---

## Mobile Navigation Patterns

### Non-Negotiable Guardrails

1. **Viewport meta required:** `<meta name="viewport" content="width=device-width, initial-scale=1">`
2. **Never destroy nav without substitution** — Add mobile trigger + overlay
3. **Symmetrical breakpoints:** Desktop `hidden md:flex`, Mobile `md:hidden`
4. **Semantic controls:** Use `<button>`, not `<div onClick>`
5. **Overlay positioning:** `position: fixed`, `overflow-y: auto`

### Root-Cause Taxonomy (Classes A-H)

| Class | Symptom | Fix |
|-------|---------|-----|
| **A** | No visible nav | Add mobile trigger + overlay |
| **B** | Hidden by opacity | Verify state toggling |
| **C** | Clipped by overflow | Use `position: fixed` |
| **D** | Behind another layer | Check z-index scale |
| **E** | Breakpoint mismatch | Verify viewport meta |
| **F** | JavaScript failure | Guard selectors, check console |
| **G** | Keyboard inaccessible | Use real `<button>` elements |
| **H** | Click-outside race | Exclude trigger from handler |

**References:**
- [`mobile-navigation.md`](references/mobile-navigation.md) — Implementation patterns
- [`mobile-nav-debugging.md`](references/mobile-nav-debugging.md) — Debugging workflow

---

## Library Discipline (CRITICAL)

**If a UI library exists (Shadcn, Radix, MUI), USE IT.**

Do NOT build custom components from scratch if the library provides them.
Do NOT pollute codebase with redundant CSS.

**Exception:** You may wrap or style library components to achieve the vision, but the underlying primitive must come from the library.

### Recommended Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | Next.js 14+ | App Router, Server Components |
| Styling | Tailwind CSS 4.0 | CSS-first with @theme |
| Components | Shadcn UI | Radix primitives + Tailwind |
| Animation | Framer Motion | Reduced-motion support required |
| Fonts | Google Fonts | Self-hosted for performance |

---

## Verification Checklist

Before marking any design complete:

```
□ Does every element have a defensible "why"?
□ Is typography intentional, not default?
□ Does color serve function, not decoration?
□ Is whitespace structural, not accidental?
□ Would this work without color?
□ Is animation purposeful or decorative?
□ Does this match audience psychology?
□ Are we adapting principles, not copying patterns?
□ Would this feel dated in 3 years?
□ Does this avoid "AI slop" aesthetics?
```

**Scoring:** 10+ passes = Strong Anti-Generic. 7-9 = Acceptable. <7 = Redesign.

---

## Patterns to Steal

| Pattern | Source | Implementation |
|---------|--------|----------------|
| Exam domain transparency table | iTrust | Percentage + day mapping for credibility |
| FAANG logo trust bar | AI Academy | Grayscale → color on hover |
| Dark section for premium | AI Academy | Visual rhythm break for pricing |
| Status pills (AVAILABLE/FILLING) | Both | Color-coded availability indicators |
| Strikethrough + urgency pricing | AI Academy | Original price + discounted + spots remaining |
| Single font discipline | iTrust | DM Sans throughout, mono for labels only |
| Two-font display system | AI Academy | Space Grotesk headlines + Inter body |
| Stats in hero (4 metrics) | Both | Large numbers, small labels |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails |
|--------------|--------------|
| Emoji icons in enterprise context | Feels informal, undermines credibility |
| Generic stock photography | Undermines distinctiveness |
| Purple-gradient-on-white | The ultimate "AI slop" signal |
| Predictable card grids | Zero memorability |
| Inter/Roboto without hierarchy | Safe = forgettable |
| Hidden pricing on B2C | Creates friction, reduces trust |
| Dark mode without contrast verification | Accessibility failure |

---

## Accessibility Requirements (WCAG AAA)

- **Contrast:** 4.5:1 for normal text, 3:1 for large text
- **Focus states:** Visible ring on all interactive elements
- **Animation:** Respect `prefers-reduced-motion`
- **Images:** Meaningful alt text (empty string for decorative)
- **Forms:** Labels, autocomplete, error states
- **Semantic HTML:** Use elements for their purpose

---

## Reference Files

| File | When to Read |
|------|--------------|
| [`intentionality-compass.md`](references/intentionality-compass.md) | Always — Strategic positioning framework |
| [`anti-generic-checklist.md`](references/anti-generic-checklist.md) | Design review — Forbidden patterns & prompts |
| [`color-typography-specs.md`](references/color-typography-specs.md) | Color/typography decisions |
| [`patterns-catalog.md`](references/patterns-catalog.md) | UI patterns to steal |
| [`tech-commitments.md`](references/tech-commitments.md) | Technical requirements by position |
| [`tailwind-v4-migration.md`](references/tailwind-v4-migration.md) | v3→v4 migration or v4 setup |
| [`tailwind-v4-pitfalls.md`](references/tailwind-v4-pitfalls.md) | Debugging v4 issues |
| [`mobile-navigation.md`](references/mobile-navigation.md) | Nav implementation |
| [`mobile-nav-debugging.md`](references/mobile-nav-debugging.md) | Nav debugging |

---

## Related Skills

| Skill | When to Use |
|-------|-------------|
| `nextjs-tailwind-v4-luxe` | Full-stack Next.js implementation |
| `aesthetic` | Deep design analysis, inspiration workflows |
| `code-review` | UI code review protocols |
| `ui-styling` | Shadcn/ui implementation details |

---

> Technical excellence requires both rigorous implementation and distinctive design.
