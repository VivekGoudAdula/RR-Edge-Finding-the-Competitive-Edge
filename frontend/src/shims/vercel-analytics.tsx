import React from 'react';

/**
 * Local fallback shim for @vercel/analytics/react when node_modules is offline.
 * On Vercel production deployments, the official npm package is resolved.
 */
export const Analytics: React.FC = () => null;
