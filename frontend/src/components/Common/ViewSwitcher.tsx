import { IconButton, Box, Tooltip } from "@mui/material"
import { FiGrid, FiList } from "react-icons/fi"
import { useState } from "react"

export type ViewMode = "card" | "table"

interface ViewSwitcherProps {
  defaultView?: ViewMode
  onViewChange?: (view: ViewMode) => void
}

const ViewSwitcher = ({ defaultView = "card", onViewChange }: ViewSwitcherProps) => {
  const [view, setView] = useState<ViewMode>(defaultView)

  const handleViewChange = (newView: ViewMode) => {
    setView(newView)
    if (onViewChange) {
      onViewChange(newView)
    }
  }

  return (
    <Box sx={{ display: "flex", gap: 0.5, border: "1px solid", borderColor: "divider", borderRadius: 1 }}>
      <Tooltip title="Card View">
        <IconButton
          size="small"
          onClick={() => handleViewChange("card")}
          sx={{
            borderRadius: 0,
            backgroundColor: view === "card" ? "action.selected" : "transparent",
            "&:hover": {
              backgroundColor: view === "card" ? "action.selected" : "action.hover",
            },
          }}
        >
          <FiGrid />
        </IconButton>
      </Tooltip>
      <Tooltip title="Table View">
        <IconButton
          size="small"
          onClick={() => handleViewChange("table")}
          sx={{
            borderRadius: 0,
            backgroundColor: view === "table" ? "action.selected" : "transparent",
            "&:hover": {
              backgroundColor: view === "table" ? "action.selected" : "action.hover",
            },
          }}
        >
          <FiList />
        </IconButton>
      </Tooltip>
    </Box>
  )
}

export default ViewSwitcher
