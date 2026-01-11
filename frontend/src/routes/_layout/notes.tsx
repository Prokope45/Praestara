import {
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"

import { ItemsService } from "../../client"
import { ItemActionsMenu } from "../../components/Common/ItemActionsMenu"
import AddNote from "../../components/Notes/AddNote"
import PendingItems from "../../components/Pending/PendingItems"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination"

const notesSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 5

function getNotesQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      ItemsService.readItems({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["notes", { page }],
  }
}

export const Route = createFileRoute("/_layout/notes")({
  component: Notes,
  validateSearch: (search) => notesSearchSchema.parse(search),
})

function NotesTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getNotesQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: { [key: string]: string }) => ({ ...prev, page }),
    })

  const notes = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingItems />
  }

  if (notes.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any notes yet</EmptyState.Title>
            <EmptyState.Description>
              Add a new note to get started
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  return (
    <>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            {/* <Table.ColumnHeader w="30%">ID</Table.ColumnHeader> */}
            <Table.ColumnHeader w="30%">Title</Table.ColumnHeader>
            <Table.ColumnHeader w="30%">Description</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {notes?.map((note) => (
            <Table.Row key={note.id} opacity={isPlaceholderData ? 0.5 : 1}>
              {/* <Table.Cell truncate maxW="30%">
                {note.id}
              </Table.Cell> */}
              <Table.Cell truncate maxW="30%">
                {note.title}
              </Table.Cell>
              {/* TODO: Rename to preview; truncate and only show body without html. */}
              <Table.Cell
                color={!note.description ? "gray" : "inherit"}
                truncate
                maxW="30%"
              >
                {note.description || "N/A"}
              </Table.Cell>
              <Table.Cell width="10%">
                <ItemActionsMenu note={note} />
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
      <Flex justifyContent="flex-end" mt={4}>
        <PaginationRoot
          count={count}
          pageSize={PER_PAGE}
          onPageChange={({ page }) => setPage(page)}
        >
          <Flex>
            <PaginationPrevTrigger />
            <PaginationItems />
            <PaginationNextTrigger />
          </Flex>
        </PaginationRoot>
      </Flex>
    </>
  )
}

function Notes() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Notes Management
      </Heading>
      <AddNote />
      <NotesTable />
    </Container>
  )
}
