import { IconButton } from "@chakra-ui/react"
import { BsThreeDotsVertical } from "react-icons/bs"
import { MenuContent, MenuRoot, MenuTrigger } from "../ui/menu"

import type { NotePublic } from "@/client"
import DeleteNote from "../Notes/DeleteNote"
import EditNote from "../Notes/EditNote"

interface ItemActionsMenuProps {
  note: NotePublic
}

export const ItemActionsMenu = ({ note }: ItemActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton variant="ghost" color="inherit">
          <BsThreeDotsVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditNote note={note} />
        <DeleteNote id={note.id} />
      </MenuContent>
    </MenuRoot>
  )
}
