import { IconButton } from "@mui/material"
import { BsThreeDotsVertical } from "react-icons/bs"
import { Menu } from "../ui/menu"
import { useState } from "react"

import type { ItemPublic } from "@/client"
import DeleteNote from "../Notes/DeleteNote"
import EditNote from "../Notes/EditNote"

interface ItemActionsMenuProps {
  note: ItemPublic
}

export const ItemActionsMenu = ({ note }: ItemActionsMenuProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  return (
    <>
      <IconButton
        onClick={handleClick}
        size="small"
        aria-label="note actions"
      >
        <BsThreeDotsVertical />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
      >
        <EditNote note={note} />
        <DeleteNote id={note.id} />
      </Menu>
    </>
  )
}
