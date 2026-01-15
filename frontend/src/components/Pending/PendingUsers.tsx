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

const PendingUsers = () => (
  <TableContainer component={Paper} sx={{ mt: 2 }}>
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell width="20%">Full name</TableCell>
          <TableCell width="25%">Email</TableCell>
          <TableCell width="15%">Role</TableCell>
          <TableCell width="20%">Status</TableCell>
          <TableCell width="20%">Actions</TableCell>
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

export default PendingUsers
