import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// =============================================================================
// Frontend Logging Utility
// =============================================================================

/**
 * Log levels for the frontend logger
 */
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4
};

/**
 * Current log level - can be toggled via dev tools or settings
 * Set to DEBUG in development, WARN in production
 */
let currentLogLevel = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? LOG_LEVELS.DEBUG
  : LOG_LEVELS.WARN;

/**
 * Log storage for debugging (keeps last 100 entries)
 */
const logHistory = [];
const MAX_LOG_HISTORY = 100;

/**
 * Format a log message with timestamp and level
 */
function formatLogMessage(level, category, message, data) {
  const timestamp = new Date().toISOString();
  return {
    timestamp,
    level,
    category,
    message,
    data,
    formatted: `[${timestamp}] [${level}] [${category}] ${message}`
  };
}

/**
 * Store log entry in history
 */
function storeLog(entry) {
  logHistory.push(entry);
  if (logHistory.length > MAX_LOG_HISTORY) {
    logHistory.shift();
  }
}

/**
 * Frontend Logger - provides structured logging for debugging
 *
 * Usage:
 *   import { logger } from '$lib/utils';
 *
 *   logger.debug('Hardware', 'Relay toggled', { relayId: 1, state: 'on' });
 *   logger.info('API', 'Status fetched successfully');
 *   logger.warn('System', 'Connection unstable');
 *   logger.error('Hardware', 'Failed to control pump', { pumpId: 2, error });
 *
 * Categories:
 *   - Hardware: Relay, pump, flow meter, EC/pH operations
 *   - API: Network requests and responses
 *   - System: General system events
 *   - UI: User interface events
 *   - Job: Job orchestration events
 */
export const logger = {
  /**
   * Debug level logging - verbose details for development
   */
  debug(category, message, data = null) {
    if (currentLogLevel <= LOG_LEVELS.DEBUG) {
      const entry = formatLogMessage('DEBUG', category, message, data);
      storeLog(entry);
      console.debug(`%c${entry.formatted}`, 'color: #64748b', data || '');
    }
  },

  /**
   * Info level logging - general information
   */
  info(category, message, data = null) {
    if (currentLogLevel <= LOG_LEVELS.INFO) {
      const entry = formatLogMessage('INFO', category, message, data);
      storeLog(entry);
      console.info(`%c${entry.formatted}`, 'color: #0ea5e9', data || '');
    }
  },

  /**
   * Warning level logging - potential issues
   */
  warn(category, message, data = null) {
    if (currentLogLevel <= LOG_LEVELS.WARN) {
      const entry = formatLogMessage('WARN', category, message, data);
      storeLog(entry);
      console.warn(`%c${entry.formatted}`, 'color: #f59e0b', data || '');
    }
  },

  /**
   * Error level logging - errors and failures
   */
  error(category, message, data = null) {
    if (currentLogLevel <= LOG_LEVELS.ERROR) {
      const entry = formatLogMessage('ERROR', category, message, data);
      storeLog(entry);
      console.error(`%c${entry.formatted}`, 'color: #ef4444', data || '');
    }
  },

  /**
   * Set the current log level
   * @param {string} level - 'debug', 'info', 'warn', 'error', 'none'
   */
  setLevel(level) {
    const upperLevel = level.toUpperCase();
    if (LOG_LEVELS[upperLevel] !== undefined) {
      currentLogLevel = LOG_LEVELS[upperLevel];
      console.info(`[Logger] Log level set to ${upperLevel}`);
    }
  },

  /**
   * Get the current log level name
   */
  getLevel() {
    return Object.keys(LOG_LEVELS).find(key => LOG_LEVELS[key] === currentLogLevel);
  },

  /**
   * Get log history for debugging
   * @param {number} count - Number of recent entries to return
   * @param {string} category - Optional category filter
   */
  getHistory(count = 50, category = null) {
    let entries = logHistory.slice(-count);
    if (category) {
      entries = entries.filter(e => e.category === category);
    }
    return entries;
  },

  /**
   * Clear log history
   */
  clearHistory() {
    logHistory.length = 0;
    console.info('[Logger] History cleared');
  },

  /**
   * Export logs for debugging
   */
  export() {
    return JSON.stringify(logHistory, null, 2);
  }
};

// Expose logger to window for debugging in dev tools
if (typeof window !== 'undefined') {
  window.__logger = logger;
  window.__setLogLevel = (level) => logger.setLevel(level);
}