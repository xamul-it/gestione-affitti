# UAT - Sidebar-Only Navigation Refactoring Test Plan

**Test Campaign ID**: `UAT-NAV-REFACTOR-2025-12-04`
**Test Date**: December 4, 2025
**Refactoring Scope**: Dual Navigation → Unified Sidebar Architecture
**Objective**: Verify ZERO functional regressions and improved UX consistency

---

## Executive Summary

### What Changed
A major frontend architecture refactoring replaced the dual navigation system with a unified sidebar-only approach:

**REMOVED:**
- `Navbar.jsx` (top navigation bar)
- `DynamicMenu.jsx` (old sidebar implementation)

**ADDED:**
- `NavigationContext.jsx` - Centralized state management
- `TopBar.jsx` - 60px utility bar (hamburger, logo, search, user menu)
- `Sidebar.jsx` - Desktop navigation (250px/60px collapsible)
- `Drawer.jsx` - Mobile navigation (slide-in overlay)
- `NavigationItem.jsx` - Recursive menu component with accordion support

**MODIFIED:**
- `App.jsx` - New layout integration with AppLayout component

### Test Objectives

1. **ZERO Functional Regressions** - All existing navigation functionality must work identically
2. **UX Consistency** - Unified navigation behavior across all screen sizes
3. **Accessibility Compliance** - WCAG Level AA keyboard and screen reader support
4. **Performance** - No degradation in menu loading or interaction responsiveness
5. **Integration** - Backend menu API and authentication integration remain intact

### Known Pre-existing Issues
- Backend has SQLAlchemy cross-module relationship error (NOT caused by this refactoring)
- Platform menu API may return limited items due to backend issue

---

## Test Environment

```
Frontend:  http://192.168.1.2:3002/ (Vite dev server, port changed from 5173)
Backend:   http://192.168.1.2:8000/api/v1
API Base:  http://192.168.1.2:8000/api/v1 (configured in .env)
Browser:   Chrome/Firefox/Safari (real browser testing required)
Devices:   Desktop (1920x1080), Tablet (768x1024), Mobile (375x667)
```

**Test User Credentials:**
- Admin: `admin` / `admin123`
- Check backend for additional test users

**Critical Test Viewports:**
- Mobile: 320px, 375px, 414px
- Tablet: 576px, 768px
- Desktop: 992px, 1200px, 1920px

---

## Parallel Testing Strategy

### Operator Allocation

| Operator | Focus Area | Test Cases | Duration | Priority |
|----------|-----------|------------|----------|----------|
| **Operator #1** | Navigation Regression | TC-NAV-001 to TC-NAV-007 | ~8 min | CRITICAL |
| **Operator #2** | UI/UX Consistency | TC-UX-001 to TC-UX-008 | ~10 min | HIGH |
| **Operator #3** | Integration & E2E | TC-INT-001 to TC-INT-006 | ~12 min | CRITICAL |

**Total Estimated Duration**: ~30 minutes (parallel execution = ~12 minutes actual)

### Operator Autonomy Guidelines

1. **Maximum Freedom**: Operators should test without asking for permission or clarification
2. **Realistic User Simulation**: Include intentional errors, typos, rapid clicks, back button usage
3. **Exploratory Testing**: Go beyond test cases if suspicious behavior is observed
4. **Screenshot Everything**: Capture all anomalies, even if unsure if they're bugs
5. **Think Like Users**: Test with different personas (rushed admin, careful data entry clerk, mobile field worker)

---

## TC-NAV-001 to TC-NAV-007: Navigation Regression Tests

**Operator**: UAT Operator #1
**Focus**: Core navigation functionality remains intact
**Acceptance Threshold**: 100% PASS (zero defects allowed)

### TC-NAV-001: Desktop Sidebar Behavior

**Objective**: Verify desktop sidebar functions correctly

**Test Steps:**

1. **Initial State**
   - Open frontend at http://192.168.1.2:3002/
   - Login with admin/admin123
   - Verify viewport ≥768px (desktop mode)
   - Expected: Sidebar visible on left, 250px width, expanded state

2. **Collapse/Expand Toggle**
   - Click hamburger icon in TopBar
   - Expected: Sidebar collapses to 60px, icons only visible
   - Click hamburger again
   - Expected: Sidebar expands to 250px, labels visible

3. **State Persistence**
   - Collapse sidebar
   - Refresh page (F5)
   - Expected: Sidebar remains collapsed (localStorage persistence)
   - Expand sidebar, refresh again
   - Expected: Sidebar remains expanded

4. **Visual Verification**
   - Collapsed state: Only icons visible, no text overflow
   - Expanded state: Icons + labels visible, proper spacing
   - Transition: Smooth animation (0.3s)
   - No layout shift in main content area

**Success Criteria:**
- ✅ Sidebar toggles between 250px and 60px
- ✅ State persists across page reloads
- ✅ No visual glitches or text overflow
- ✅ Main content area adjusts margin-left correctly

**Defect Examples:**
- ❌ Sidebar doesn't collapse/expand on click
- ❌ Text overflows in collapsed mode
- ❌ State not persisted in localStorage
- ❌ Animation jittery or missing

---

### TC-NAV-002: Mobile Drawer Behavior

**Objective**: Verify mobile drawer functions correctly

**Test Steps:**

1. **Resize to Mobile**
   - Open DevTools (F12)
   - Set viewport to 375x667 (iPhone SE)
   - Login if needed
   - Expected: Sidebar hidden, only TopBar visible

2. **Open Drawer**
   - Click hamburger icon in TopBar
   - Expected:
     - Drawer slides in from left (280px width)
     - Overlay appears (semi-transparent background)
     - Body scroll disabled
     - Drawer shows: logo + close button + menu

3. **Close Drawer - Overlay Click**
   - Click on overlay (outside drawer)
   - Expected: Drawer slides out, overlay disappears, body scroll restored

4. **Close Drawer - ESC Key**
   - Open drawer again
   - Press ESC key
   - Expected: Drawer closes

5. **Close Drawer - Close Button**
   - Open drawer again
   - Click X button in drawer header
   - Expected: Drawer closes

6. **Close Drawer - Navigation**
   - Open drawer
   - Click any menu item
   - Expected: Drawer closes, route changes

7. **Swipe to Close** (if touch device available)
   - Open drawer
   - Swipe left from drawer edge
   - Expected: Drawer closes

**Success Criteria:**
- ✅ Drawer opens/closes smoothly
- ✅ Overlay blocks interaction with main content
- ✅ All 4 close methods work (overlay, ESC, X button, navigation)
- ✅ Body scroll locked when drawer open
- ✅ No horizontal scrollbar appears

**Defect Examples:**
- ❌ Drawer doesn't slide in
- ❌ Can still interact with content behind overlay
- ❌ ESC key doesn't close drawer
- ❌ Body still scrollable when drawer open
- ❌ Drawer width exceeds viewport (causes horizontal scroll)

---

### TC-NAV-003: Menu Data Loading

**Objective**: Verify menu items load from backend API

**Test Steps:**

1. **Initial Load**
   - Clear localStorage: `localStorage.clear()`
   - Refresh page
   - Login
   - Open browser DevTools → Network tab
   - Expected: XHR request to `/api/v1/platform/menu/`

