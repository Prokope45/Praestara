import { Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText } from "@mui/material"
import { Link as RouterLink } from "@tanstack/react-router"

import type { IconType } from "react-icons/lib"
import { FiMap } from "react-icons/fi";
import { FiHome } from "react-icons/fi";
import { FiClipboard } from "react-icons/fi";
import { FiSettings } from "react-icons/fi";
import { FiUsers } from "react-icons/fi";
import { HiOutlineChatAlt2 } from "react-icons/hi";

import useAuth from "@/hooks/useAuth"

const items = [
  { icon: FiHome as IconType, title: "Dashboard", path: "/" },
  { icon: FiClipboard as IconType, title: "Questionnaires", path: "/questionnaires" },
  { icon: FiMap as IconType, title: "Value Map", path: "/value-map" },
  { icon: HiOutlineChatAlt2 as IconType, title: "Chat", path: "/chat" },
  { icon: FiSettings as IconType, title: "User Settings", path: "/settings" },
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

  const finalItems: Item[] = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items

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
