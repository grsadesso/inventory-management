---
name: redesign-saas-ui
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a vertical left sidebar instead of a top nav bar, a consistent spacing scale, and a polished professional look. Use when the user asks to modernize, restyle, or restructure the layout or navigation of a Vue 3 app.
---

# Redesign a Vue 3 App into a SaaS-Style UI

Turn a top-nav Vue 3 app into a modern SaaS interface: fixed left sidebar, slim top bar, a design-token layer, and consistent spacing, type, and surfaces. This is a presentation-layer change only.

## Hard rules

1. **Presentation only.** Do not change data flow, API calls, routes, props/events, i18n keys, or business logic. If a route or label has to change, say so and ask first.
2. **Follow the project's own rules first.** Read the root `CLAUDE.md` and any `client/CLAUDE.md`. They override this skill. In particular:
   - If the project requires a specific subagent for `.vue` work (for example `vue-expert`), delegate to it.
   - Keep the project's API style (Composition API vs Options API), scoped styles, and `v-for` key rules.
   - Respect stated design constraints (palette, "no emojis in UI", chart approach).
3. **No new dependencies** (UI kits, icon packs, CSS frameworks) unless the user approves. Use inline SVG icons and plain CSS custom properties.
4. **Keep it public-safe.** Never add CDN links, internal hostnames, or private registry URLs.
5. **Preserve existing behavior** of every feature reachable from the old nav: all links, language switcher, profile menu, global filters, modals.

## Workflow

### 1. Discover (read before designing)

- Find the shell: usually `src/App.vue`, plus `src/main.js` for routes.
- List every nav item (label source, route path, active-state logic) and everything else in the old header (logo, switcher, profile menu, search).
- Find global UI that sits under the header (filter bars, banners) and where modals are mounted.
- Locate existing styles: global CSS, `:root` variables, per-view hard-coded colors, spacing, and radii.
- Check for i18n: nav labels must keep using the existing translation function, not hard-coded text.
- Note the dev-server port and any existing visual checks (screenshots, Playwright).

Summarize what you found in a few lines before editing.

### 2. Define design tokens

Create one token layer (`:root` custom properties in the global stylesheet, or a dedicated `styles/tokens.css` imported once). Reuse the project's existing palette where there is one; otherwise use this neutral base.

```css
:root {
  /* Spacing: 4px base scale. Use only these values for padding, margin, and gap. */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px;

  /* Surfaces */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-sidebar-bg: #0f172a;
  --color-sidebar-text: #94a3b8;
  --color-sidebar-text-active: #ffffff;
  --color-sidebar-item-hover: rgba(255, 255, 255, 0.06);
  --color-sidebar-item-active: rgba(255, 255, 255, 0.12);

  /* Text */
  --color-text: #0f172a;
  --color-text-muted: #64748b;

  /* Brand + status: replace --color-primary with the app's brand color */
  --color-primary: #3b82f6;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-danger: #dc2626;

  /* Shape and depth */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  /* Type */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --text-xs: 12px; --text-sm: 14px; --text-base: 15px; --text-lg: 18px; --text-xl: 24px;

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 56px;
  --content-max-width: 1440px;
}
```

Rules for tokens:
- Every new or touched style uses tokens, not raw hex or pixel values.
- Do not delete the old variables or colors that views still use. Migrate views to tokens gradually and only where you edit them.

### 3. Build the shell

Target structure in the root component:

```
.app-shell            display: flex; min-height: 100vh
  <aside class="sidebar">      fixed/sticky, full height, width var(--sidebar-width)
    brand block (logo + app name + subtitle)
    <nav aria-label="Primary">  vertical list of router-links
    sidebar footer (language switcher, profile menu)
  <div class="shell-main">     flex: 1; min-width: 0
    <header class="topbar">    slim bar: page title (or breadcrumb) + global actions
    global filter bar / banners
    <main class="content">     padding var(--space-5); max-width var(--content-max-width)
      <router-view />
```

