# Tailwind CSS v4 Migration

CSS-first architecture with no `tailwind.config.js`.

---

## Critical: CSS-First Architecture

**NO `tailwind.config.js`** — Use CSS-only configuration.

---

## Required Setup

### Package Installation

```bash
npm install tailwindcss@latest @tailwindcss/vite
```

### vite.config.js

```javascript
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tailwindcss()],
});
```

### globals.css (Required Structure)

```css
@import "tailwindcss";

@theme {
  /* Colors - OKLCH color space preferred */
  --color-brand-500: oklch(0.84 0.18 117.33);
  --color-brand-600: oklch(0.53 0.12 118.34);

  /* Typography */
  --font-sans: "Inter", system-ui, sans-serif;
  --font-display: "Space Grotesk", sans-serif;

  /* Spacing Scale */
  --spacing-18: 4.5rem;

  /* Custom Animations */
  --animate-float: float 3s ease-in-out infinite;

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }
}

@layer base {
  * {
    @apply border-slate-800;
  }
  body {
    @apply bg-void text-slate-100 font-sans antialiased;
  }
}
```

---

## v3 → v4 Utility Mappings

### Removed Utilities (Must Migrate)

| v3 Utility | v4 Replacement | Pattern |
|------------|----------------|---------|
| `bg-opacity-50` | `bg-red-500/50` | Opacity modifiers |
| `text-opacity-50` | `text-white/50` | Opacity modifiers |
| `border-opacity-50` | `border-black/50` | Opacity modifiers |
| `flex-shrink-*` | `shrink-*` | Direct rename |
| `flex-grow-*` | `grow-*` | Direct rename |
| `overflow-ellipsis` | `text-ellipsis` | Direct rename |

### Renamed Utilities

| v3 | v4 | Reason |
|----|----|--------|
| `shadow-sm` | `shadow-xs` | Explicit scale |
| `shadow` | `shadow-sm` | Named values |
| `blur-sm` | `blur-xs` | Explicit scale |
| `blur` | `blur-sm` | Named values |
| `rounded-sm` | `rounded-xs` | Explicit scale |
| `rounded` | `rounded-sm` | Named values |
| `outline-none` | `outline-hidden` | Semantic clarity |
| `ring` | `ring-3` | Explicit width |

### Gradients (Major Change)

| v3 | v4 |
|----|----|
| `bg-gradient-to-r` | `bg-linear-to-r` |
| `bg-gradient-to-r from-red-500` | `bg-linear-to-r from-red-500` |

**New in v4:** `bg-conic-*`, `bg-radial-*`, `bg-linear-45`

---

## CSS Variable Syntax Changes

```html
<!-- v3: Square brackets for CSS variables -->
<div class="bg-[--brand-color] w-[--custom-width]">

<!-- v4: Parentheses for CSS variables -->
<div class="bg-(--brand-color) w-(--custom-width)">
```

---

## Container Queries (Now Built-In)

```html
<div class="@container">
  <div class="grid grid-cols-1 @sm:grid-cols-3 @lg:grid-cols-4">
    <!-- Responsive to container, not viewport -->
  </div>
</div>

<!-- Max-width queries -->
<div class="@container">
  <div class="flex @max-md:hidden">
    <!-- Hidden when container < md -->
  </div>
</div>
```

---

## Custom Utilities Registration

**v3 Approach (Deprecated):**

```css
@layer utilities {
  .tab-4 { tab-size: 4; }
}
```

**v4 Approach:**

```css
@utility tab-4 {
  tab-size: 4;
}
```

---

## Container Configuration

**v3 (JavaScript):**

```javascript
module.exports = {
  theme: {
    container: {
      center: true,
      padding: '2rem'
    }
  }
}
```

**v4 (CSS):**

```css
@utility container {
  margin-inline: auto;
  padding-inline: 2rem;
}
```

---

**See Also:** [`tailwind-v4-pitfalls.md`](tailwind-v4-pitfalls.md) for common pitfalls and browser requirements.
