# Patterns Catalog

Validated patterns extracted from iTrust Academy and AI Academy analysis.

---

## Patterns to Steal

### Credibility & Trust

| Pattern | Source | Implementation |
|---------|--------|----------------|
| **Exam domain transparency table** | iTrust | Show percentage + day mapping for each topic. Builds credibility through specificity. |
| **Vendor authorization badges** | iTrust | "Authorized Training Partner" logos. Institutional trust signals. |
| **FAANG logo trust bar** | AI Academy | Company logos grayscale → color on hover. Subtle, professional social proof. |
| **Quantified outcomes** | AI Academy | "94% completion rate", "92% placement rate", "45% salary increase". Specific numbers beat vague claims. |

### Visual Hierarchy

| Pattern | Source | Implementation |
|---------|--------|----------------|
| **Stats in hero** | Both | 4 metrics with large numbers + small labels. Quick value communication. |
| **Dark section for premium** | AI Academy | Visual rhythm break. Creates contrast for pricing/featured content. |
| **Status pills** | Both | Color-coded availability: "AVAILABLE" (green), "FILLING FAST" (amber), "OPEN" (blue). |
| **Card top-border color coding** | Both | 3px colored top border for category differentiation. Instant visual scan. |

### Conversion Psychology

| Pattern | Source | Implementation |
|---------|--------|----------------|
| **Strikethrough + urgency pricing** | AI Academy | Original price crossed out + discounted price + "Only 8 spots remaining". |
| **Month/day date badges** | AI Academy | Calendar-style visual treatment for upcoming cohorts. |
| **Early bird deadlines** | AI Academy | Specific dates create urgency without feeling manipulative. |
| **Multiple CTA placements** | iTrust | Strategic CTAs throughout scroll, not just hero. |

### Typography & Content

| Pattern | Source | Implementation |
|---------|--------|----------------|
| **Single font discipline** | iTrust | DM Sans throughout. Mono only for stats/labels. Cohesive, fast-loading. |
| **Two-font display system** | AI Academy | Space Grotesk for headlines, Inter for body. Personality + readability. |
| **Monospace for statistics** | Both | JetBrains Mono/Space Mono for numbers. Creates technical vocabulary. |
| **Ghost buttons with arrows** | iTrust | Subtle secondary navigation. Suggests "explore" action. |

---

## Anti-Patterns Each Avoids

| iTrust Avoids | AI Academy Avoids |
|---------------|-------------------|
| Stock photography clichés | Corporate sterility |
| Over-animation | Single-color monotony |
| Vague promises ("transform your life!") | Generic stock illustrations |
| Pricing without context | Information overload in hero |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Alternative |
|--------------|--------------|-------------|
| **Emoji icons in enterprise** | Feels informal, undermines credibility | Custom icon system or Lucide/Heroicons |
| **Generic stock photos** | Zero distinctiveness, dated instantly | Custom photography or abstract illustrations |
| **Purple-gradient-on-white** | The ultimate "AI slop" signal | Unexpected color combinations |
| **Predictable card grids** | No memorability | Asymmetric layouts, varying card sizes |
| **Inter/Roboto without hierarchy** | Safe = forgettable | Distinctive display font + clear scale |
| **Hidden pricing on B2C** | Creates friction, reduces trust | Transparent pricing or clear "Request Quote" |
| **Dark mode without verification** | Accessibility failure | Explicit contrast testing required |
| **"Available" status without urgency** | Missed conversion opportunity | "FILLING FAST" + remaining count |

---

## Layout Specifications

### Shared Patterns (Both Sites)

| Element | Specification | Rationale |
|---------|---------------|-----------|
| Max content width | 1140px | Optimal line length for reading |
| Navigation height | 68px fixed | Standard, accessible |
| Card border-radius | 12-14px | Modern, approachable |
| Card padding | 24-32px | Generous internal spacing |
| Section padding | 4-8rem vertical | Breathing room |

### Divergent Patterns

| Element | iTrust | AI Academy |
|---------|--------|------------|
| Grid system | Strict 12-column | Flexible, asymmetric |
| Hero layout | Text-focused, centered | Two-column, floating elements |
| Card treatment | Subtle shadows, borders | Colored tops, illustrations |
| Whitespace philosophy | Structural separator | Dramatic isolation |
| Animation level | Minimal (0.2s fades) | Transform effects (0.3s) |

---

## Component Patterns

### Status Badges

```html
<!-- Available -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
  AVAILABLE
</span>

<!-- Filling Fast -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
  FILLING FAST
</span>

<!-- Open -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
  OPEN
</span>
```

### Trust Bar

```html
<!-- Grayscale logos → color on hover -->
<div class="flex items-center justify-center gap-8 py-8">
  <img src="google.svg" class="h-8 opacity-50 grayscale hover:opacity-100 hover:grayscale-0 transition-all" />
  <img src="microsoft.svg" class="h-8 opacity-50 grayscale hover:opacity-100 hover:grayscale-0 transition-all" />
  <!-- ... -->
</div>
```

### Stats in Hero

```html
<div class="grid grid-cols-2 md:grid-cols-4 gap-8">
  <div>
    <div class="text-4xl font-bold font-mono">94%</div>
    <div class="text-sm text-muted-foreground">Completion Rate</div>
  </div>
  <!-- ... -->
</div>
```

### Dark Section

```html
<section class="bg-slate-900 text-white py-16">
  <!-- Premium content, pricing, featured course -->
</section>
```

---

## Conversion Optimization Patterns

### Urgency Without Manipulation

| Bad | Good |
|-----|------|
| "BUY NOW OR MISS OUT!" | "Only 8 spots remaining" |
| Countdown timer that loops | Specific cohort start date |
| Fake scarcity | Real enrollment numbers |

### Trust Architecture

| B2B (iTrust) | B2C (AI Academy) |
|--------------|------------------|
| Vendor partnerships | FAANG logos |
| Certifications | Outcome percentages |
| Regional specificity | Community size |
| Professional services | Student testimonials |

---

## Performance Considerations

| Pattern | Performance Impact | Recommendation |
|---------|-------------------|----------------|
| Single font family | Minimal payload | Preferred for performance |
| Two-font system | +20-40KB | Acceptable for differentiated experiences |
| Custom illustrations | Varies | Use SVG or WebP |
| Dark sections | Minimal | CSS only, no JS |
| Trust logos | +10-30KB | Lazy load below fold |
