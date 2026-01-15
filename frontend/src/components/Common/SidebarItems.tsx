import { Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText } from "@mui/material"
import { useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink } from "@tanstack/react-router"
import { FiFileText, FiHome, FiSettings, FiUsers } from "react-icons/fi"
import type { IconType } from "react-icons/lib"

import type { UserPublic } from "@/client"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiFileText, title: "Notes", path: "/notes" },
  { icon: FiFileText, title: "Tasks", path: "/tasks" },
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
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])

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
