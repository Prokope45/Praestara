import { Container, Typography, Tabs, Tab, Box } from "@mui/material"
import { createFileRoute } from "@tanstack/react-router"
import * as React from "react"

import Appearance from "@/components/UserSettings/Appearance"
import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import useAuth from "@/hooks/useAuth"

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const tabsConfig = [
  { value: "my-profile", title: "My profile", component: UserInformation },
  { value: "password", title: "Password", component: ChangePassword },
  { value: "appearance", title: "Appearance", component: Appearance },
  { value: "danger-zone", title: "Danger zone", component: DeleteAccount },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
})

function UserSettings() {
  const { user: currentUser } = useAuth()
  const [value, setValue] = React.useState(0)

  const finalTabs = currentUser?.is_superuser
    ? tabsConfig.slice(0, 3)
    : tabsConfig

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue)
  }

  if (!currentUser) {
    return null
  }

  return (
    <Container maxWidth={false}>
      <Typography 
        variant="h4" 
        component="h1" 
        sx={{ 
          pt: 6, 
          textAlign: { xs: "center", md: "left" } 
        }}
      >
        User Settings
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: "divider", mt: 3 }}>
        <Tabs value={value} onChange={handleChange} aria-label="user settings tabs">
          {finalTabs.map((tab, index) => (
            <Tab key={tab.value} label={tab.title} id={`settings-tab-${index}`} />
          ))}
        </Tabs>
      </Box>
      {finalTabs.map((tab, index) => (
        <TabPanel key={tab.value} value={value} index={index}>
          <tab.component />
        </TabPanel>
      ))}
    </Container>
  )
}