2. **API Request Verification**
   - Check request headers: `Authorization: Bearer <token>`
   - Expected: Status 200 or appropriate error
   - Response format: Array of menu items with structure:
     ```json
     [
       {
         "id": "home",
         "label": "Home",
         "path": "/",
         "icon": "🏠",
         "children": []
       }
     ]
     ```

3. **Menu Rendering**
   - Expected: Menu items appear in sidebar/drawer
   - If backend returns error, check for error message in UI
   - If backend returns empty array, check for empty state message

4. **Loading State**
   - Clear localStorage, refresh
   - During menu load, check for loading indicator
   - Expected: Spinner or "Caricamento..." text visible

5. **Error State** (simulate backend down)
   - Stop backend server temporarily
   - Refresh frontend
   - Expected:
     - Error message in sidebar/drawer
     - "Riprova" (retry) button visible
     - Click retry button → attempts reload

**Success Criteria:**
- ✅ Menu API called with correct auth token
- ✅ Loading indicator shown during fetch
- ✅ Menu items rendered when API succeeds
- ✅ Error message shown when API fails
- ✅ Retry button works

**Defect Examples:**
- ❌ Menu API not called
- ❌ Auth token missing from request
- ❌ Menu items don't render
- ❌ No loading indicator
- ❌ App crashes on API error

---

### TC-NAV-004: Hierarchical Menu Navigation

**Objective**: Verify nested menu items work correctly

**Test Steps:**

1. **Expand Submenu (Desktop)**
   - Login and ensure desktop viewport
   - Locate a parent menu item (e.g., "Immobili")
   - Click parent item
   - Expected: Submenu expands (accordion), arrow rotates 90°
   - Click parent again
   - Expected: Submenu collapses

2. **Expand Submenu (Mobile)**
   - Switch to mobile viewport (375px)
   - Open drawer
   - Click parent menu item
   - Expected: Same accordion behavior

3. **Navigate to Child Item**
   - Expand parent menu
   - Click child item (e.g., "Unità Immobiliari")
   - Expected:
     - Route changes to child path
     - Drawer closes (mobile only)
     - Child item highlighted as active

4. **Active State Highlighting**
   - Navigate to `/unita-immobiliari`
   - Expected:
     - "Unità Immobiliari" item has active styling
     - Parent "Immobili" also highlighted (if applicable)
     - Active indicator visible (border, background, etc.)

5. **Deep Linking**
   - Copy URL of nested route: `/contratti/123`
   - Open in new tab
   - Login
   - Expected:
     - Menu auto-expands to show active route
     - "Contratti" item highlighted
     - Parent menu expanded

6. **Multiple Levels** (if present)
   - Test 3-level deep menu: Parent → Child → Grandchild
   - Expected: All accordion levels work independently

**Success Criteria:**
- ✅ Accordion expand/collapse works
- ✅ Navigation to child routes succeeds
- ✅ Active route highlighted correctly
- ✅ Deep linking auto-expands parent menus
- ✅ Multiple submenu levels work

**Defect Examples:**
- ❌ Submenu doesn't expand
- ❌ Multiple submenus open at once (should be accordion)
- ❌ Active state not highlighted
- ❌ Deep linking doesn't expand parent
- ❌ Arrow icon doesn't rotate

---

### TC-NAV-005: Keyboard Navigation & Accessibility

**Objective**: Verify WCAG Level AA keyboard and screen reader support

**Test Steps:**

1. **Keyboard Navigation - Desktop**
   - Login, focus on TopBar
   - Press TAB repeatedly
   - Expected TAB order:
     1. Skip-to-content link (visible on focus)
     2. Hamburger button
     3. Logo link
     4. Search input
     5. User menu button
     6. First sidebar menu item
     7. Second sidebar menu item
     8. ... (all menu items)
     9. Main content area
   - Test SHIFT+TAB (reverse order)
   - Expected: Same order in reverse

2. **Skip-to-Content Link**
   - Focus on page (TAB once)
   - Expected: "Vai al contenuto principale" link visible
   - Press ENTER
   - Expected: Focus jumps to `#main-content`

3. **Sidebar Menu Keyboard Controls**
   - TAB to first menu item
   - Press ENTER
   - Expected: Navigates to route
   - TAB to parent item with children
   - Press ENTER or SPACE
   - Expected: Submenu expands (accordion)
   - Press ARROW_DOWN
   - Expected: Focus moves to child item
   - Press ARROW_UP
   - Expected: Focus moves back to parent

4. **Drawer Keyboard Controls (Mobile)**
   - Resize to mobile
   - TAB to hamburger
   - Press ENTER
   - Expected: Drawer opens
   - Press ESC
   - Expected: Drawer closes
   - Open drawer again
   - TAB through menu items
   - Expected: Focus trapped inside drawer

5. **ARIA Attributes Verification**
   - Open DevTools → Inspect Sidebar
   - Expected attributes:
     - `<aside role="navigation" aria-label="Main navigation">`
     - `<ul role="menu">`
     - `<li role="none">`
     - `<a role="menuitem" aria-current="page">` (for active item)
   - Inspect Drawer:
     - `<aside aria-modal="true">`
     - `<button aria-label="Chiudi menu">`
     - `<button aria-expanded="true/false">` (for accordion)

6. **Screen Reader Test** (if available)
   - Enable screen reader (NVDA, JAWS, VoiceOver)
   - Navigate through menu
   - Expected announcements:
     - "Main navigation, navigation landmark"
     - "Home, link, current page"
     - "Immobili, button, collapsed"
     - "Immobili, button, expanded"

**Success Criteria:**
- ✅ Logical TAB order without focus traps
- ✅ Skip-to-content link functional
- ✅ All interactive elements keyboard accessible
- ✅ ESC closes drawer
- ✅ ARIA attributes present and correct
- ✅ Focus visible indicators (no outline: none)
- ✅ Screen reader announces navigation correctly