**Sidebar spec**
- Dark or light surface from tokens, full height, `position: sticky; top: 0; height: 100vh; overflow-y: auto`.
- Brand block at the top; nav in the middle; utilities (language switcher, profile) pinned to the bottom with `margin-top: auto`.
- Each nav item: icon (20px inline SVG, `currentColor`) + label, height 40px, `padding: 0 var(--space-3)`, `border-radius: var(--radius-md)`, `gap: var(--space-3)`.
- States: default (muted text), hover (subtle background), active (stronger background, white text, optional 3px accent bar), `:focus-visible` (2px outline using `--color-primary`).
- Use `router-link` with `active-class` / `exact-active-class` instead of manual `$route.path` comparison where equivalent. Keep `exact` behavior for the root route so "/" is not active everywhere.
- Group items under small uppercase section labels only if the app has more than about six destinations.
- Keep labels bound to the existing i18n function.

**Top bar spec**
- Height `var(--topbar-height)`, white surface, bottom border, `padding: 0 var(--space-5)`.
- Show the current page title (derive from the route or an existing label; do not invent new copy). Put items that used to live in the header and are not nav (profile, language) either here or in the sidebar footer, not both.

**Responsive**
- At `>= 1024px`: sidebar visible.
- At `< 1024px`: sidebar becomes an off-canvas drawer toggled by a menu button in the top bar, with an overlay, `Escape` to close, and closing on route change.
- Optional: a collapsed icon-only mode (`--sidebar-width-collapsed`) with `title`/tooltip labels, persisted in `localStorage`. Only add it if asked.

**Icons**
- Inline SVG, 24x24 viewBox, `stroke="currentColor"`, `stroke-width="1.75"`, `fill="none"`, `aria-hidden="true"`. Pick icons that match the section meaning (dashboard, boxes, receipt, chart, etc.). Do not use emoji or icon fonts.

### 4. Polish content areas

Apply consistently, view by view, without changing structure or logic:
- **Page container:** `padding: var(--space-5)`, vertical rhythm of `var(--space-5)` between sections.
- **Cards:** `background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); padding: var(--space-5)`.
- **Page headers:** title `--text-xl` semibold, optional muted description `--text-sm`.
- **Tables:** sticky-looking header row on `--color-bg`, 12px uppercase muted header text, row height about 48px, subtle row hover, right-align numbers with `font-variant-numeric: tabular-nums`.
- **Buttons:** one primary style, one secondary (bordered), one ghost; height 36px, `--radius-md`, visible focus ring.
- **Inputs and selects:** height 36px, `--radius-md`, 1px border, focus ring in `--color-primary`.
- **Badges/status pills:** `--radius-sm`, `--text-xs`, tinted background plus matching text color; use the project's existing status color mapping.
- **Modals:** keep existing behavior; align radius, shadow, padding, and header style with cards. Do not change open/close logic.
- **Empty, loading, and error states** keep their existing logic; restyle them to the same muted treatment.
- Charts: keep implementation; align colors with tokens only if the project allows it.

### 5. Verify

1. Start the app with the project's documented command and open it in a browser (use the project's required browser tooling, such as Playwright MCP, if CLAUDE.md names one).
2. Walk every route from the sidebar. Confirm: correct active state, no layout overflow, no horizontal scrollbar, content not hidden behind the sidebar.
3. Resize to about 800px wide. Confirm the drawer opens, closes, and traps nothing.
4. Keyboard check: Tab reaches every nav item in order, focus ring is visible, Enter activates.
5. Check the browser console for new warnings or errors. Report pre-existing ones separately; do not claim they are yours or fix them silently.
6. Run the project's build and tests (`npm run build`, plus any test command) and report the real output.
7. Take before/after screenshots if tooling is available.

## Anti-patterns

- Hard-coded colors or pixel values that bypass the tokens.
- Mixed spacing (for example 10px, 14px, 18px) instead of the scale.
- Rewriting views' logic or markup structure just to restyle them.
- Duplicating the nav in both a sidebar and a header.
- Using `index` as a `v-for` key for the nav list; use the route path.
- Removing the language switcher, profile menu, or filter bar because they "don't fit".
- Adding a UI framework to save time.
- Declaring the redesign done without running it in a browser.

## Output to the user

End with a short report:
- What changed (shell, tokens, which views were restyled).
- Anything intentionally left alone, and why.
- Pre-existing issues you noticed but did not touch.
- How to run and review it.
