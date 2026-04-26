# Color & Typography Specifications

Validated specifications from comparative analysis of iTrust Academy and AI Academy.

---

## Color Systems

### Trust-Focused Palette (iTrust-inspired)

```css
:root {
  /* Primary Brand */
  --color-primary: #F27A1A;
  --color-primary-subtle: rgba(242, 122, 26, 0.08);

  /* Backgrounds */
  --color-bg-primary: #FFFFFF;
  --color-bg-secondary: #F8F9FA;

  /* Text */
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;

  /* Status */
  --color-status-green: #059669;

  /* Vendor Accents (for categorization) */
  --color-vendor-1: #2BBCB4; /* SolarWinds */
  --color-vendor-2: #3B82F6; /* Securden */
  --color-vendor-3: #7C3AED; /* Quest */
}
```

**Psychology:** Single accent signals authority. White background = clarity. Orange = energy without frivolity.

### Innovation-Focused Palette (AI Academy-inspired)

```css
:root {
  /* Primary Brand */
  --color-primary: #4F46E5;
  --color-primary-subtle: rgba(79, 70, 229, 0.08);
  --color-primary-light: #E0E7FF;

  /* Backgrounds */
  --color-bg-primary: #FAFAF9; /* Warm off-white */
  --color-bg-card: #F8FAFC;    /* Cool off-white */
  --color-bg-dark: #1E293B;    /* Dark sections */

  /* Accents */
  --color-accent-cyan: #06B6D4;
  --color-accent-emerald: #10B981;
  --color-accent-amber: #F59E0B;
  --color-accent-violet: #7C3AED;

  /* States */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-urgency: #EF4444;
}
```

**Psychology:** Multi-accent signals energy and modernity. Off-white = warmth. Dark sections = premium.

---

## Typography Systems

### Single-Family System (iTrust)

```css
:root {
  --font-family: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'Space Mono', monospace;
}

h1 {
  font-size: 76.8px;
  font-weight: 700;
  line-height: 1.06;
  letter-spacing: -0.03em;
}

h2 {
  font-size: 40px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

h3 {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
}

body {
  font-size: 16-18px;
  font-weight: 400;
  line-height: 1.6;
}
```

**Use When:** Corporate, fast-loading, cohesion priority. Mono for labels/stats only.

### Two-Family System (AI Academy)

```css
:root {
  --font-display: 'Space Grotesk', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

h1 {
  font-family: var(--font-display);
  font-size: 60px;
  font-weight: 700;
  line-height: 1.0;
  letter-spacing: -0.04em;
}

h2 {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

h3 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
}

body {
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 400;
  line-height: 1.6;
}
```

**Use When:** Modern tech, personality priority. Display for headlines, body for readability.

---

## Typography Pairings Reference

| Pairing | Use Case | Fonts |
|---------|----------|-------|
| **Single family** | Corporate, fast-loading | DM Sans only |
| **Display + body** | Modern tech, personality | Space Grotesk + Inter |
| **With mono labels** | Technical/data-heavy | Either + JetBrains Mono |
| **Luxury** | Premium, refined | Instrument Serif + Inter |

---

## H1 Scale Guidelines

| Context | Size | Weight | Line-Height |
|---------|------|--------|-------------|
| **Authority/Enterprise** | 76.8px | 700 | 1.06 |
| **Modern/Tech** | 60px | 700 | 1.0 |
| **Premium/Luxury** | 48-56px | 600 | 1.1 |
| **Mobile** | 36-44px | 700 | 1.1 |

---

## Anti-Patterns

| Anti-Pattern | Issue |
|--------------|-------|
| Inter/Roboto without hierarchy | Safe = forgettable |
| System fonts for display | No personality |
| Tight tracking on body text | Readability suffers |
| Large sizes with loose tracking | Loses impact |
| Multiple display fonts | Visual confusion |

---

## Contrast Requirements (WCAG)

| Element | Minimum Ratio | Notes |
|---------|---------------|-------|
| Normal text | 4.5:1 | Body copy, descriptions |
| Large text (18pt+) | 3:1 | Headlines, subheads |
| UI components | 3:1 | Buttons, inputs, icons |
| Focus indicators | 3:1 | Visible against background |

**Dark Mode Note:** Requires explicit contrast verification. Don't assume light palette conversions work.
