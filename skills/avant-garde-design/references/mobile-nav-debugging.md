# Mobile Navigation Debugging

Root-cause taxonomy and anti-patterns for debugging mobile navigation failures.

---

## Root-Cause Taxonomy

| Class | Symptom | Fix |
|-------|---------|-----|
| **A** | No visible nav on mobile | Add mobile trigger + overlay |
| **B** | Hidden by opacity/visibility | Verify state toggling logic |
| **C** | Clipped by overflow | Use `position: fixed` overlay |
| **D** | Behind another layer | Check z-index scale |
| **E** | Breakpoint mismatch | Verify viewport meta |
| **F** | JavaScript failure | Guard selectors, check console |
| **G** | Keyboard inaccessible | Use real `<button>` elements |
| **H** | Click-outside race condition | Exclude trigger from handler |

---

## Diagnostic Decision Tree

### Step 1: Is the nav present in the DOM?

- Inspect Elements
- Search for `<nav` or `.nav-links`

**If not present:** Class A or template omission
**If present:** Continue

### Step 2: Is it hidden by computed CSS?

Check Computed styles for:
- `display: none`
- `visibility: hidden`
- `opacity: 0`

**If `display: none`:** Find the rule (likely mobile media query)

### Step 3: Is it off-screen or clipped?

Check layout box:
- `position`
- `top/left/right/bottom`
- `transform`
- Any ancestor `overflow: hidden`

### Step 4: Is it behind another layer?

If it looks "open" but clicks fail:
- Temporarily toggle `pointer-events: none` on suspected overlays
- Inspect stacking contexts

### Step 5: Is JS failing to toggle state?

- Check Console for errors
- Verify click handler is attached
- Verify state change occurs

### Step 6: Production-only disappearance?

- Check build config: content globs and class string patterns
- Verify no dynamic class concatenation
- Test production build locally

---

## Anti-Patterns (Avoid!)

### ❌ Anti-Pattern 1: Hide Nav Without Menu Trigger

```css
@media (max-width: 768px) {
  .nav-links { display: none; }
  /* Creates dead-end */
}
```

### ❌ Anti-Pattern 2: Random Z-Index

```css
.nav { z-index: 999999; }
/* Hides architectural problems */
```

### ❌ Anti-Pattern 3: Non-Semantic Clickables

```tsx
<div onClick={toggleMenu}>Menu</div>
/* Invisible to keyboard */
```

### ❌ Anti-Pattern 4: Missing Trigger at Correct Breakpoint

```tsx
<nav className="hidden md:flex">...</nav>
<button className="hidden md:inline-flex">Menu</button>
/* Nothing visible on mobile! */
```

### ❌ Anti-Pattern 5: SSR Conditional Nav

```tsx
const isMobile = window.innerWidth < 768; // Breaks on SSR
return isMobile ? <MobileNav/> : <DesktopNav/>;
```

### ❌ Anti-Pattern 6: Click-Outside Race Condition

```tsx
useEffect(() => {
  const handleClick = (e: MouseEvent) => {
    if (!menuRef.current?.contains(e.target as Node)) {
      setIsOpen(false); // Closes when toggle clicked!
    }
  };
  document.addEventListener('click', handleClick);
}, []);
```

**Fix:** Check both menu AND trigger:

```tsx
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  if (menu && !menu.contains(target) && !trigger?.contains(target)) {
    setIsOpen(false);
  }
};
```

---

## Common Fixes by Class

| Class | Quick Fix | Full Solution |
|-------|-----------|---------------|
| **A** | Add `<button className="md:hidden">` | Implement full Sheet/overlay pattern |
| **B** | Check `setOpen` call | Add state machine with explicit states |
| **C** | Add `position: fixed` | Move overlay outside overflow containers |
| **D** | Increase z-index | Implement z-index scale system |
| **E** | Add viewport meta | Verify responsive meta tag |
| **F** | Check console | Add guards: `if (!button || !nav) return;` |
| **G** | Change `<div>` to `<button>` | Add ARIA attributes and keyboard handlers |
| **H** | Add trigger check | Refactor to single state function |

---

**See Also:** [`mobile-navigation.md`](mobile-navigation.md) for guardrails and implementation patterns.
