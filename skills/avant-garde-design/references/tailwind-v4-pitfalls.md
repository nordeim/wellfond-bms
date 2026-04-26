# Tailwind CSS v4 Pitfalls & Performance

Common migration pitfalls, performance benchmarks, and browser requirements.

---

## Common Pitfalls

### Gradient Persistence

```html
<!-- v3: to-yellow-400 would reset in dark mode -->
<div class="bg-gradient-to-r from-red-500 to-yellow-400 dark:from-blue-500">

<!-- v4: Gradients persist - use explicit reset -->
<div class="bg-linear-to-r from-red-500 via-orange-400 to-yellow-400 dark:via-none dark:from-blue-500 dark:to-teal-400">
```

### Border Color Default

```html
<!-- v3: Implicit gray-200 -->
<div class="border px-2 py-3">

<!-- v4: Must specify color -->
<div class="border border-gray-200 px-2 py-3">
```

### Hover Media Query

```css
/* v4: Only applies when primary input supports hover */
@media (hover: hover) {
  .hover\:underline:hover { text-decoration: underline; }
}

/* Override for touch */
@custom-variant hover (&:hover);
```

---

## @apply Breaking Changes

### Issue: @apply Not Working in v4.0.8+

**Root Causes:**
- Lightning CSS compatibility issues
- CSS module isolation
- Missing `@reference` directive

**Solution:**

```css
/* In scoped styles (CSS Modules, Vue SFC, etc.) */
@reference "../../app.css";

.my-component {
  @apply flex items-center gap-4;
}
```

---

## @source Issues in Monorepos

### Issue: Internal Package Imports Fail

**Solution:**

```css
/* apps/web/src/style.css */
@import 'tailwindcss';
@import '@repo/tailwind-config/style.css';
@source '../../../tools/tailwind';
```

---

## Arbitrary Values Not Recognized

### Issue: Dynamic Arbitrary Values Fail

**Root Cause:** v4 requires predefined values in `@theme` for some contexts.

**Solution:**

```css
@theme {
  --dynamic-width: 200px;
  --dynamic-color: #ff0000;
}
```

```html
<div class="w-[--dynamic-width] bg-[--dynamic-color]">
```

---

## Color Opacity Rendering Differences

### Issue: Subtle Color Differences Between v3 and v4

**Cause:** v4 uses `color-mix()` internally instead of CSS custom properties.

**Mitigation:** Test color values in target browsers, especially with `currentColor`.

---

## Build Time Regression

### Issue: Builds Slower Than v3

**Diagnosis:**
1. Check for misconfigured `@source` scanning large directories
2. Verify Vite plugin vs PostCSS plugin usage
3. Check for content detection scanning `node_modules`

**Solution:**

```css
/* Limit scanning scope */
@source "src/components";
/* NOT @source "." or @source "node_modules"; */
```

---

## Performance Benchmarks

| Metric | Improvement |
|--------|-------------|
| Full build | 3.78x faster |
| Incremental rebuild | 8.8x faster |
| No-change rebuild | 182x faster |

---

## Browser Requirements

| Browser | Minimum Version |
|---------|-----------------|
| Safari | 16.4+ |
| Chrome | 111+ |
| Firefox | 128+ |

Projects requiring older browsers **must remain on v3.4**.

---

## Quick Migration Checklist

- [ ] Remove `tailwind.config.js`
- [ ] Replace `@tailwind base/components/utilities` with `@import "tailwindcss"`
- [ ] Update opacity utilities: `bg-opacity-50` → `bg-color/50`
- [ ] Update shadow/blur/rounded: `shadow-sm` → `shadow-xs`
- [ ] Update gradients: `bg-gradient-*` → `bg-linear-*`
- [ ] Update CSS variables: `bg-[--color]` → `bg-(--color)`
- [ ] Move theme config to `@theme` directive
- [ ] Test in all supported browsers

---

**See Also:** [`tailwind-v4-migration.md`](tailwind-v4-migration.md) for setup and utility mappings.
