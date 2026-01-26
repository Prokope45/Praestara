import { Card, CardContent, CardActions, Typography, Box, Chip } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import type { OrientationPublic } from "../../types/orientations"
import OrientationActionsMenu from "./OrientationActionsMenu"

interface OrientationCardProps {
  orientation: OrientationPublic
  isPlaceholderData?: boolean
  onDelete?: () => void
}

const OrientationCard = ({ orientation, isPlaceholderData = false, onDelete }: OrientationCardProps) => {
  const navigate = useNavigate()

  const totalTraits = orientation.traits?.length || 0
  const averageValue =
    totalTraits > 0
      ? Math.round(
          (orientation.traits?.reduce((sum, trait) => sum + trait.value, 0) || 0) / totalTraits
        )
      : 0

  const handleClick = () => {
    navigate({
      to: "/orientations",
      search: (prev: Record<string, unknown>) => ({
        ...prev,
        orientationId: orientation.id,
      }),
    })
  }

  return (
    <Card
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        opacity: isPlaceholderData ? 0.5 : 1,
        transition: "transform 0.2s, box-shadow 0.2s",
        cursor: "pointer",
        "&:hover": {
          transform: "translateY(-4px)",
          boxShadow: 4,
        },
      }}
      onClick={handleClick}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>
          {orientation.title}
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            overflow: "hidden",
            textOverflow: "ellipsis",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
          }}
        >
          {orientation.description || "No description"}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
          <Chip label={`${totalTraits} traits`} size="small" variant="outlined" />
          {totalTraits > 0 && (
            <Chip
              label={`${averageValue}% avg`}
              size="small"
              color={averageValue >= 70 ? "success" : "default"}
            />
          )}
        </Box>
      </CardContent>
      <CardActions
        sx={{ justifyContent: "flex-end", pt: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <OrientationActionsMenu orientation={orientation} onDelete={onDelete} />
      </CardActions>
    </Card>
  )
}

export default OrientationCard
