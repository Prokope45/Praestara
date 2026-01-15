import { Container, Typography, Stack } from "@mui/material"
import { useColorMode } from "@/components/ui/color-mode"
import { Radio, RadioGroup } from "@/components/ui/radio"

const Appearance = () => {
  const { colorMode, setColorMode } = useColorMode()

  return (
    <Container maxWidth="lg">
      <Typography variant="h6" sx={{ py: 2 }}>
        Appearance
      </Typography>

      <RadioGroup
        value={colorMode}
        onValueChange={(value) => setColorMode(value as "light" | "dark")}
      >
        <Stack spacing={1}>
          <Radio value="light">Light Mode</Radio>
          <Radio value="dark">Dark Mode</Radio>
        </Stack>
      </RadioGroup>
    </Container>
  )
}

export default Appearance
