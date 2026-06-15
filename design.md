# Multimodal Video Search - Design System

> [!NOTE]
> This document details the visual design language, color palette, typography, and stylistic choices used in the Multimodal Video Search application. It also outlines recommendations for future UI enhancements, specifically focusing on introducing more dynamic animations.

## 1. Color Palette

The project utilizes a "Spiritual Warm / Earthy" palette, combining deep dark backgrounds with vibrant saffron and gold accents to create an ethereal and highly legible aesthetic.

### Backgrounds
- **Deep Background (`--bg-deep`)**: `#0C0908` - Used as the primary app background.
- **Mid Background (`--bg-mid`)**: `#17110C` - Used for slightly elevated surfaces.

### Accents & Brand Colors
- **Saffron (`--saffron`)**: `#F97316` - The primary vibrant orange accent.
- **Dim Saffron (`--saffron-dim`)**: `#C2410C` - Used for gradients and hover states.
- **Soft Gold (`--gold-soft`)**: `#FBBF24` - Secondary accent color for highlighting elements like tags or active navigation links.

### Typography Colors
- **Primary Text (`--text`)**: `#FFFFFF` - Pure white for maximum legibility on dark backgrounds.
- **Dim/Secondary Text (`--text-dim`)**: `#E6DFD5` - An off-white, earthy tone used for metadata and subtle text.

### Glassmorphism & Surfaces
The application relies heavily on translucent, blurred surfaces to create depth:
- **Glass Surface (`--glass`)**: `rgba(255, 255, 255, 0.03)`
- **Glass Hover (`--glass-hover`)**: `rgba(255, 255, 255, 0.06)`
- **Glass Border (`--glass-border`)**: `rgba(249, 115, 22, 0.15)` - A subtle saffron tint on borders.
- **Solid Surface (`--surface`)**: `rgba(24, 18, 14, 0.65)`

---

## 2. Typography

The typography system is designed to handle both English and complex scripts (like Marathi Devanagari) elegantly.

- **Primary Heading Font (`--font-head`)**: `'Inter', sans-serif`
- **Primary Body Font (`--font-body`)**: `'Inter', sans-serif`
- **Devanagari/Script Font (`--font-dev`)**: `'Tiro Devanagari Marathi', 'Noto Sans Devanagari', serif` - Used for quotes, spiritual texts, and prominent titles to give a traditional, serif feel.

---

## 3. Structural Tokens

- **Border Radius (`--radius`)**: `16px`
- **Large Border Radius (`--radius-lg`)**: `20px`

The application uses rounded corners extensively on cards, buttons, and input fields to maintain a modern, friendly appearance.

---

## 4. Current Design Elements & Animations

The UI currently implements several high-end visual features:
- **Backdrop Filters**: Heavy use of `backdrop-filter: blur(24px)` on headers and cards to create a frosted glass effect over the ethereal background.
- **Ethereal Glows**: The background uses large radial gradients (`radial-gradient`) with a slow breathing animation (`bg-breathe` at 20s) to create a spiritual ambiance.
- **Hover Micro-interactions**: 
  - Cards scale up (`transform: scale()`) and shift slightly (`translateY`).
  - Drop shadows pulse with saffron/gold tints on hover.
- **CSS Animations**: Includes basic structural animations like `fade-up` (cubic-bezier), `pulse-glow`, `fadeIn`, and `scaleUpFade` for modals.

---

## 5. UI Improvements & Animation Recommendations

> [!TIP]
> While the current design is aesthetically premium, incorporating more advanced animations and fluid transitions would significantly elevate the user experience, making the interface feel more alive and interactive.

To improve the application, we recommend adding the following animations:

### 1. Staggered List Entrance
When search results or stories are loaded, they should animate into view sequentially (staggered delay) rather than appearing all at once. This creates a more satisfying, cascading visual effect.

### 2. Page & Routing Transitions
Implement smooth transitions between the home page, search results, and library views. A subtle cross-fade with a slight scale effect can make navigation feel seamless.

### 3. Advanced Loading States
Replace basic fade animations with Lottie animations or custom SVG path animations (like a drawing Om symbol) during search requests or heavy data loading.

### 4. Interactive Micro-Animations
- **Ripple Effects**: Add ripple animations to buttons (Play, Search) when clicked.
- **Icon Animations**: Animate the icons within buttons (e.g., the play icon morphing into a pause icon, or the search icon slightly rotating on focus).
- **Smooth Expansion**: Use libraries like Framer Motion or CSS `grid-template-rows` transitions to smoothly expand/collapse the "Read More" sections or result cards.

### 5. Parallax Background
Enhance the existing `bg-breathe` background by making the radial gradients respond slightly to mouse movement or scrolling, adding a layer of depth (parallax effect).
