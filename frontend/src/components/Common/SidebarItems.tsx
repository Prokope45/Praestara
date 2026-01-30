import { Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText } from "@mui/material"
<<<<<<< HEAD
import { Link as RouterLink } from "@tanstack/react-router"
import { FiHome, FiSettings, FiUsers, FiMap, FiClipboard } from "react-icons/fi"
import type { IconType } from "react-icons/lib"

import useAuth from "@/hooks/useAuth"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiMap, title: "Value Map", path: "/value-map" },
  { icon: FiClipboard, title: "Chat", path: "/chat" },
=======
import { useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink } from "@tanstack/react-router"
import { FiFileText, FiHome, FiSettings, FiUsers, FiCompass, FiClipboard } from "react-icons/fi"
import type { IconType } from "react-icons/lib"

import type { UserPublic } from "@/client"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiClipboard, title: "Questionnaires", path: "/questionnaires" },
  { icon: FiFileText, title: "Notes", path: "/notes" },
  { icon: FiCompass, title: "Orientations", path: "/orientations" },
>>>>>>> 143f201b1c0eb0505243029a56878d6568d99d9f
  { icon: FiSettings, title: "User Settings", path: "/settings" },
]

interface SidebarItemsProps {
  onClose?: () => void
}

interface Item {
  icon: IconType
  title: string
  path: string
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
<<<<<<< HEAD
  const { user: currentUser } = useAuth()

  const onboardingItem: Item = { icon: FiClipboard, title: "Onboarding", path: "/onboarding" }
  const baseItems = [items[0], onboardingItem, ...items.slice(1)]
  const finalItems: Item[] = currentUser?.is_superuser
    ? [...baseItems, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : baseItems
=======
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])

  const finalItems: Item[] = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items
>>>>>>> 143f201b1c0eb0505243029a56878d6568d99d9f

  return (
    <>
      <Typography 
        variant="caption" 
        sx={{ px: 4, py: 2, fontWeight: 'bold', display: 'block' }}
      >
        Menu
      </Typography>
      <List>
        {finalItems.map(({ icon: Icon, title, path }) => (
          <ListItem key={title} disablePadding>
            <ListItemButton
              component={RouterLink}
              to={path}
              onClick={onClose}
              sx={{
                gap: 2,
                px: 4,
                py: 2,
                '&:hover': {
                  bgcolor: 'secondary.main',
                  color: 'secondary.contrastText',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 'auto', color: 'inherit' }}>
                <Icon />
              </ListItemIcon>
              <ListItemText 
                primary={title} 
                primaryTypographyProps={{ fontSize: 'small' }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </>
  )
}

export default SidebarItems
