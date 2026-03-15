import { Outlet, createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/alignment")({
  component: AlignmentLayout,
})

function AlignmentLayout() {
  return <Outlet />
}
