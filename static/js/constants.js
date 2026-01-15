// Global constants for the application
// Auto-detect base path from current URL
// If we're at /cooling-monitor/*, use /cooling-monitor/api
// If we're at /*, use /api
const pathPrefix = window.location.pathname.startsWith('/cooling-monitor') ? '/cooling-monitor' : '';
const API_BASE = pathPrefix + '/api';
