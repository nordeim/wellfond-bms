# Technical Commitments

## Commitment Matrix by Strategic Position

### Strong Institutional Clarity

**Must Commit To:**
- Maximum performance (Lighthouse 95+)
- AAA accessibility compliance
- Rock-solid semantic HTML
- Simple, maintainable CSS architecture
- `prefers-reduced-motion` compliance

**Can Deprioritize:**
- Complex JavaScript animations
- Bespoke WebGL/3D assets
- Cutting-edge interaction patterns

---

### Strong Dynamic Modernism

**Must Commit To:**
- Expert-level animation (GSAP/Framer Motion)
- 3D/WebGL engineering (Three.js) for hero elements
- Performance budgetting & code-splitting
- Comprehensive design system documentation
- `prefers-reduced-motion` compliance (required)

**Can Deprioritize:**
- Maximum performance on low-end devices
- Pixel-perfect cross-browser consistency (focus on modern browsers)

---

### Balanced Position (Quadrants 2-3)

**Must Commit To:**
- Clear, prioritized component library
- Strong foundational accessibility
- Performant core experience
- Selective use of "delight" elements

**Can Deprioritize:**
- Full 3D/WebGL complexity
- Experimental interaction patterns
- Ultra-conservative design constraints

---

## Performance Budgets

| Metric | Institutional | Dynamic | Balanced |
|--------|---------------|---------|----------|
| **Initial Bundle** | < 150 KB | < 300 KB | < 200 KB |
| **First Contentful Paint** | < 1.0s | < 1.5s | < 1.2s |
| **Largest Contentful Paint** | < 1.5s | < 2.5s | < 2.0s |
| **Time to Interactive** | < 2.0s | < 3.5s | < 2.5s |
| **Cumulative Layout Shift** | < 0.05 | < 0.1 | < 0.05 |
| **Animation Frame Budget** | N/A | < 16ms (60fps) | < 16ms |

---

## Tech Stack by Position

### Institutional Clarity Stack

```yaml
Framework: Next.js 16+ or Astro (static-first)
Styling: Tailwind CSS 4.0 + shadcn UI
Fonts: DM Sans (Google Fonts, single family)
Animations: CSS transitions only (no JS libraries)
Icons: Lucide or Heroicons (consistent stroke weight)
Performance: Lighthouse 95+ target
Accessibility: WCAG AAA compliance
Testing: Playwright E2E, axe-core a11y
```

### Dynamic Modernism Stack

```yaml
Framework: Next.js 16+ with App Router
Styling: Tailwind CSS 4.0 + shadcn UI + Custom CSS
Fonts: Space Grotesk + Inter (two-family system)
Animations: Framer Motion or GSAP
3D Elements: Three.js or Spline (hero only)
Icons: Custom SVG or Phosphor Icons
Performance: Lighthouse 85+ target (trade-off)
Accessibility: WCAG AA minimum, reduced-motion required
Testing: Playwright + Lighthouse CI + manual a11y
```

---

## Component Library Standards

**CRITICAL:** Per Frontend Architect standards, use library primitives as foundation. Style them; don't rebuild.

| Component | Library Primitive | Styling Approach |
|-----------|------------------|------------------|
| Buttons | Shadcn `Button` | CVA variants for institutional/dynamic |
| Cards | Shadcn `Card` | Custom top borders for categorization |
| Navigation | Shadcn `NavigationMenu` | Tailwind + backdrop blur |
| Badges | Shadcn `Badge` | Status-based color coding |
| Tables | Radix `Table` | Custom styling for transparency tables |
| Dialogs/Modals | Shadcn `Dialog` | Theme-aligned, don't rebuild |
| Accordions | Shadcn `Accordion` | FAQ/curriculum details |
| Tabs | Shadcn `Tabs` | Module navigation |

---

## Security Checklist

| Category | Checks |
|----------|--------|
| **Broken Access Control** | IDOR prevention, proper auth checks, SSRF protection |
| **Security Misconfiguration** | Secure headers, no default credentials |
| **Supply Chain** | Audit dependencies (`npm audit`), lock file integrity |
| **Cryptographic Failures** | bcrypt for passwords, jose for JWT, no hardcoded secrets |
| **Injection** | No SQL injection (use ORM), no XSS |
| **Authentication** | Session management, MFA, secure cookies |

### High-Risk Patterns to Flag

```typescript
// ❌ String concatenation in queries
const query = "SELECT * FROM users WHERE id = " + userId;

// ❌ Dynamic code execution
eval(userInput);

// ❌ Unsafe deserialization
JSON.parse(untrustedData); // Without validation

// ❌ Path traversal
fs.readFile(`./uploads/${userInput}`);
```

---

## Pre-Deploy Checklist

- [ ] All tests passing
- [ ] Build successful (exit 0)
- [ ] No console errors
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Lighthouse score meets target
- [ ] No high/critical vulnerabilities
- [ ] Tested on mobile, tablet, desktop
- [ ] Analytics error tracking configured
