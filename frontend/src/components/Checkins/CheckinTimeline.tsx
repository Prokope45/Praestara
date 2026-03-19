import { Box, CircularProgress, Stack, Tooltip, Typography } from "@mui/material"
import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"
import { CheckinsService } from "@/client"
import type { CheckinPublic } from "@/client"

interface CheckinTimelineProps {
  selectedCheckins: Set<string>
  toggleSelection: (id: string) => void
  days?: number
}

export default function CheckinTimeline({ selectedCheckins, toggleSelection, days = 7 }: CheckinTimelineProps) {
  // Fetch recent checkins for the timeline
  const { data: checkinsResponse, isLoading: isLoadingCheckins } = useQuery({
    queryKey: ["checkins", "timeline", days],
    queryFn: () => CheckinsService.readCheckinTimeline({ days }),
  })

  // Build timeline nodes
  const timelineNodes = useMemo(() => {
    const today = new Date()
    const daysArray = Array.from({ length: days }, (_, i) => {
      const d = new Date(today)
      d.setDate(d.getDate() - i)
      return d
    }).reverse()

    const formatDate = (date: Date) => {
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
    }

    return daysArray.map((date) => {
      const dateStr = formatDate(date)
      const dayCheckins =
        checkinsResponse?.data.filter((c: CheckinPublic) => {
          return formatDate(new Date(c.created_at)) === dateStr
        }) || []

      const morning = dayCheckins.find((c: CheckinPublic) => c.type === "morning")
      const evening = dayCheckins.find((c: CheckinPublic) => c.type === "evening")

      return { date, dateStr, morning, evening }
    })
  }, [checkinsResponse?.data, days])

  if (isLoadingCheckins) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    )
  }

  return (
    <Box sx={{ minWidth: "max-content", position: "relative", px: 2 }}>
      {/* Connector Line */}
      <Box
        sx={{
          position: "absolute",
          bottom: "15px",
          left: 0,
          right: 0,
          height: 2,
          bgcolor: "grey.200",
          zIndex: 0,
        }}
      />
      <Stack
        direction="row"
        spacing={4}
        sx={{ position: "relative", zIndex: 1, justifyContent: "space-between" }}
      >
        {timelineNodes.map((node) => (
          <Box
            key={node.dateStr}
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              bgcolor: "background.paper",
              px: 1,
            }}
          >
            <Typography
              variant="caption"
              sx={{ mb: 1, color: "text.secondary", fontWeight: 500 }}
            >
              {node.date.toLocaleDateString(undefined, {
                weekday: "short",
                month: "short",
                day: "numeric",
              })}
            </Typography>
            <Stack direction="row" spacing={1}>
              <Tooltip
                title={
                  node.morning
                    ? `Morning: ${node.morning.text}`
                    : "No morning check-in"
                }
              >
                <Box
                  onClick={() =>
                    node.morning && toggleSelection(node.morning.id)
                  }
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: node.morning ? "pointer" : "default",
                    bgcolor: node.morning
                      ? selectedCheckins.has(node.morning.id)
                        ? "primary.main"
                        : "primary.light"
                      : "grey.200",
                    color: node.morning
                      ? selectedCheckins.has(node.morning.id)
                        ? "primary.contrastText"
                        : "primary.contrastText"
                      : "grey.400",
                    transition: "all 0.2s",
                    "&:hover": node.morning
                      ? {
                          transform: "scale(1.1)",
                          bgcolor: selectedCheckins.has(node.morning.id)
                            ? "primary.dark"
                            : "primary.main",
                        }
                      : {},
                    boxShadow:
                      node.morning && selectedCheckins.has(node.morning.id)
                        ? 2
                        : 0,
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: "bold" }}>
                    M
                  </Typography>
                </Box>
              </Tooltip>

              <Tooltip
                title={
                  node.evening
                    ? `Evening: ${node.evening.text}`
                    : "No evening check-in"
                }
              >
                <Box
                  onClick={() =>
                    node.evening && toggleSelection(node.evening.id)
                  }
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: node.evening ? "pointer" : "default",
                    bgcolor: node.evening
                      ? selectedCheckins.has(node.evening.id)
                        ? "primary.main"
                        : "primary.light"
                      : "grey.200",
                    color: node.evening
                      ? selectedCheckins.has(node.evening.id)
                        ? "primary.contrastText"
                        : "primary.contrastText"
                      : "grey.400",
                    transition: "all 0.2s",
                    "&:hover": node.evening
                      ? {
                          transform: "scale(1.1)",
                          bgcolor: selectedCheckins.has(node.evening.id)
                            ? "secondary.dark"
                            : "secondary.main",
                        }
                      : {},
                    boxShadow:
                      node.evening && selectedCheckins.has(node.evening.id)
                        ? 2
                        : 0,
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: "bold" }}>
                    E
                  </Typography>
                </Box>
              </Tooltip>
            </Stack>
          </Box>
        ))}
      </Stack>
    </Box>
  )
}
