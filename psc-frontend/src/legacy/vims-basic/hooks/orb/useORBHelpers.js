// src/hooks/useORBHelpers.js
// Shared date/time formatting helpers and geo utilities for ORB components

export const useORBHelpers = () => {
  /** Format ISO string → "DD-MMM-YYYY : HH:MM HRS" */
  const formatToDisplay = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    const day = String(d.getDate()).padStart(2, '0');
    const month = ['JAN','FEB','MAR','APR','MAY','JUN',
                   'JUL','AUG','SEP','OCT','NOV','DEC'][d.getMonth()];
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${day}-${month}-${year} : ${hours}:${minutes} HRS`;
  };

  /** Format any date to "YYYY-MM-DDTHH:mm" in local time (for datetime-local inputs) */
  const formatToDateTimeLocal = (date) => {
    const d = new Date(date);
    d.setSeconds(0, 0);
    const offset = d.getTimezoneOffset();
    const local = new Date(d.getTime() - offset * 60000);
    return local.toISOString().slice(0, 16);
  };

  /** Returns a Date object for yesterday at 00:00 */
  const yesterdayDate = () => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    d.setHours(0, 0, 0, 0);
    return d;
  };

  /** Format ISO date → "DD-MMM-YYYY" (used in table display) */
  const formatDate = (isoDate) => {
    if (!isoDate) return '';
    const d = new Date(isoDate);
    return d.toLocaleDateString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric'
    }).toUpperCase().replace(/ /g, '-');
  };

  /**
   * Detect IMO special sea areas by lat/lon.
   * Returns area name string or null if open ocean.
   */
  const getSpecialAreaFromPosition = (pos) => {
    if (!pos) return null;
    const { latitude: lat, longitude: lon } = pos;
    if (lat >= 30 && lat <= 46 && lon >= -7 && lon <= 37) return 'Mediterranean Sea';
    if (lat >= 12 && lat <= 28 && lon >= 32 && lon <= 44) return 'Red Sea';
    if (lat >= 54 && lat <= 66 && lon >= 10 && lon <= 31) return 'Baltic Sea';
    if (lat >= 41 && lat <= 47 && lon >= 27 && lon <= 42) return 'Black Sea';
    if (lat >= 31 && lat <= 32 && lon >= 35 && lon <= 36) return 'Dead Sea';
    if (lat <= -60) return 'Antarctic Area';
    return null;
  };

  /**
   * Build a decimal lat/lon object from degree/minute/direction parts.
   * Returns null if any part is missing.
   */
  const buildPosition = (latDeg, latMin, latDir, lonDeg, lonMin, lonDir) => {
    if (latDeg === '' || latMin === '' || !latDir ||
        lonDeg === '' || lonMin === '' || !lonDir) return null;
    const latitude  = (parseInt(latDeg) + parseInt(latMin) / 60) * (latDir === 'S' ? -1 :  1);
    const longitude = (parseInt(lonDeg) + parseInt(lonMin) / 60) * (lonDir === 'W' ? -1 :  1);
    return { latitude, longitude };
  };

  return {
    formatToDisplay,
    formatToDateTimeLocal,
    yesterdayDate,
    formatDate,
    getSpecialAreaFromPosition,
    buildPosition,
  };
};
