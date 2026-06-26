import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

/**
 * mountSmartFill - Mounts the SmartFill AI widget onto a target DOM container.
 * 
 * @param {string|HTMLElement} targetElement - DOM element or container ID to mount into.
 * @param {Object} config - Configuration options passed from the host ERP/portal.
 * @returns {Object} Plugin handle with API functions (like unmount).
 */
export function mountSmartFill(targetElement, config = {}) {
  let element = targetElement;
  if (typeof targetElement === 'string') {
    element = document.getElementById(targetElement);
  }

  if (!element) {
    console.error(`[SmartFill Mounter] Target container not found: "${targetElement}"`);
    return null;
  }

  // Create style-isolated wrapper class
  const wrapper = document.createElement('div');
  wrapper.className = 'smartfill-plugin-root';
  element.appendChild(wrapper);

  const root = ReactDOM.createRoot(wrapper);
  root.render(
    <React.StrictMode>
      <App config={config} />
    </React.StrictMode>
  );

  // Return API handles for host integration control
  return {
    unmount: () => {
      root.unmount();
      wrapper.remove();
    }
  };
}

// Register globally on window for host script embedding
if (typeof window !== 'undefined') {
  window.SmartFillPlugin = {
    mount: mountSmartFill
  };
}

// Standalone Fallback: If we have <div id="root">, auto-mount (e.g. local dev / production SPA view)
const defaultRoot = document.getElementById('root');
if (defaultRoot) {
  // Only auto-mount if we are not explicitly running in an embedded environment
  if (!window.__SMARTFILL_EMBEDDED__) {
    mountSmartFill(defaultRoot);
  }
}
