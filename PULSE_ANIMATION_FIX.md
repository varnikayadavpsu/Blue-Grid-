# Pulse Animation Fix - Critical Zones

## Problem
The pulse animation on critical zones (risk ≥ 81) was too aggressive:
- Markers appeared to throb and move
- `transform: scale(1.15)` caused 15% size change
- Visually distracting, looked glitchy
- Marker positions appeared to shift

## Solution

### BEFORE (aggressive):
```css
.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.8;
    transform: scale(1);  /* ❌ Causes visible size change */
  }
  50% {
    opacity: 1;
    transform: scale(1.15);  /* ❌ 15% growth */
  }
}
```

### AFTER (subtle):
```css
.pulse {
  animation: pulse 2.5s ease-in-out infinite;  /* ✓ Slower, smoother */
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.7;  /* ✓ Subtle opacity range */
    filter: drop-shadow(0 0 3px currentColor);  /* ✓ Minimal glow */
  }
  50% {
    opacity: 0.95;  /* ✓ Peak visibility */
    filter: drop-shadow(0 0 8px currentColor) drop-shadow(0 0 12px currentColor);  /* ✓ Soft halo */
  }
}
```

## Changes Made

### 1. Removed Position Changes
- ❌ Removed `transform: scale()` entirely
- ✓ Marker center stays perfectly fixed
- ✓ No apparent movement or position shift

### 2. Subtle Opacity Breathing
- Range: 0.7 → 0.95 (was 0.8 → 1.0)
- Gentle fade in/out, not jarring

### 3. Soft Glow Halo
- Resting state: 3px drop-shadow (barely visible)
- Peak state: 8px + 12px layered drop-shadows
- Creates gentle "breathing" halo around critical zones
- Uses `currentColor` so glow matches the red marker color

### 4. Slower Cycle
- Duration: 2.5s (was 2s)
- Easing: `ease-in-out` for smooth transitions
- More natural breathing rhythm

## Result

**Critical zones (risk 81+) now:**
- ✓ Stay perfectly centered (no position change)
- ✓ Have gentle opacity fade (0.7 → 0.95)
- ✓ Show soft red glow halo that "breathes"
- ✓ Cycle smoothly over 2.5 seconds
- ✓ Draw attention without being distracting

**Visual Effect:**
Imagine a gentle red glow that slowly brightens and dims around the marker, like a calm heartbeat or breathing pattern. The marker itself never moves or resizes - only the soft halo around it pulses.

## File Updated
- **index.html** (lines 471-484)
- **Applied to:** All zones with risk ≥ 81
- **Status:** ✓ Live at http://localhost:8000

## Testing
Open http://localhost:8000/index.html and look at critical (red) zones:
- Marker should stay perfectly still
- Soft glow should breathe slowly
- No visible throbbing or movement
