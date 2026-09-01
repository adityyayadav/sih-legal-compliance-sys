package com.packsure.backend;

import com.packsure.backend.support.AbstractIntegrationTest;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class AuthAndUserApiTest extends AbstractIntegrationTest {

    @Test
    void register_then_login_then_me() throws Exception {
        String token = registerInspector("alice", "alice@test.com", "secret123");

        mvc.perform(get("/api/users/me").header("Authorization", bearer(token)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("alice@test.com"))
                .andExpect(jsonPath("$.role").value("INSPECTOR"));
    }

    @Test
    void register_ignores_role_in_body() throws Exception {
        var res = mvc.perform(post("/api/auth/register").contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of(
                                "username", "mallory", "email", "mallory@test.com",
                                "password", "secret123", "role", "ADMIN"))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.role").value("INSPECTOR"))
                .andReturn();
        String token = readJson(res.getResponse().getContentAsString()).get("token").asText();
        mvc.perform(get("/api/users/me").header("Authorization", bearer(token)))
                .andExpect(jsonPath("$.role").value("INSPECTOR"));
    }

    @Test
    void duplicate_email_returns_409() throws Exception {
        registerInspector("bob", "bob@test.com", "secret123");
        mvc.perform(post("/api/auth/register").contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of(
                                "username", "bob2", "email", "bob@test.com", "password", "secret123"))))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409));
    }

    @Test
    void short_password_returns_400_with_field_error() throws Exception {
        mvc.perform(post("/api/auth/register").contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of(
                                "username", "x", "email", "x@test.com", "password", "short"))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.fieldErrors.password").exists());
    }

    @Test
    void wrong_password_returns_401() throws Exception {
        registerInspector("carol", "carol@test.com", "secret123");
        mvc.perform(post("/api/auth/login").contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of("email", "carol@test.com", "password", "nope"))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void me_without_token_returns_401() throws Exception {
        mvc.perform(get("/api/users/me")).andExpect(status().isUnauthorized());
    }

    @Test
    void unknown_route_returns_404_not_500() throws Exception {
        String token = registerInspector("dave", "dave@test.com", "secret123");
        mvc.perform(get("/api/does-not-exist").header("Authorization", bearer(token)))
                .andExpect(status().isNotFound());
    }
}
