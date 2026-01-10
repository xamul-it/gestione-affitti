# Navigation Architecture - Quick Reference Card

**Status:** Proposed | **Decision:** Sidebar-Only | **Timeline:** 3 weeks

---

## One-Minute Summary

**WHAT:** Replace dual navigation (top navbar + sidebar) with single sidebar system

**WHY:** User confusion, poor mobile UX, maintenance burden, backend architecture mismatch

**HOW:** Build sidebar-only navigation with utility top bar, mobile drawer, collapse feature

**WHEN:** Sprint 1 (3 weeks)

**WHO:** 1 frontend dev (3 weeks) OR 2 devs (1.5 weeks)

---

## Component Structure

```
components/Navigation/
├── AppNavigation.jsx        # Main controller
├── TopBar.jsx               # Logo, search, user menu (utility only)
├── Sidebar.jsx              # Desktop navigation (250px, collapsible)
├── MobileDrawer.jsx         # Mobile navigation (280px overlay)
├── NavigationItem.jsx       # Reusable menu item
└── NavigationContext.jsx    # Shared state (React Context)
```

---

## Layout Architecture

### Desktop (≥768px)
```
[TopBar: Logo | Search | User] ← 60px
[Sidebar: Menu] [Content]      ← Sidebar 250px, Content flex
```

### Mobile (<768px)
```
[TopBar: ☰ Logo | Search | User] ← 60px
[Content: Full-width]             ← Drawer slides over on ☰ tap
```

---

## Key Features

| Feature | Desktop | Mobile |
|---------|---------|--------|
| **Navigation** | Persistent sidebar (left) | Hamburger → drawer overlay |
| **Collapse** | Yes (250px → 60px) | N/A (full overlay) |
| **Interaction** | Click to expand/navigate | Tap to expand/navigate |
| **Gestures** | N/A | Swipe left to close |
| **Menu Data** | GET /platform/menu/ | Same API |
| **State** | NavigationContext | Same context |

---

## State Management

```jsx
// Use NavigationContext (not Redux)

const {
  isMobile,              // Boolean: < 768px?
  sidebarOpen,           // Boolean: drawer visible?
  setSidebarOpen,        // Function: toggle drawer
  sidebarCollapsed,      // Boolean: 60px mode?
  setSidebarCollapsed,   // Function: toggle collapse
  menuItems,             // Array: menu from API
  menuLoading,           // Boolean: loading state
  menuError,             // String: error message
  expandedItems,         // Set: expanded menu item IDs
  toggleExpanded,        // Function: expand/collapse item
  reloadMenu,            // Function: refresh from API
} = useNavigation()
```

---

## API Integration

```javascript
// Single API call (cached in sessionStorage)

GET /api/v1/platform/menu/

// Returns:
[
  {
    id: "immobili",
    module_id: "immobili",
    label: "Immobili",
    path: "/immobili",
    icon: "building",
    parent_id: null,
    order_index: 10,
    required_permission: "immobili.view",
    children: [ /* nested items */ ]
  },
  // ...
]

// Permission filtering: Backend (automatic)
// Hierarchy support: Unlimited depth
// Module registration: Automatic (from manifest)
```

---

## Responsive Breakpoints

```css
/* Mobile-first strategy */
320px  - Extra small (iPhone SE)
576px  - Small (landscape phones)
768px  - Medium (tablets) ← SIDEBAR APPEARS
992px  - Large (small laptops)
1200px - Extra large (desktops)
```

---

## Accessibility Checklist

- [ ] **Keyboard:** Tab, Enter, Escape work
- [ ] **ARIA:** Proper labels, roles, states
- [ ] **Focus:** Visible outline, trapped in drawer
- [ ] **Contrast:** 4.5:1 ratio (text)
- [ ] **Touch:** 44px minimum targets (mobile)
- [ ] **Screen reader:** Landmarks, navigation role

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Create `components/Navigation/` directory
- [ ] Build NavigationContext (state management)
- [ ] Build TopBar (utility bar)
- [ ] Build Sidebar (desktop nav)
- [ ] Build MobileDrawer (mobile nav)
- [ ] Build NavigationItem (reusable component)

### Week 2: Integration
- [ ] Update App.jsx (wrap in NavigationProvider)
- [ ] Connect to `/platform/menu/` API
- [ ] Implement active route highlighting
- [ ] User menu (logout, profile)
- [ ] Accessibility audit
- [ ] Mobile testing (real devices)

### Week 3: Polish & Deploy
- [ ] Cross-browser testing
- [ ] Performance testing (<200ms load, 60fps)
- [ ] Remove old Navbar.jsx, DynamicMenu.jsx
- [ ] Update documentation (CLAUDE.md)
- [ ] Code review
- [ ] Deploy to staging → production

---

## File Changes

### NEW Files
```
✅ components/Navigation/AppNavigation.jsx      (150 lines)
✅ components/Navigation/TopBar.jsx              (100 lines)
✅ components/Navigation/Sidebar.jsx             (120 lines)
✅ components/Navigation/MobileDrawer.jsx        (140 lines)
✅ components/Navigation/NavigationItem.jsx       (80 lines)
✅ contexts/NavigationContext.jsx                (100 lines)
✅ + CSS files for each component
```

### MODIFIED Files
```
✏️ App.jsx                          (wrap in NavigationProvider)
✏️ CLAUDE.md                        (update navigation docs)
```

