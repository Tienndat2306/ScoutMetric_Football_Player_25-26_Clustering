---
name: Pitch Analytics System
colors:
  surface: '#f9f9ff'
  surface-dim: '#d3daea'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eefe'
  surface-container-high: '#e2e8f8'
  surface-container-highest: '#dce2f3'
  on-surface: '#151c27'
  on-surface-variant: '#4a4455'
  inverse-surface: '#2a313d'
  inverse-on-surface: '#ebf1ff'
  outline: '#7b7487'
  outline-variant: '#ccc3d8'
  surface-tint: '#732ee4'
  primary: '#630ed4'
  on-primary: '#ffffff'
  primary-container: '#7c3aed'
  on-primary-container: '#ede0ff'
  inverse-primary: '#d2bbff'
  secondary: '#5e5c6e'
  on-secondary: '#ffffff'
  secondary-container: '#e4e0f5'
  on-secondary-container: '#646274'
  tertiary: '#4e4e58'
  on-tertiary: '#ffffff'
  tertiary-container: '#666670'
  on-tertiary-container: '#e7e5f1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d2bbff'
  on-primary-fixed: '#25005a'
  on-primary-fixed-variant: '#5a00c6'
  secondary-fixed: '#e4e0f5'
  secondary-fixed-dim: '#c7c4d8'
  on-secondary-fixed: '#1b1a29'
  on-secondary-fixed-variant: '#464555'
  tertiary-fixed: '#e3e1ed'
  tertiary-fixed-dim: '#c7c5d1'
  on-tertiary-fixed: '#1a1b23'
  on-tertiary-fixed-variant: '#46464f'
  background: '#f9f9ff'
  on-background: '#151c27'
  surface-variant: '#dce2f3'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 20px
  margin: 32px
---

## Brand & Style

The brand personality is analytical, sophisticated, and forward-thinking. Designed for scouts, analysts, and club directors, the design system prioritizes data density without sacrificing legibility. 

The design style is **Corporate / Modern** with a lean toward high-performance sports aesthetics. It utilizes a clean, airy "White-Label" feel that allows player data and clustering visualizations to take center stage. The use of soft lavender and violet as primary accents creates a distinctive identity that feels premium and tech-oriented, moving away from the common "grass-green" clichés of football applications.

## Colors

The palette is anchored in a high-contrast relationship between pure whites and deep violets. 

- **Primary:** A vibrant Violet (#7C3AED) used for critical actions, selected states, and data points that require immediate attention.
- **Secondary/Lavender:** Soft washes of purple (#EDE9FE) are used for hover states and subtle background differentiation in UI containers.
- **Surface & Background:** The application uses a slightly off-white background to reduce eye strain, while cards and containers use pure white to pop from the canvas.
- **Clustering Palettes:** For data visualization, additional shades of purple, indigo, and slate are used to differentiate player clusters while maintaining a monochromatic harmony.

## Typography

This design system utilizes **Inter** for its exceptional performance in data-heavy environments. The typeface offers a tall x-height which ensures that player names and numerical statistics remain legible even at smaller sizes. 

Headlines use a tighter letter-spacing and heavier weights to provide a sense of authority. Labels for data axes and table headers use an uppercase styling with increased tracking to create a clear visual distinction between descriptive metadata and functional content.

## Layout & Spacing

The system follows a **Fluid Grid** model built on a 4px baseline. Layouts are structured using a 12-column grid for the main dashboard content, allowing for flexible arrangements of charts and data tables.

Padding within data containers is generous (24px) to ensure that complex charts have "room to breathe." Sidebars are fixed at 280px, while the main content area expands to fill the viewport, ensuring the player clustering graphs can utilize all available horizontal space.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layers** and **Ambient Shadows**. 

- **Level 0 (Background):** Soft gray-white (#F9FAFB).
- **Level 1 (Cards/Containers):** Pure white with a very soft, diffused shadow (0px 4px 20px rgba(124, 58, 237, 0.05)). The shadow is slightly tinted with the primary purple to maintain color harmony.
- **Level 2 (Dropdowns/Modals):** Higher elevation with a more pronounced shadow to indicate temporary overlay status.

Borders are kept minimal, using 1px strokes of light lavender (#F5F3FF) to define boundaries without adding visual clutter.

## Shapes

The shape language is consistently **Rounded**, evoking a modern and accessible feel. 

- **Standard Elements:** Buttons, input fields, and small cards use a 0.5rem (8px) radius.
- **Large Containers:** Dashboard widgets and main content blocks use a 1rem (16px) radius.
- **Active Indicators:** Selection pills and status badges utilize a full "pill" radius for maximum distinction.

## Components

### Buttons & Inputs
- **Primary Action:** Solid violet background with white text. High contrast, 8px corner radius.
- **Comboboxes:** Input fields feature a subtle chevron icon. On focus, the border transitions to a 2px violet stroke with a soft purple glow.
- **Checkboxes:** When active, these show a solid violet fill with a white checkmark, utilizing the `rounded-sm` property.

### Data Visualization Containers
- **Chart Cards:** Must include a header row with a Title (Title-sm) and an Actions area for filtering or exporting data. 
- **Tooltips:** Dark-themed tooltips (near-black) provide high contrast against the light UI, appearing when hovering over data points in the clustering scatter plots.

### List & Tables
- **Player Rows:** Features a hover state using the Secondary Lavender color. 
- **Status Chips:** Used for "Position" or "Cluster Group," these chips use low-saturation versions of the cluster color with high-saturation text for readability.

### Clustering Specifics
- **Cluster Highlights:** When a cluster is selected, non-relevant data points should drop to 10% opacity, while the active cluster maintains full saturation with a primary violet glow effect.