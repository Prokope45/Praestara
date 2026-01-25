import { Container, Box, Typography } from "@mui/material"
import {
  Link as RouterLink,
  createFileRoute,
  redirect,
} from "@tanstack/react-router"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiLock, FiMail } from "react-icons/fi"

import type { Body_login_login_access_token as AccessToken } from "@/client"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { InputGroup } from "@/components/ui/input-group"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import Logo from "/assets/images/praestara-logo.png"
import { emailPattern, passwordRules } from "../utils"

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
})

function Login() {
  const { loginMutation, error, resetError } = useAuth()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AccessToken>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  const onSubmit: SubmitHandler<AccessToken> = async (data) => {
    if (isSubmitting) return

    resetError()

    try {
      await loginMutation.mutateAsync(data)
    } catch {
      // error is handled by useAuth hook
    }
  }

  return (
    <Container
      component="form"
      onSubmit={handleSubmit(onSubmit)}
      maxWidth="sm"
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Box
          component="img"
          src={Logo}
          alt="Logo"
          sx={{ width: 125, maxWidth: 'md' }}
        />
        <Typography variant="h3" fontWeight="bold">
          Praestara
        </Typography>
      </Box>
      
      <Field
        invalid={!!errors.username}
        errorText={errors.username?.message || (error ? 'Invalid credentials' : '')}
        sx={{ width: '100%' }}
      >
        <InputGroup
          startElement={<FiMail />}
          {...register("username", {
            required: "Username is required",
            pattern: emailPattern,
          })}
          placeholder="Email"
          type="email"
          fullWidth
        />
      </Field>

      <PasswordInput
        type="password"
        startElement={<FiLock />}
        {...register("password", passwordRules())}
        placeholder="Password"
        errors={errors}
      />

      <RouterLink to="/recover-password" style={{ alignSelf: 'flex-start', color: 'inherit' }}>
        Forgot Password?
      </RouterLink>

      <Button variant="contained" type="submit" loading={isSubmitting} size="medium" fullWidth>
        Log In
      </Button>

      <Typography>
        Don't have an account?{" "}
        <RouterLink to="/signup" style={{ color: 'inherit', fontWeight: 'bold' }}>
          Sign Up
        </RouterLink>
      </Typography>
    </Container>
  )
}
