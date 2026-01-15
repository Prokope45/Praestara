import { Container, Typography } from "@mui/material"

import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  return (
    <Container maxWidth="lg">
      <Typography variant="h6" sx={{ py: 2 }}>
        Delete Account
      </Typography>
      <Typography>
        Permanently delete your data and everything associated with your
        account.
      </Typography>
      <DeleteConfirmation />
    </Container>
  )
}

export default DeleteAccount
