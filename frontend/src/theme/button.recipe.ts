import { defineRecipe } from "@chakra-ui/react"

export const buttonRecipe = defineRecipe({
  base: {
    fontWeight: "bold",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 2,
    transition: "all 0.2s ease",
  },
  variants: {
    variant: {
      solid: {
        bg: "primary.emphasis",
        color: "primary.default",
        _hover: {
          bg: "secondary.default",
          _dark: {
            bg: "secondary.emphasis",
          }
        },
      },
      subtle: {
        bg: "button.subtle",
        color: "button.subtle",
        _hover: {
          bg: "brand.100",
          _dark: {
            bg: "brand.600",
          }
        },
      },
      ghost: {
        bg: "transparent",
        color: "fg.default",
        _hover: {
          bg: "bg.subtle",
        },
      },
    },
  },
})