### REMOVED Files
```
❌ components/Layout/Navbar.jsx      (210 lines) - DELETE
❌ components/Layout/Navbar.css      (236 lines) - DELETE
❌ components/Platform/DynamicMenu.jsx (152 lines) - REPLACE with Sidebar
❌ components/Platform/DynamicMenu.css (209 lines) - REPLACE with Sidebar.css
❌ core/modules/ModuleRegistry.js     (50 lines) - DELETE (no longer needed)
```

---

## Code Snippets

### Using NavigationContext

```jsx
import { useNavigation } from '../contexts/NavigationContext'

function MyComponent() {
  const { isMobile, sidebarOpen, setSidebarOpen } = useNavigation()

  return (
    <div>
      {isMobile && (
        <button onClick={() => setSidebarOpen(true)}>
          Open Menu
        </button>
      )}
    </div>
  )
}
```

### Creating a Menu Item

```jsx
<NavigationItem
  item={{
    id: 'immobili',
    label: 'Immobili',
    icon: 'building',
    path: '/immobili',
    children: [/* submenus */]
  }}
  collapsed={false}
  mobile={false}
  expanded={true}
  onToggle={() => toggleExpanded('immobili')}
/>
```

### Checking Active Route

```jsx
import { useLocation } from 'react-router-dom'

const location = useLocation()
const isActive = location.pathname === item.path

<Link
  to={item.path}
  className={`nav-link ${isActive ? 'active' : ''}`}
>
  {item.label}
</Link>
```

---

## Design Tokens

```css
:root {
  /* Sidebar */
  --sidebar-width: 250px;
  --sidebar-collapsed-width: 60px;
  --sidebar-bg: #2c3e50;
  --sidebar-text: #ecf0f1;
  --sidebar-hover-bg: rgba(255, 255, 255, 0.1);
  --sidebar-active-bg: #3498db;

  /* Top Bar */
  --topbar-height: 60px;
  --topbar-bg: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);

  /* Mobile Drawer */
  --drawer-width: 280px;
  --drawer-backdrop: rgba(0, 0, 0, 0.5);

  /* Transitions */
  --nav-transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  /* Z-index */
  --z-topbar: 1000;
  --z-sidebar: 900;
  --z-drawer: 1200;
}
```

---

## Testing Commands

```bash
# Development
npm run dev

# Build
npm run build

# Preview production build
npm run preview

# Run accessibility audit (install axe-core)
npm run a11y

# Check bundle size
npm run analyze
```

---

## Common Issues & Solutions

### Issue: Menu items not loading
**Cause:** Not authenticated, API error
**Solution:** Check localStorage for `access_token`, check backend logs

### Issue: Active route not highlighting
**Cause:** Path mismatch
**Solution:** Log `location.pathname` and `item.path`, ensure exact match

### Issue: Mobile drawer not closing
**Cause:** Event listener not working
**Solution:** Check backdrop click handler, add console.log to debug

### Issue: Sidebar collapsed state not persisting
**Cause:** localStorage not saving
**Solution:** Check browser localStorage quota, clear old data

### Issue: Menu hierarchy not rendering
**Cause:** Incorrect parent_id relationships
**Solution:** Check backend menu API response, verify parent_id values

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Menu load time | <200ms | Chrome DevTools Network |
| Animation FPS | 60fps | Chrome DevTools Performance |
| Bundle size increase | <50KB | webpack-bundle-analyzer |
| Lighthouse Performance | >90 | Chrome Lighthouse |
| First Contentful Paint | <1.5s | Chrome Lighthouse |

---

## Decision Rationale (Quick)

**Why Sidebar-Only?**
1. Backend menu API is designed for sidebar (hierarchical, unlimited depth)
2. Better mobile UX (drawer pattern vs stacked menus)
3. Single system = less confusion, easier maintenance
4. Extensible (supports 10+ modules)
5. Industry standard (Salesforce, Odoo, ERPs use sidebar)

**Why Not Top-Only?**
1. Limited horizontal space (can't fit 10+ modules)
2. Requires backend API redesign (flatten hierarchy)
3. Still needs mobile drawer (inconsistent)

**Why Not Hybrid?**
1. Still two systems (maintenance burden)
2. Content separation unclear (which menu gets what?)
3. Mobile still broken (stacks vertically)

---

## Success Metrics

**User Satisfaction:** 8/10+ (post-deployment survey)
**Mobile UX:** Zero "can't find menu" support tickets
**Performance:** <200ms load, 60fps animations
**Accessibility:** WAVE validator 0 errors
**Code Quality:** 80%+ test coverage
**Adoption:** Zero rollback requests

---

## Resources

- **Full Decision Doc:** `/docs/architecture/NAVIGATION_ARCHITECTURE_DECISION.md` (35 pages)
- **Visual Comparison:** `/docs/architecture/NAVIGATION_COMPARISON.md` (diagrams)
- **Summary:** `/docs/architecture/NAVIGATION_DECISION_SUMMARY.md` (4 pages)
- **Component API:** `/components/Navigation/README.md` (TBD)
- **Backend Menu API:** `GET /api/v1/platform/menu/` (existing)

---

## Contact / Questions

- **Architecture Questions:** Web Architecture Advisor (this document author)
- **UX Questions:** UX Optimizer (Sprint 1 lead)
- **Backend Questions:** Backend team (menu API owners)
- **Product Questions:** Product Owner (approval authority)

---

**Last Updated:** 2025-12-04
**Status:** Awaiting Approval
**Next Steps:** Product Owner + UX Optimizer sign-off
