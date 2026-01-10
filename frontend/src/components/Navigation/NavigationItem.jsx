import { Link } from 'react-router-dom';
import { useState } from 'react';
import { renderIcon } from './iconRegistry.jsx';
import './NavigationItem.css';

/**
 * NavigationItem - Recursive navigation item component
 *
 * Handles:
 * - Links with icons
 * - Nested submenus (accordion)
 * - Active state highlighting
 * - Collapsed sidebar mode (icons only)
 * - Keyboard navigation
 */

function NavigationItem({ item, collapsed, currentPath, level = 0 }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = item.children && item.children.length > 0;
  const isActive = currentPath === item.path || currentPath.startsWith(item.path + '/');

  const handleToggle = (e) => {
    if (hasChildren) {
      e.preventDefault();
      e.stopPropagation();
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <li
      className={`nav-item ${isActive ? 'nav-item-active' : ''} ${level > 0 ? 'nav-item-child' : ''}`}
      role="none"
    >
      {item.path && item.path !== '#' ? (
        // Link item (with optional children)
        <div className="nav-link-wrapper">
          <Link
            to={item.path}
            className="nav-link"
            role="menuitem"
            aria-current={isActive ? 'page' : undefined}
            title={collapsed ? item.label : undefined}
          >
            {item.icon && renderIcon(item.icon)}
            {!collapsed && <span className="nav-label">{item.label}</span>}
          </Link>
          {!collapsed && hasChildren && (
            <button
              className={`nav-arrow-btn ${isExpanded ? 'nav-arrow-open' : ''}`}
              onClick={handleToggle}
              aria-label="Espandi sottomenu"
              aria-expanded={isExpanded}
            >
              ›
            </button>
          )}
        </div>
      ) : (
        // Group/folder item (no link, just expands)
        <button
          className="nav-link nav-link-group"
          onClick={handleToggle}
          role="menuitem"
          aria-expanded={isExpanded}
          aria-haspopup={hasChildren}
          title={collapsed ? item.label : undefined}
        >
          {item.icon && renderIcon(item.icon)}
          {!collapsed && <span className="nav-label">{item.label}</span>}
          {!collapsed && hasChildren && (
            <span
              className={`nav-arrow ${isExpanded ? 'nav-arrow-open' : ''}`}
              aria-hidden="true"
            >
              ›
            </span>
          )}
        </button>
      )}

      {/* Submenu */}
      {hasChildren && !collapsed && isExpanded && (
        <ul className="nav-submenu" role="menu">
          {item.children.map((child) => (
            <NavigationItem
              key={child.id}
              item={child}
              collapsed={false}
              currentPath={currentPath}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

export default NavigationItem;
