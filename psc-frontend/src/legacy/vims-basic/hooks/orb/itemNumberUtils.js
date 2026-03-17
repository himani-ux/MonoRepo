// src/utils/orb/itemNumberUtils.js

export const getItemNumber = (code, line, lineIdx, defaultItemNo = '') => {
  let itemNo = '';

  // First line gets the default item number
  if (lineIdx === 0) {
    itemNo = defaultItemNo;
  } else {
    // Code-specific logic
    switch (code) {
      case 'A':
        if (line.startsWith('TANK(S) BALLASTED')) {
          itemNo = '1';
        } else if (line.includes('TANK CLEANED SINCE') || line.includes('NOT CLEANED – PREVIOUS OIL')) {
          itemNo = '2';
        } else if (line.startsWith('START BALLAST')) {
          itemNo = '4.1';
        } else if (line.includes('START') && line.includes('HRS')) {
          itemNo = '3.1';
        } else if (line.includes('RINSING') || line.includes('STEAMING') || line.includes('CHEMICAL')) {
          itemNo = '3.2';
        } else if (line.startsWith('CLEANING WATER TO')) {
          itemNo = '3.3';
        } else if (line.includes('BALLAST QUANTITY')) {
          itemNo = '4.2';
        }
        break;

      case 'B':
        if (lineIdx === 1 || /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)) {
          itemNo = '6';
        } else if (lineIdx === 2 || /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)) {
          itemNo = '7';
        } else if (line.includes('KNOTS')) {
          itemNo = '8';
        } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
          itemNo = '9.1';
        } else if (line.includes('TO RECEPTION FACILITY')) {
          itemNo = '9.2';
        } else if (line.includes('M³')) {
          itemNo = '10';
        }
        break;

      case 'C':
        if (lineIdx === 1 && line.includes('M³')) {
          itemNo = '11.2';
        } else if (lineIdx === 2 && line.includes('M³')) {
          itemNo = '11.3';
        } else if (line.includes('COLLECTED FROM')) {
          itemNo = '11.4';
        } else if (line.includes('RECEPTION FACILITY')) {
          itemNo = '12.1';
        } else if (line.includes('TRANSFERRED TO') && line.includes('TANK')) {
          itemNo = '12.2';
        } else if (line.includes('INCINERATED')) {
          itemNo = '12.3';
        } else if (line.includes('EVAPORATED') || line.includes('DRAINED')) {
          itemNo = '12.4';
        }
        break;

      case 'D':
        if (lineIdx === 0) {
          itemNo = '13';
        }
        if (lineIdx === 1 && line.startsWith('START:')) {
          itemNo = '14';
        } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
          itemNo = '15.1';
        } else if (line.includes('TO PORT RECEPTION FACILITIES OF')) {
          itemNo = '15.2';
        } else if ((line.includes('TRANSFERRED TO') || line.includes('RETAINED IN TANK')) && (lineIdx === 2)) {
          itemNo = '15.3';
        }
        break;

      case 'F':
        if (lineIdx === 0) {
          itemNo = '19';
        } else if (lineIdx === 1 || line.includes('HRS')) {
          itemNo = '20';
        } else if (lineIdx === 2 && line.trim().length > 0) {
          itemNo = '21';
        }
        break;

      case 'G':
        if (lineIdx === 0) {
          itemNo = '22';
        }
        if (lineIdx === 1 || /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)) {
          itemNo = '23';
        }
        if (lineIdx === 2) {
          itemNo = '24';
        } else if (lineIdx === 3) {
          itemNo = '25';
        }
        break;

      case 'H':
        if (line.startsWith('PLACE:')) {
          itemNo = '26.1';
        } else if (
          line.startsWith('TIME:') ||
          line.includes('BUNKERING START') ||
          line.includes('BUNKERING END') ||
          line.includes('START') ||
          line.includes('END TIME')
        ) {
          itemNo = '26.2';
        } else if (line.includes('FUEL OIL BUNKERED IN TANKS')) {
          itemNo = '26.3';
        } else if (line.includes('LUBE BUNKERED IN TANKS')) {
          itemNo = '26.4';
        }
        break;

      case 'I':
        itemNo = '';
        break;

      default:
        if (line.includes('M³') || line.includes('MT')) {
          itemNo = '10';
        }
        break;
    }

    // Reset if SIGNED
    if (line.startsWith('SIGNED:')) {
      itemNo = '';
    }
  }

  return itemNo;
};