**Defect Examples:**
- ❌ TAB order illogical or skips elements
- ❌ Focus trap in drawer (can't TAB out)
- ❌ ENTER/SPACE don't activate menu items
- ❌ ESC doesn't close drawer
- ❌ Missing ARIA labels
- ❌ Focus indicators invisible
- ❌ Screen reader announces wrong context

---

### TC-NAV-006: TopBar Utility Components

**Objective**: Verify TopBar components function correctly

**Test Steps:**

1. **Hamburger Button**
   - Desktop: Click hamburger
   - Expected: Sidebar toggles
   - Mobile: Click hamburger
   - Expected: Drawer opens

2. **Logo Link**
   - Click logo (🏢 Gestione Affitti)
   - Expected: Navigates to home route (/)

3. **Search Bar** (if implemented)
   - Type query in search input
   - Expected: Search results appear (or functionality pending)
   - If not implemented, verify placeholder or disabled state

4. **User Menu**
   - Click user avatar/name
   - Expected: Dropdown opens with options:
     - Profile
     - Settings
     - Logout
   - Click "Logout"
   - Expected:
     - Token removed from localStorage
     - Redirected to /login
     - Sidebar/Drawer hidden

5. **TopBar Sticky Behavior**
   - Scroll page down
   - Expected: TopBar remains fixed at top (position: sticky/fixed)

6. **Responsive TopBar**
   - Resize viewport from 1920px to 320px
   - Expected at all breakpoints:
     - TopBar remains 60px height
     - All buttons visible (no overflow)
     - Text truncates gracefully if needed

**Success Criteria:**
- ✅ Hamburger toggles navigation
- ✅ Logo navigates to home
- ✅ Search functional or gracefully disabled
- ✅ User menu dropdown works
- ✅ Logout clears session
- ✅ TopBar sticky/fixed
- ✅ Responsive at all viewport sizes

**Defect Examples:**
- ❌ Hamburger doesn't toggle navigation
- ❌ Logo link broken
- ❌ User menu doesn't open
- ❌ Logout doesn't clear token
- ❌ TopBar scrolls with page
- ❌ Buttons overflow on small screens

---

### TC-NAV-007: No Orphaned UI Elements

**Objective**: Verify old navigation components are completely removed

**Test Steps:**

1. **Visual Inspection - All Routes**
   - Navigate to every major route:
     - /
     - /dashboard
     - /immobili
     - /unita-immobiliari
     - /affittuari
     - /contratti
     - /spese
     - /incassi
     - /admin/modules
   - On each route, inspect for:
     - Old navbar at top (should NOT exist)
     - Old DynamicMenu sidebar (should NOT exist)
     - Duplicate navigation elements

2. **Console Errors**
   - Open DevTools → Console
   - Navigate through all routes
   - Expected: ZERO errors related to:
     - `Navbar.jsx`
     - `DynamicMenu.jsx`
     - Missing imports
     - Cannot read property of undefined

3. **Network Requests**
   - Open DevTools → Network tab
   - Navigate through app
   - Expected: NO requests to old endpoints (if any)
   - Menu API should only call `/api/v1/platform/menu/` once

4. **CSS Conflicts**
   - Inspect styles on navigation elements
   - Expected:
     - No conflicting CSS from old Navbar.css
     - New Sidebar.css, Drawer.css, TopBar.css applied correctly
     - No z-index conflicts (overlapping elements)

5. **Build Verification**
   - Run: `npm run build`
   - Check output for warnings about unused imports
   - Expected: Build succeeds, no references to removed files

**Success Criteria:**
- ✅ No visual presence of old navigation components
- ✅ Zero console errors related to removed files
- ✅ No duplicate navigation UI
- ✅ CSS applies correctly without conflicts
- ✅ Build completes without warnings

**Defect Examples:**
- ❌ Old navbar still visible
- ❌ Console error: "Cannot find module 'Navbar.jsx'"
- ❌ Two sidebars rendering simultaneously
- ❌ CSS from old navbar interfering with new topbar
- ❌ Build warnings about missing dependencies

---

## TC-UX-001 to TC-UX-008: UI/UX Consistency Tests

**Operator**: UAT Operator #2
**Focus**: Visual consistency, responsive design, user experience
**Acceptance Threshold**: ≥95% PASS (minor cosmetic issues acceptable)

### TC-UX-001: Responsive Breakpoints

**Objective**: Verify navigation adapts correctly at all screen sizes

**Test Steps:**

1. **Desktop Large (1920x1080)**
   - Open frontend in maximized browser
   - Expected:
     - Sidebar visible, 250px expanded
     - TopBar 60px height
     - Main content has margin-left to avoid overlap
     - No horizontal scrollbar

2. **Desktop Medium (1200x800)**
   - Resize viewport
   - Expected: Same as desktop large

3. **Tablet Landscape (992x768)**
   - Resize viewport
   - Expected:
     - Sidebar still visible (≥768px)
     - Slightly tighter spacing acceptable

4. **Tablet Portrait (768x1024)**
   - Resize viewport
   - Expected:
     - This is the BREAKPOINT
     - Sidebar SHOULD be visible (exactly 768px = desktop)
     - OR Drawer SHOULD appear (depends on CSS media query)
     - Test at 767px to confirm mobile behavior

5. **Mobile Large (576x800)**
   - Resize viewport
   - Expected:
     - Sidebar hidden
     - Drawer accessible via hamburger
     - TopBar responsive

6. **Mobile Medium (414x896) - iPhone**
   - Resize viewport
   - Expected: Same as mobile large

7. **Mobile Small (375x667) - iPhone SE**
   - Resize viewport
   - Expected: Same as mobile large

8. **Mobile Tiny (320x568) - Smallest supported**
   - Resize viewport
   - Expected:
     - Drawer width ≤280px to avoid horizontal scroll
     - TopBar buttons don't overflow
     - Text truncates gracefully

**Success Criteria:**
- ✅ Sidebar shown at ≥768px
- ✅ Drawer shown at <768px
- ✅ No horizontal scrollbar at any viewport
- ✅ All touch targets ≥44x44px (mobile)
- ✅ Text readable at all sizes
- ✅ No overlapping elements

**Defect Examples:**
- ❌ Sidebar shown on mobile (should be drawer)
- ❌ Horizontal scrollbar at 320px
- ❌ Buttons too small to tap (<44px)
- ❌ Text overflow without ellipsis
- ❌ Sidebar overlaps main content

---

### TC-UX-002: Touch Target Sizes (Mobile)

**Objective**: Verify all interactive elements meet 44x44px minimum

**Test Steps:**

1. **Measure TopBar Buttons (Mobile)**
   - Resize to 375px viewport
   - Right-click hamburger button → Inspect
   - Check computed dimensions
   - Expected: Width ≥44px, Height ≥44px
   - Repeat for: Logo, Search, User menu

2. **Measure Drawer Menu Items**
   - Open drawer on mobile
   - Inspect menu item links
   - Expected: Height ≥44px, full width clickable

3. **Measure Drawer Close Button**
   - Inspect X button in drawer header
   - Expected: ≥44x44px clickable area

4. **Touch Test** (if touch device available)
   - Use actual mobile device or tablet
   - Try to tap each button with thumb
   - Expected: Easy to hit, no mis-taps

**Success Criteria:**
- ✅ All buttons ≥44x44px on mobile
- ✅ Menu items ≥44px height
- ✅ No overlapping touch targets
- ✅ Comfortable tap experience

**Defect Examples:**
- ❌ Hamburger button only 30x30px
- ❌ Menu items 32px height (too small)
- ❌ Close button hard to tap
- ❌ Accidental double-taps on nearby buttons

---

### TC-UX-003: Visual Consistency Across Routes

**Objective**: Verify navigation looks identical on all pages

**Test Steps:**

1. **TopBar Consistency**
   - Navigate to each route:
     - /, /dashboard, /immobili, /affittuari, /contratti, etc.
   - On each route, verify:
     - TopBar height = 60px
     - Logo position identical
     - Hamburger icon identical
     - Background color consistent
     - Border/shadow consistent

2. **Sidebar Consistency (Desktop)**
   - Navigate to each route
   - Verify:
     - Sidebar width = 250px (expanded) or 60px (collapsed)
     - Background color consistent
     - Active item highlighting consistent
     - Font sizes consistent
     - Icon alignment consistent

3. **Drawer Consistency (Mobile)**
   - Switch to mobile viewport
   - Open drawer on each route
   - Verify:
     - Drawer width = 280px
     - Slide-in animation identical
     - Overlay opacity identical
     - Header layout identical
     - Footer identical

4. **Active State Highlighting**
   - On each route, verify active menu item:
     - Background color change
     - Border-left indicator (e.g., 4px blue bar)
     - Font weight change (bold)
     - Icon color change
   - Verify NO other items have active styling

**Success Criteria:**
- ✅ TopBar identical on all routes
- ✅ Sidebar styling consistent
- ✅ Drawer styling consistent
- ✅ Active states clearly visible
- ✅ No route-specific layout shifts

**Defect Examples:**
- ❌ TopBar height varies on different pages
- ❌ Sidebar wider on one page
- ❌ Active state missing on some routes
- ❌ Inconsistent icon colors
- ❌ Logo position shifts between pages

---

### TC-UX-004: Loading and Error States

**Objective**: Verify graceful handling of loading/error states

**Test Steps:**

1. **Menu Loading State**
   - Clear localStorage: `localStorage.clear()`
   - Throttle network: DevTools → Network → Slow 3G
   - Refresh page, login
   - Expected:
     - Sidebar shows loading spinner
     - "Caricamento..." text (expanded) or spinner only (collapsed)
     - No menu items visible
     - No console errors

2. **Menu Error State**
   - Stop backend server
   - Refresh frontend
   - Expected:
     - Sidebar shows error message
     - "Errore caricamento menu" text
     - "Riprova" retry button visible
     - Click "Riprova" attempts reload

3. **Empty Menu State** (simulate backend returning [])
   - Mock API to return empty array
   - Expected:
     - Sidebar shows empty state message
     - "Nessun elemento nel menu" or similar
     - No console errors

4. **Slow Navigation Feedback**
   - Throttle network again
   - Click menu item that loads data (e.g., /contratti)
   - Expected:
     - Immediate visual feedback (active state)
     - Page content shows loading state
     - Navigation doesn't feel "stuck"

**Success Criteria:**
- ✅ Loading spinner visible during fetch
- ✅ Error message clear and actionable
- ✅ Empty state handled gracefully
- ✅ Retry button functional
- ✅ No UI freeze during slow operations

**Defect Examples:**
- ❌ No loading indicator (user confused)
- ❌ Error crashes app
- ❌ Empty array shows error message
- ❌ Retry button doesn't work
- ❌ UI freezes during API call

---

### TC-UX-005: Animation and Transition Smoothness

**Objective**: Verify all animations are smooth and performant

**Test Steps:**

1. **Sidebar Collapse/Expand Animation**
   - Click hamburger to toggle sidebar
   - Expected:
     - Smooth width transition (0.3s ease-in-out)
     - Main content margin animates in sync
     - No text reflow jitter
     - 60fps animation (check DevTools → Performance)

2. **Drawer Slide-In/Out Animation**
   - Open drawer on mobile
   - Expected:
     - Smooth slide from left (0.3s)
     - Overlay fades in (0.2s)
     - Drawer doesn't "snap" into place
   - Close drawer
   - Expected: Reverse animation equally smooth

3. **Submenu Accordion Animation**
   - Expand submenu in sidebar
   - Expected:
     - Height animates smoothly
     - Arrow rotates 90° smoothly
     - No jump or flicker

4. **Active State Transition**
   - Navigate between routes
   - Expected:
     - Active highlight transitions smoothly
     - No flash of unstyled content
     - Previous active state fades out

5. **Performance Under Load**
   - Open DevTools → Performance
   - Record while toggling sidebar 10 times rapidly
   - Expected:
     - No dropped frames
     - CPU usage <50%
     - Memory stable (no leaks)

**Success Criteria:**
- ✅ All animations smooth (60fps)
- ✅ Consistent timing across animations
- ✅ No layout thrashing
- ✅ No memory leaks after 50 interactions
- ✅ Animations feel "native" and responsive

**Defect Examples:**
- ❌ Sidebar animation stutters
- ❌ Drawer snaps open (no transition)
- ❌ Accordion jumps instead of animating
- ❌ Dropped frames during toggle
- ❌ Memory increases with each toggle

---

### TC-UX-006: Focus and Hover States

**Objective**: Verify all interactive states are visually clear

**Test Steps:**

1. **Hover States (Desktop)**
   - Hover over each button in TopBar
   - Expected:
     - Background color change or opacity change
     - Cursor changes to pointer
     - Tooltip appears (if applicable)
   - Hover over menu items in sidebar
   - Expected:
     - Background highlight
     - Smooth transition (0.2s)

2. **Focus States (Keyboard)**
   - TAB through all interactive elements
   - Expected:
     - Visible focus ring (2px outline)
     - High contrast color (e.g., blue)
     - Focus ring never removed (no outline: none)
   - Focus on menu item, press SPACE
   - Expected: Focus ring remains visible during action

3. **Active/Pressed States**
   - Click and hold button
   - Expected:
     - Active state styling (darker background)
     - Provides tactile feedback
   - Release mouse
   - Expected: Returns to normal or hover state

4. **Disabled States** (if applicable)
   - Find any disabled menu items or buttons
   - Expected:
     - Reduced opacity (0.5)
     - Cursor: not-allowed
     - Tooltip explains why disabled

5. **High Contrast Mode** (accessibility)
   - Enable Windows High Contrast Mode or browser extension
   - Expected:
     - All navigation elements remain visible
     - Focus states clear
     - Active states distinguishable

**Success Criteria:**
- ✅ Hover states visible on all interactive elements
- ✅ Focus rings clearly visible
- ✅ Active states provide feedback
- ✅ Disabled states obvious
- ✅ High contrast mode supported

**Defect Examples:**
- ❌ No hover feedback
- ❌ Focus rings invisible (outline: none)
- ❌ Can't tell if button is active
- ❌ Disabled items look enabled
- ❌ High contrast mode breaks layout

---

### TC-UX-007: Color Contrast and Readability

**Objective**: Verify WCAG AA color contrast compliance

**Test Steps:**

1. **Sidebar Text Contrast**
   - Inspect menu item text color vs background
   - Use tool: WebAIM Contrast Checker or DevTools Lighthouse
   - Expected ratio: ≥4.5:1 for normal text, ≥3:1 for large text

2. **Active Item Contrast**
   - Check active menu item text vs active background
   - Expected: Still meets 4.5:1 ratio

3. **TopBar Contrast**
   - Check logo text vs TopBar background
   - Check icon colors vs background
   - Expected: All meet 4.5:1 ratio

4. **Drawer Overlay Contrast**
   - Check drawer content vs overlay (when open)
   - Expected: Overlay dark enough to distinguish drawer

5. **Font Sizes**
   - Measure all text in navigation
   - Expected minimum:
     - Body text: 14px (mobile), 16px (desktop)
     - Small text: 12px minimum
     - Icon size: 20px minimum

6. **Readability on Different Screens**
   - Test on:
     - Low-resolution monitor (1366x768)
     - High-DPI Retina display (2880x1800)
     - Mobile OLED screen
   - Expected: Text crisp and readable on all

**Success Criteria:**
- ✅ All text meets WCAG AA contrast (4.5:1)
- ✅ Large text meets 3:1
- ✅ Font sizes ≥14px on mobile, ≥16px on desktop
- ✅ Icons ≥20px
- ✅ Readable on all screen types

**Defect Examples:**
- ❌ Gray text on white background (3:1 ratio, fails)
- ❌ Active item text hard to read
- ❌ Font too small (10px) on mobile
- ❌ Icons tiny (16px)
- ❌ Blurry text on Retina displays

---

### TC-UX-008: No Layout Shift (CLS)

**Objective**: Verify zero cumulative layout shift during navigation

**Test Steps:**

1. **Initial Page Load**
   - Clear cache, hard reload (Ctrl+Shift+R)
   - Open DevTools → Lighthouse
   - Run performance audit
   - Expected: CLS score ≤0.1 (good)

2. **Sidebar Toggle Layout Shift**
   - Place cursor on specific word in main content
   - Toggle sidebar collapsed/expanded
   - Expected:
     - Word remains at same vertical position
     - Content shifts horizontally only (margin-left change)
     - No unexpected jumps

3. **Menu Load Layout Shift**
   - Clear localStorage, refresh
   - Login
   - Observe sidebar during menu load
   - Expected:
     - Sidebar height reserved before menu loads
     - No "pop-in" effect when menu appears
     - Page doesn't jump

4. **Route Change Layout Shift**
   - Navigate between routes with different content heights
   - Expected:
     - TopBar remains fixed (no shift)
     - Sidebar remains fixed (no shift)
     - Only main content area changes

5. **Drawer Open Layout Shift (Mobile)**
   - Open drawer
   - Expected:
     - Main content doesn't shift
     - Overlay appears smoothly
     - No horizontal scroll introduced

**Success Criteria:**
- ✅ Lighthouse CLS score ≤0.1
- ✅ Sidebar toggle doesn't shift content vertically
- ✅ Menu load doesn't cause layout jump
- ✅ Route changes don't affect navigation layout
- ✅ Drawer doesn't introduce horizontal scroll

**Defect Examples:**
- ❌ CLS score >0.25 (poor)
- ❌ Content jumps vertically when sidebar toggles
- ❌ Menu "pops in" causing page to shift
- ❌ TopBar position shifts on route change
- ❌ Horizontal scrollbar appears when drawer opens

---

## TC-INT-001 to TC-INT-006: Integration & E2E Tests

**Operator**: UAT Operator #3
**Focus**: End-to-end workflows, authentication, cross-route navigation
**Acceptance Threshold**: 100% PASS (critical business flows)

### TC-INT-001: Authentication Integration

**Objective**: Verify navigation integrates correctly with auth system

**Test Steps:**

1. **Unauthenticated State**
   - Open frontend without login
   - Expected:
     - Redirected to /login
     - TopBar visible (hamburger, logo)
     - Sidebar/Drawer NOT visible
     - No menu API call

2. **Login Flow**
   - Enter credentials: admin / admin123
   - Submit login
   - Expected:
     - Token stored in localStorage
     - Redirected to / or /dashboard
     - Menu API called with Bearer token
     - Sidebar/Drawer now visible

3. **Protected Route Access**
   - Logout, then manually navigate to: /immobili
   - Expected:
     - Redirected to /login
     - After login, redirected back to /immobili
     - Menu loads correctly

4. **Token Expiry Simulation**
   - Login successfully
   - Manually delete token: `localStorage.removeItem('access_token')`
   - Click any menu item
   - Expected:
     - API call fails with 401
     - Redirected to /login
     - Menu clears

5. **Role-Based Menu Items** (if implemented)
   - Login as admin
   - Expected: Admin-only menu items visible
   - Logout, login as regular user
   - Expected: Admin menu items hidden

**Success Criteria:**
- ✅ Navigation hidden when not authenticated
- ✅ Navigation appears after login
- ✅ Menu API uses correct auth token
- ✅ Token expiry handled gracefully
- ✅ Role-based menu filtering works

**Defect Examples:**
- ❌ Sidebar visible before login
- ❌ Menu API called without token
- ❌ App crashes on token expiry
- ❌ All menu items visible to all users
- ❌ Protected routes accessible without login

---

### TC-INT-002: Cross-Route Navigation Flow

**Objective**: Verify seamless navigation through multi-step workflows

**Test Steps:**

1. **Workflow: Create Property → View Property → Create Contract**
   - Login
   - Navigate: Sidebar → Immobili → Unità Immobiliari
   - Click "Crea Nuovo"
   - Fill form, submit
   - Expected: Redirected to property list, property visible
   - Click property name → Detail page
   - Expected: Navigation sidebar still present, active item highlighted
   - From property detail, click "Crea Contratto"
   - Expected: Navigate to contract form, property pre-filled
   - Menu state remains consistent throughout

2. **Workflow: Dashboard → Reports → Back to Dashboard**
   - Navigate: Sidebar → Dashboard
   - Click widget link (e.g., "Contratti Attivi")
   - Expected: Navigate to /contratti, filtered
   - Click browser back button
   - Expected: Return to dashboard, menu state preserved

3. **Deep Linking Workflow**
   - Copy URL of nested route: `/contratti/123/edit`
   - Open in new browser tab
   - Login
   - Expected:
     - Redirected to `/contratti/123/edit` after login
     - Sidebar auto-expands "Affitti" → "Contratti"
     - Active highlighting on "Contratti"

4. **Multi-Tab Navigation Consistency**
   - Open app in Tab 1, login
   - Collapse sidebar
   - Open app in Tab 2 (same browser)
   - Expected:
     - Tab 2 auto-authenticated (same token)
     - Sidebar state SAME as Tab 1 (localStorage sync)
   - Expand sidebar in Tab 2
   - Refresh Tab 1
   - Expected: Sidebar now expanded (localStorage updated)

**Success Criteria:**
- ✅ Navigation persists across all routes
- ✅ Active state updates correctly
- ✅ Browser back/forward works
- ✅ Deep linking auto-expands menus
- ✅ Multi-tab state syncs via localStorage

**Defect Examples:**
- ❌ Sidebar disappears on certain routes
- ❌ Active state doesn't update
- ❌ Back button breaks navigation
- ❌ Deep link doesn't expand parent menu
- ❌ Sidebar state differs between tabs

---

### TC-INT-003: Backend Menu API Integration

**Objective**: Verify frontend correctly consumes backend menu API

**Test Steps:**

1. **Menu API Structure Verification**
   - Login
   - Open DevTools → Network → XHR
   - Find request: GET `/api/v1/platform/menu/`
   - Check response format:
     ```json
     [
       {
         "id": "string",
         "label": "string",
         "path": "string",
         "icon": "string",
         "sequence": number,
         "parent_id": null | "string",
         "children": []
       }
     ]
     ```
   - Expected: Response matches NavigationContext expectations

2. **Dynamic Menu Rendering**
   - Verify menu items rendered match API response exactly
   - Expected:
     - Same labels
     - Same icon emojis
     - Same route paths
     - Correct hierarchy (parent-child)
     - Correct sequence order

3. **Menu Refresh on Auth Change**
   - Logout, login as different user (if available)
   - Expected:
     - Menu API called again
     - Menu items updated (if role-based)

4. **Error Handling - 500 Backend Error**
   - Simulate backend crash (or mock 500 response)
   - Expected:
     - Error message in sidebar: "Errore caricamento menu"
     - "Riprova" button visible
     - App remains functional (doesn't crash)

5. **Error Handling - Empty Menu Response**
   - Mock API to return `[]`
   - Expected:
     - Sidebar shows empty state message
     - No console errors
     - App remains functional

6. **Menu Caching Behavior** (if implemented)
   - Login, menu loads
   - Navigate to different routes
   - Expected: Menu API called only ONCE per session
   - Manual refresh: Menu API called again

**Success Criteria:**
- ✅ Menu API response correctly parsed
- ✅ Menu items rendered dynamically
- ✅ Hierarchy and sequence respected
- ✅ Error states handled gracefully
- ✅ Menu cached appropriately

**Defect Examples:**
- ❌ Menu API returns 200 but items don't render
- ❌ Wrong hierarchy (parent-child relationships broken)
- ❌ Sequence ignored (random order)
- ❌ App crashes on API error
- ❌ Menu API called on every route change (over-fetching)

---

### TC-INT-004: Module System Integration

**Objective**: Verify navigation works with dynamic module loading

**Test Steps:**

1. **Module Auto-Discovery**
   - Check browser console on page load
   - Expected logs:
     - "Loading modules..."
     - "Module loaded: immobili"
     - "Module loaded: affitti_lungo"
     - "Module loaded: anagrafica_italiana"

2. **Module Routes in Menu**
   - Verify menu includes module-specific routes:
     - Immobili section → Routes from immobili module
     - Affitti section → Routes from affitti_lungo module
   - Expected: Routes from manifest match menu items

3. **Dynamic Route Registration**
   - Navigate to module route: /hello (if hello_module exists)
   - Expected: Route renders correctly
   - Check menu for "Hello Module" item
   - Expected: Present if module registered

4. **Module Error Handling**
   - Simulate module load error (if possible)
   - Expected:
     - Error banner at top: "Errore caricamento moduli"
     - App continues to function
     - Static routes still accessible

5. **Admin Modules Page**
   - Navigate: Sidebar → Admin → Modules
   - Expected:
     - List of all installed modules
     - Module status indicators
     - Menu items from modules visible

**Success Criteria:**
- ✅ All modules auto-discovered
- ✅ Module routes in menu
- ✅ Dynamic routes navigable
- ✅ Module errors handled gracefully
- ✅ Admin page shows module list

**Defect Examples:**
- ❌ Module routes missing from menu
- ❌ Module route navigation broken
- ❌ Module error crashes app
- ❌ Admin page shows empty list
- ❌ Duplicate modules loaded

---

### TC-INT-005: Browser Compatibility

**Objective**: Verify navigation works across major browsers

**Test Steps:**

1. **Chrome/Chromium**
   - Open app in Chrome
   - Execute all critical flows
   - Expected: All features work

2. **Firefox**
   - Open app in Firefox
   - Test sidebar/drawer functionality
   - Expected: All features work, animations smooth

3. **Safari** (macOS/iOS if available)
   - Open app in Safari
   - Test touch interactions on iOS Safari
   - Expected: All features work, no webkit-specific bugs

4. **Edge**
   - Open app in Edge
   - Test navigation features
   - Expected: All features work

5. **Mobile Browsers**
   - Chrome Mobile (Android)
   - Safari Mobile (iOS)
   - Expected: Drawer works, touch targets adequate

**Browser-Specific Checks:**
- CSS Grid/Flexbox compatibility
- Touch event handling
- localStorage access
- Fetch API support
- CSS custom properties (variables)

**Success Criteria:**
- ✅ Works in Chrome, Firefox, Safari, Edge
- ✅ Mobile browsers fully functional
- ✅ No browser-specific console errors
- ✅ Animations smooth in all browsers

**Defect Examples:**
- ❌ Drawer doesn't open in Firefox
- ❌ Sidebar layout broken in Safari
- ❌ Touch events don't work in Chrome Mobile
- ❌ localStorage error in Edge

---

### TC-INT-006: Performance and Memory

**Objective**: Verify navigation doesn't degrade performance

**Test Steps:**

1. **Initial Load Performance**
   - Clear cache, hard reload
   - Open DevTools → Performance
   - Record page load
   - Expected metrics:
     - First Contentful Paint (FCP) <1.8s
     - Time to Interactive (TTI) <3.8s
     - Total Blocking Time (TBT) <300ms

2. **Navigation Performance**
   - Record performance while navigating 10 routes
   - Expected:
     - Route change <100ms
     - Menu API called only once
     - No performance degradation

3. **Memory Leak Test**
   - Open DevTools → Memory
   - Take heap snapshot (Baseline)
   - Toggle sidebar 50 times
   - Take heap snapshot (After)
   - Expected:
     - Memory increase <5MB
     - No detached DOM nodes (old navigation components)

4. **Sidebar Animation Performance**
   - Open DevTools → Performance
   - Record while toggling sidebar 20 times
   - Expected:
     - 60fps maintained (16.67ms per frame)
     - No long tasks >50ms
     - CPU usage <40%

5. **Drawer Animation Performance (Mobile)**
   - Switch to mobile viewport
   - Record while opening/closing drawer 20 times
   - Expected:
     - 60fps maintained
     - No scroll jank
     - Touch response <100ms

6. **Bundle Size Impact**
   - Run: `npm run build`
   - Check output bundle sizes
   - Compare to pre-refactor (if available)
   - Expected:
     - New navigation code <50KB
     - Overall bundle size increase <5%

**Success Criteria:**
- ✅ FCP <1.8s, TTI <3.8s
- ✅ Route changes <100ms
- ✅ No memory leaks after 50 toggles
- ✅ 60fps animations
- ✅ Bundle size increase <5%

**Defect Examples:**
- ❌ Page load >5s
- ❌ Memory grows to 100MB after 50 toggles
- ❌ Animation drops to 30fps
- ❌ Long tasks >200ms during navigation
- ❌ Bundle size increased 50%

---

## Risk Assessment

### High-Risk Areas (Priority Testing)

| Risk Area | Likelihood | Impact | Mitigation |
|-----------|-----------|--------|------------|
| **Mobile drawer not opening** | Medium | Critical | Test on real devices, multiple browsers |
| **Active route highlighting broken** | Low | High | Test all routes, deep linking |
| **Menu API integration failure** | Medium | Critical | Mock API responses, error handling |
| **Keyboard navigation broken** | Low | High | Thorough TAB testing, ARIA verification |
| **Sidebar state not persisted** | Low | Medium | Test localStorage read/write |
| **Memory leak on toggle** | Low | Medium | Performance profiling |
| **Old navigation still present** | Low | Critical | Visual inspection on all routes |

### Medium-Risk Areas

- Responsive breakpoint edge cases (767px vs 768px)
- Animation performance on low-end devices
- Browser compatibility (Safari webkit bugs)
- Multi-tab localStorage sync issues
- Backend menu API returns unexpected format

### Low-Risk Areas

- Color contrast issues (already WCAG compliant)
- Minor CSS inconsistencies across routes
- Tooltip positioning edge cases
- Search bar functionality (if not implemented)

---

## Test Execution Guidelines

### Operator Instructions

1. **Setup Your Environment**
   - Open frontend: http://192.168.1.2:3002/
   - Open backend API docs: http://192.168.1.2:8000/docs (to verify backend running)
   - Clear browser cache: Ctrl+Shift+Del → All time → Cached images/files
   - Close other tabs to avoid confusion
   - Open DevTools (F12) in separate window

2. **Test Execution Approach**
   - Follow test cases sequentially within your focus area
   - Mark each test step as ✅ PASS or ❌ FAIL
   - If FAIL, capture:
     - Screenshot (screenshot tool or DevTools)
     - Console errors (copy text)
     - Network errors (copy response)
     - Detailed description of unexpected behavior
   - Don't stop on first failure - complete all tests

3. **Exploratory Testing Freedom**
   - After completing structured tests, spend 5 minutes on exploratory testing
   - Try to "break" the navigation:
     - Rapid clicking
     - Double-clicking everything
     - Spamming ESC key
     - Resizing viewport mid-interaction
     - Opening 10 tabs simultaneously
     - Using browser back/forward rapidly
     - Switching between desktop/mobile sizes
   - Document any unexpected behavior

4. **Realistic User Simulation**
   - Make intentional "mistakes":
     - Click wrong menu item, use back button
     - Resize viewport mid-workflow
     - Let page sit idle for 5 minutes (test session timeout)
     - Open external link in new tab, return to app
   - Simulate different user personas:
     - **Rushed Admin**: Fast clicks, impatient, uses keyboard shortcuts
     - **Careful Data Clerk**: Deliberate clicks, reads everything
     - **Mobile Field Worker**: Touch-only, one-handed use, poor connection

5. **Reporting Format**
   - Use structured format for each defect:
     ```
     DEFECT ID: NAV-001
     Severity: CRITICAL | HIGH | MEDIUM | LOW
     Test Case: TC-NAV-002
     Summary: Drawer doesn't close on overlay click (mobile)
     Steps to Reproduce:
       1. Resize viewport to 375px
       2. Click hamburger to open drawer
       3. Click overlay (outside drawer panel)
       4. Expected: Drawer closes
       5. Actual: Drawer remains open
     Environment: Chrome 120, Ubuntu 22.04, 375x667 viewport
     Screenshot: nav-001-drawer-stuck.png
     Console Errors: None
     Workaround: ESC key closes drawer (but overlay click should also work)
     ```

6. **Time Management**
   - Operator #1 (Navigation Regression): ~8 minutes structured + 2 min exploratory = 10 min
   - Operator #2 (UI/UX Consistency): ~10 minutes structured + 2 min exploratory = 12 min
   - Operator #3 (Integration & E2E): ~12 minutes structured + 3 min exploratory = 15 min
   - If running behind, prioritize CRITICAL test cases first

7. **Communication Protocol**
   - No need to ask permission to proceed with tests
   - Report defects as you find them (don't wait for end)
   - If completely blocked (e.g., can't login), report immediately
   - Otherwise, work independently in parallel

---

## Acceptance Criteria

### Overall Test Campaign: PASS if:

1. ✅ **Zero CRITICAL defects** in navigation functionality
   - Navigation must be accessible (can open sidebar/drawer)
   - Menu items must be clickable
   - Routes must navigate correctly
   - No app crashes

2. ✅ **≤2 HIGH defects** with documented workarounds
   - Example acceptable HIGH: Active state missing on one route (workaround: visual check of URL)

3. ✅ **All core flows functional:**
   - Login → Navigate menu → Access all major routes
   - Desktop sidebar collapse/expand works
   - Mobile drawer open/close works
   - Keyboard navigation functional

4. ✅ **Accessibility compliance:**
   - Keyboard navigation works
   - ARIA attributes present
   - Focus indicators visible
   - Screen reader compatibility (if tested)

5. ✅ **Performance acceptable:**
   - Page load <3s
   - Navigation interactions <200ms
   - No memory leaks
   - Animations smooth (≥30fps, target 60fps)

### Overall Test Campaign: FAIL if:

- ❌ **Any CRITICAL defect** blocking core functionality
  - Cannot open sidebar/drawer
  - Cannot navigate to routes
  - App crashes on navigation
  - Menu doesn't load with no error message

- ❌ **>5 HIGH defects** without workarounds

- ❌ **Any accessibility violation** Level A (WCAG)
  - Keyboard navigation completely broken
  - No focus indicators
  - ARIA labels missing causing screen reader failure

- ❌ **Any data loss or security issue**
  - Token exposed in URL
  - localStorage not secure
  - XSS vulnerability in menu rendering

---

## Deliverables

### During Test Execution

1. **Real-Time Defect Log**
   - File: `/docs/uat/NAV_DEFECTS_{operator_number}.md`
   - Format: Markdown table with structured defect entries

2. **Screenshots**
   - Directory: `/docs/uat/screenshots/nav-refactor/`
   - Naming: `{operator}_{test_case}_{defect_id}_{description}.png`

### After Test Execution

3. **Individual Operator Reports** (3 files)
   - `/docs/uat/UAT_NAV_OPERATOR_1_REPORT.md` (Navigation Regression)
   - `/docs/uat/UAT_NAV_OPERATOR_2_REPORT.md` (UI/UX Consistency)
   - `/docs/uat/UAT_NAV_OPERATOR_3_REPORT.md` (Integration & E2E)
   - Format:
     ```markdown
     # Test Summary
     - Operator: #1
     - Test Cases Executed: 7
     - Passed: 6
     - Failed: 1
     - Duration: 12 minutes

     # Defects Found
     - CRITICAL: 0
     - HIGH: 1
     - MEDIUM: 0
     - LOW: 0

     # Detailed Results
     (Test case breakdown with ✅/❌)
     ```

4. **Consolidated UAT Report**
   - File: `/docs/uat/UAT_NAVIGATION_REFACTORING_REPORT.md`
   - Contents:
     - Executive Summary (1-page overview)
     - Aggregated defects from all 3 operators
     - Pass/Fail decision
     - Risk assessment
     - Recommendations

5. **Defect CSV** (if defects found)
   - File: `/docs/uat/NAV_DEFECTS_CONSOLIDATED.csv`
   - Columns: ID, Severity, Test Case, Operator, Summary, Status, Owner

6. **Executive Summary** (for stakeholders)
   - File: `/docs/uat/UAT_NAV_EXECUTIVE_SUMMARY.txt`
   - 1-page plain text summary suitable for email

---

## Rollback Plan

If test campaign FAILS with CRITICAL defects:

### Immediate Actions (within 1 hour)

1. **Stop any deployment plans**
2. **Document all CRITICAL defects** with reproduction steps
3. **Notify tech lead** with executive summary

### Investigation Phase (within 4 hours)

4. **Root cause analysis**:
   - Review git diff for refactor changes
   - Check if issue existed pre-refactor
   - Identify exact commit that introduced issue

5. **Impact assessment**:
   - Is this a complete rollback, or targeted fix?
   - Can we fix in <2 hours?

### Rollback Decision

**Option A: Targeted Fix** (if issue isolated)
- Fix specific component
- Re-run affected test cases only
- Deploy fix

**Option B: Full Rollback** (if widespread issues)
- Revert to pre-refactor commit (tag: `pre-nav-refactor`)
- Restore old Navbar.jsx, DynamicMenu.jsx
- Re-run full UAT on old version (should pass)
- Schedule refactor fix for next sprint

### Git Rollback Commands

```bash
# View refactor commits
git log --oneline --graph -10

# Rollback to specific commit (if needed)
git revert <commit-hash> --no-commit
git commit -m "Rollback: Navigation refactor due to UAT failures"

# OR hard reset (destructive, last resort)
git reset --hard <pre-refactor-commit>
git push --force origin main  # DANGEROUS - coordinate with team
```

---

## Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Test Pass Rate** | ≥95% | (Passed tests / Total tests) × 100 |
| **Defect Density** | ≤2 defects/module | Critical + High defects / 3 modules |
| **Zero Critical Defects** | 0 | Count of CRITICAL defects |
| **Performance Regression** | ≤+10% | (New load time - Old load time) / Old load time |
| **Accessibility Score** | ≥90/100 | Lighthouse Accessibility score |
| **Test Execution Time** | ≤15 min | Actual parallel execution time |

### Qualitative Metrics

- ✅ Navigation feels "intuitive" and "responsive"
- ✅ Mobile drawer UX comparable to native apps
- ✅ No "I can't find X" confusion from operators
- ✅ Keyboard navigation "just works" without documentation
- ✅ Visual consistency maintained across all routes

---

## Post-UAT Actions

### If PASS (≥95% success rate, 0 CRITICAL defects):

1. ✅ **Sign-off document** - Tech lead approval
2. ✅ **Deploy to production** (if applicable)
3. ✅ **Update documentation** - Architecture docs reflect new navigation
4. ✅ **Close refactor ticket** - Mark as complete
5. ✅ **Retrospective** - What went well, lessons learned
6. ✅ **Monitor production** - Watch for user-reported issues in first 48h

### If FAIL (CRITICAL defects or <95% success):

1. ❌ **Do NOT deploy**
2. ❌ **Triage defects** - Prioritize by severity
3. ❌ **Assign ownership** - Devs take specific defects
4. ❌ **Fix and retest** - Execute targeted regression tests
5. ❌ **Full UAT re-run** - If fixes extensive
6. ❌ **Document lessons learned** - Update refactor checklist

### If MEDIUM Issues Found (even if overall PASS):

- 🟡 Create GitHub issues for MEDIUM defects
- 🟡 Prioritize in next sprint backlog
- 🟡 Deploy with known issues documented
- 🟡 Monitor user feedback for impact

---

## Appendix A: Test Credentials

**Primary Test Account:**
- Username: `admin`
- Password: `admin123`
- Role: Administrator
- Permissions: Full access

**Backend Health Check:**
```bash
curl http://192.168.1.2:8000/health
# Expected: {"status": "healthy"}
```

**Frontend Health Check:**
```bash
curl http://192.168.1.2:3002/
# Expected: HTML page with <title>Gestione Affitti</title>
```

---

## Appendix B: Browser DevTools Shortcuts

| Action | Shortcut |
|--------|----------|
| Open DevTools | F12 or Ctrl+Shift+I |
| Toggle Device Toolbar (responsive) | Ctrl+Shift+M |
| Open Console | Ctrl+Shift+J |
| Open Network tab | Ctrl+Shift+E (Firefox) |
| Clear console | Ctrl+L |
| Hard reload (clear cache) | Ctrl+Shift+R |
| Screenshot (full page) | Ctrl+Shift+P → "screenshot" |
| Inspect element | Ctrl+Shift+C |
| Show Lighthouse | F12 → "Lighthouse" tab → Generate report |

---

## Appendix C: Common Issues and Quick Fixes

### Issue: Frontend not accessible at port 3002

**Check:**
```bash
lsof -i :3002
```

**Fix:**
```bash
cd /home/htpc/test/gestione-affitti/frontend
npm run dev -- --port 3002 --host 0.0.0.0
```

---

### Issue: Backend not responding

**Check:**
```bash
curl http://192.168.1.2:8000/docs
```

**Fix:**
```bash
cd /home/htpc/test/gestione-affitti/backend
source venv/bin/activate
python app/main.py
```

---

### Issue: Menu API returns 401 Unauthorized

**Root cause:** Token expired or missing

**Fix:**
1. Logout
2. Clear localStorage: `localStorage.clear()`
3. Login again
4. Verify token stored: `localStorage.getItem('access_token')`

---

### Issue: Sidebar doesn't appear after login

**Check:**
1. Open DevTools → Console
2. Look for errors: "useNavigation must be used within NavigationProvider"
3. Check if NavigationContext wrapper present in App.jsx

**Fix:**
- If error present, check git diff for App.jsx changes
- Verify `<NavigationProvider>` wraps `<AppLayout>`

---

### Issue: Drawer doesn't close on mobile

**Check:**
1. Verify viewport <768px
2. Check DevTools → Elements → `.drawer-overlay` present?
3. Check Console for event listener errors

**Workaround:**
- Use ESC key to close drawer
- Report as defect

---

## Appendix D: NavigationContext API Reference

For developers fixing defects:

```javascript
// NavigationContext exports
const {
  // Sidebar (desktop)
  sidebarOpen,        // boolean - current state
  setSidebarOpen,     // function - set state directly
  toggleSidebar,      // function - toggle state

  // Drawer (mobile)
  drawerOpen,         // boolean - current state
  setDrawerOpen,      // function - set state directly
  toggleDrawer,       // function - toggle state
  closeDrawer,        // function - close drawer (used by overlay/ESC)

  // Menu data
  menuItems,          // array - menu structure from backend
  menuLoading,        // boolean - true during fetch
  menuError,          // string | null - error message
  loadMenu,           // function - manual reload

  // Submenu state
  activeSubmenu,      // string | null - currently expanded submenu ID
  toggleSubmenu,      // function - toggle submenu accordion
} = useNavigation();
```

**localStorage Keys:**
- `sidebar-open`: `"true"` | `"false"` (persisted sidebar state)
- `access_token`: JWT token for API authentication

---

## Sign-Off

| Role | Name | Date | Signature | Status |
|------|------|------|-----------|--------|
| **UAT Manager** | Claude Code QA | 2025-12-04 | _________ | ⏳ Pending |
| **UAT Operator #1** | Navigation Tester | 2025-12-04 | _________ | ⏳ Ready |
| **UAT Operator #2** | UX Tester | 2025-12-04 | _________ | ⏳ Ready |
| **UAT Operator #3** | Integration Tester | 2025-12-04 | _________ | ⏳ Ready |
| **Tech Lead** | User | 2025-12-04 | _________ | ⏳ Awaiting results |
| **Product Owner** | User | 2025-12-04 | _________ | ⏳ Awaiting results |

---

## Status: READY FOR EXECUTION

**Created**: December 4, 2025
**Last Updated**: December 4, 2025
**Next Action**: Launch 3 UAT operators in parallel
**Estimated Total Time**: 15 minutes (parallel execution)

---

**END OF UAT PLAN**
