import { Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText } from "@mui/material"
import { Link as RouterLink } from "@tanstack/react-router"
import {
  QuestionAnswerOutlined, HomeOutlined, ContentPasteOutlined,
  MapOutlined, SettingsOutlined, PeopleOutlined
} from "@mui/icons-material"
import type { IconType } from "react-icons/lib"

import useAuth from "@/hooks/useAuth"

const ClipboardIcon = ContentPasteOutlined as IconType
const UsersIcon = PeopleOutlined as IconType

const items = [
  { icon: HomeOutlined as IconType, title: "Dashboard", path: "/" },
  { icon: ContentPasteOutlined as IconType, title: "Questionnaires", path: "/questionnaires" },
  { icon: MapOutlined as IconType, title: "Value Map", path: "/value-map" },
  { icon: QuestionAnswerOutlined as IconType, title: "Chat", path: "/chat" },
  // { icon: FiFileText, title: "Notes", path: "/notes" },
  // { icon: FiCompass, title: "Orientations", path: "/orientations" },
  { icon: SettingsOutlined as IconType, title: "User Settings", path: "/settings" },
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
  const { user: currentUser } = useAuth()

  const onboardingItem: Item = { icon: ClipboardIcon, title: "Onboarding", path: "/onboarding" }
  const baseItems = [items[0], onboardingItem, ...items.slice(1)]
  const finalItems: Item[] = currentUser?.is_superuser
    ? [...baseItems, { icon: UsersIcon, title: "Admin", path: "/admin" }]
    : baseItems

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
