# Widget System - Core Platform

## Overview

This directory contains the **platform-level widget infrastructure** that enables dynamic, modular widget loading without hardcoding module references.

## Architecture Principles

- **Platform Independence:** No imports from business modules
- **Dynamic Loading:** Widgets loaded on-demand via registry
- **Module Self-Registration:** Modules register their own widgets

## Components

### `WidgetComponentRegistry.js`
Dynamic registry that stores widget loaders. Modules register widgets at load time.

**API:**
```javascript
import widgetRegistry from './WidgetComponentRegistry'

// Register a widget (called by modules)
widgetRegistry.registerWidget(
  'MyWidget',              // component name
  'my_module',             // module ID
  () => import('./path')   // lazy loader
)

// Get widget component (called by platform)
const Component = await widgetRegistry.getComponent('MyWidget')

// Check registration
widgetRegistry.hasWidget('MyWidget')  // boolean

// Get info
widgetRegistry.getWidgetInfo('MyWidget')  // { moduleId, loaded }

// Get stats
widgetRegistry.getStats()  // { registered, loaded, modules }
```

### `LazyWidgetLoader.jsx`
React component that lazy-loads widgets from the registry.

**Usage:**
```jsx
import { LazyWidgetLoader } from '@/core/widgets'

<LazyWidgetLoader
  componentName="MyWidget"
  onError={(err) => console.error(err)}
/>
```

## For Module Developers

To add a widget to your module:

1. **Create widget component:**
   ```
   src/modules/{module}/components/Dashboard/MyWidget.jsx
   ```

2. **Register in module index.js:**
   ```javascript
   import { widgetRegistry } from '../../core/widgets'

   widgetRegistry.registerWidget(
     'MyWidget',
     'my_module',
     () => import('./components/Dashboard/MyWidget')
   )
   ```

3. **That's it!** Platform will lazy-load it automatically.

## Debugging

In development, access registry via console:

```javascript
window.__widgetRegistry.getRegisteredWidgets()
window.__widgetRegistry.getStats()
```

## See Also

- `/WIDGET_DEVELOPMENT_GUIDE.md` - Complete development guide
- `/CLAUDE.md` - Project architecture overview
