import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material"
import { Skeleton } from "../ui/skeleton"

const PendingItems = () => (
  <TableContainer component={Paper} sx={{ mt: 2 }}>
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell width="30%">Title</TableCell>
          <TableCell width="30%">Description</TableCell>
          <TableCell width="10%">Actions</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {[...Array(5)].map((_, index) => (
          <TableRow key={index}>
            <TableCell>
              <Skeleton h="20px" />
            </TableCell>
            <TableCell>
              <Skeleton h="20px" />
            </TableCell>
            <TableCell>
              <Skeleton h="20px" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
)

export default PendingItems
