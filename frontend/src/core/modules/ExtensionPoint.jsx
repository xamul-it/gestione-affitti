/**
 * Extension Point Component
 *
 * Allows modules to inject UI components at specific points.
 *
 * Usage:
 *   <ExtensionPoint name="immobile.detail.tabs" immobileId={id} />
 *
 * Modules can register components:
 *   moduleRegistry.registerExtension('my_module', 'immobile.detail.tabs', {
 *     component: MyTabComponent,
 *     order: 10
 *   });
 */
import { Fragment } from 'react';
import moduleRegistry from './ModuleRegistry';

export function ExtensionPoint({ name, ...props }) {
  const extensions = moduleRegistry.getExtensions(name);

  if (extensions.length === 0) {
    console.log(`[ExtensionPoint] No extensions registered for: ${name}`);
    return null;
  }

  console.log(`[ExtensionPoint] Rendering ${extensions.length} extensions for: ${name}`);

  return (
    <>
      {extensions.map((extension, index) => {
        const Component = extension.component;

        if (!Component) {
          console.warn(`[ExtensionPoint] Extension ${index} has no component for: ${name}`);
          return null;
        }

        // Merge props from extension config with passed props
        const mergedProps = {
          ...extension.props,
          ...props,
        };

        return (
          <Fragment key={`extension-${name}-${extension.moduleName}-${index}`}>
            <Component {...mergedProps} />
          </Fragment>
        );
      })}
    </>
  );
}

export default ExtensionPoint;
