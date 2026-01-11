import { createSystem, defaultConfig } from "@chakra-ui/react"
import { buttonRecipe } from "./theme/button.recipe"

/**
 * Color theme: 
 * Deep Purple: #522f75 (Brand/Main)
 * Muted Purple: #987ca2 (Secondary)
 * Ghost White: #f8f7ff (Background)
 * Apricot: #ffeedd (Subtle accent)
 * Peach: #ffd8be (Accent)
 */

export const system = createSystem(defaultConfig, {
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: "#f8f7ff" },   // Ghost White
          100: { value: "#ffeedd" },  // Apricot
          200: { value: "#ffd8be" },  // Peach
          500: { value: "#522f75" },  // Deep Purple
          600: { value: "#987ca2" },  // Muted Purple
        },
      },
    },
    semanticTokens: {
      colors: {
        // Semantic background colors with Dark Mode support
        bg: {
          canvas: { 
            value: { _light: "{colors.brand.50}", _dark: "{colors.brand.500}" } 
          },
          surface: { 
            value: { _light: "{colors.brand.100}", _dark: "{colors.brand.500}" } 
          },
          subtle: {
            value: { _light: "{colors.brand.50}", _dark: "{colors.brand.500}" }, // Subtle text for buttons, etc.
          },
          muted: { 
            value: { _light: "{colors.brand.50}", _dark: "#42265e" } // Slightly darker purple for contrast
          },
          // Custom token for your table requirement
          table: {
            value: { _light: "#ffffff", _dark: "{colors.brand.500}" }
          },
          // BUTTON BACKGROUNDS (Static - same in both modes)
          button: {
            primary: { value: { _light: "{colors.brand.200}", _dark: "{colors.brand.600}" }},
            secondary: { value: "{colors.brand.600}" },
            subtle: { value: "{colors.brand.100}" },
          }
        },
        // Semantic foreground (text) colors
        fg: {
          default: { 
            value: { _light: "{colors.brand.500}", _dark: "{colors.brand.50}" } 
          },
          muted: { 
            value: { _light: "{colors.brand.600}", _dark: "{colors.brand.200}" } 
          },
          // BUTTON TEXT (Static - same in both modes)
          button: {
            primary: { value: "{colors.brand.50}" },
            subtle: { value: "{colors.brand.500}" },
          }
        },
        accent: {
          fg: { value: "{colors.brand.500}" },
          emphasis: { value: "{colors.brand.200}" },
        },
      },
    },
    recipes: {
      button: buttonRecipe,
    },
  },
  globalCss: {
    body: {
      bg: "bg.canvas",
      color: "fg.default",
      fontSize: "0.875rem",
      margin: 0,
      padding: 0,
      transition: "background-color 0.2s ease, color 0.2s ease",
    },
    // Table override
    table: {
      bg: "bg.table",
      width: "100%",
      "& th, & td": {
        borderColor: { _light: "brand.200", _dark: "brand.600" },
      }
    },
    ".main-link": {
      color: { _light: "brand.500", _dark: "brand.200" },
      fontWeight: "bold",
    },
  },
})