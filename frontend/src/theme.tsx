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
            value: { _light: "{colors.brand.50}", _dark: "#1a1a1a" } // Darker anthracite color for dark mode
          },
          surface: {
            value: { _light: "{colors.brand.100}", _dark: "#2a2a2a" } // Slightly lighter anthracite for surfaces
          },
          subtle: {
            value: { _light: "{colors.brand.50}", _dark: "#3a3a3a" }, // Subtle text for buttons, etc.
          },
          muted: {
            value: { _light: "{colors.brand.50}", _dark: "#2a2a2a" } // Slightly darker purple for contrast
          },
          // Custom token for your table requirement
          table: {
            value: { _light: "#ffffff", _dark: "{colors.brand.500}" }
          },
          // BUTTON BACKGROUNDS (Static - same in both modes)
          // button: {
          //   primary: { value: { _light: "{colors.brand.200}", _dark: "{colors.brand.600}" }},
          //   secondary: { value: "{colors.brand.600}" },
          //   subtle: { value: "{colors.brand.100}" },
          // }
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
          // button: {
          //   primary: { value: "{colors.brand.50}" },
          //   subtle: { value: "{colors.brand.500}" },
          // }
        },
        accent: {
          fg: { value: "{colors.brand.500}" },
          emphasis: { value: "{colors.brand.200}" },
        },
        // Primary and secondary color mappings
        primary: {
          default: { value: "{colors.brand.500}" }, // Deep Purple
          emphasis: { value: "{colors.brand.200}" }, // Peach
          subtle: { value: "{colors.brand.100}" },   // Apricot
        },
        secondary: {
          default: { value: "{colors.brand.600}" }, // Muted Purple
          emphasis: { value: "{colors.brand.200}" }, // Peach
          subtle: { value: "{colors.brand.100}" },   // Apricot
        },
        success: {
          default: { value: "#48bb78" },
          emphasis: { value: "#68d391" },
        },
        warning: {
          default: { value: "#ed8936" },
          emphasis: { value: "#f6ad55" },
        },
        danger: {
          default: { value: "#f56565" },
          emphasis: { value: "#fc8181" },
        },
        info: {
          default: { value: "{colors.brand.200}" }, // Peach for info
          emphasis: { value: "{colors.brand.100}" }, // Apricot for info emphasis
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
      },
      "& th": {
        color: "primary.default",
        bg: { _light: "primary.subtle", _dark: "primary.default" },
      },
      "& tr:hover": {
        bg: { _light: "secondary.subtle", _dark: "secondary.default" },
      },
    },
    // Link styling with primary colors
    "a, .link": {
      color: "primary.default",
      _hover: {
        color: "primary.emphasis",
        textDecoration: "underline",
      },
    },
    // Button styling enhancements
    "button, .button": {
      _focus: {
        boxShadow: "0 0 0 3px rgba(82, 47, 117, 0.3)",
      },
    },
    // Primary button styling
    ".primary-button": {
      bg: "primary.default",
      color: "white",
      _hover: {
        bg: "primary.emphasis",
      },
    },
    // Secondary button styling
    ".secondary-button": {
      bg: "secondary.default",
      color: "white",
      _hover: {
        bg: "secondary.emphasis",
      },
    },
    // Success button styling
    ".success-button": {
      bg: "success.default",
      color: "white",
      _hover: {
        bg: "success.emphasis",
      },
    },
    // Warning button styling
    ".warning-button": {
      bg: "warning.default",
      color: "white",
      _hover: {
        bg: "warning.emphasis",
      },
    },
    // Danger button styling
    ".danger-button": {
      bg: "danger.default",
      color: "white",
      _hover: {
        bg: "danger.emphasis",
      },
    },
    // Info button styling
    ".info-button": {
      bg: "info.default",
      color: "primary.default",
      _hover: {
        bg: "info.emphasis",
      },
    },
    ".main-link": {
      color: { _light: "brand.500", _dark: "brand.200" },
      fontWeight: "bold",
    },
  },
})
