package com.packsure.backend.support;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.packsure.backend.common.Role;
import com.packsure.backend.user.User;
import com.packsure.backend.user.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;

import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Base for API integration tests: full context, MockMvc, H2 ({@code test}
 * profile), each test method wrapped in a transaction that rolls back.
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
public abstract class AbstractIntegrationTest {

    /** Plain instance — Boot 4 defaults to Jackson 3, so no Jackson-2 ObjectMapper bean exists. */
    protected final ObjectMapper json = new ObjectMapper();

    @Autowired
    protected MockMvc mvc;
    @Autowired
    protected UserRepository users;
    @Autowired
    protected PasswordEncoder passwordEncoder;

    /** Registers an INSPECTOR via the public endpoint and returns their JWT. */
    protected String registerInspector(String username, String email, String password) throws Exception {
        var res = mvc.perform(post("/api/auth/register")
                        .contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(
                                Map.of("username", username, "email", email, "password", password))))
                .andExpect(status().isCreated())
                .andReturn();
        return tokenOf(res.getResponse().getContentAsString());
    }

    /** Seeds an ADMIN directly (public registration can't create one) and logs in. */
    protected String createAdmin(String email, String password) throws Exception {
        users.save(User.builder()
                .username(email).email(email)
                .password(passwordEncoder.encode(password))
                .role(Role.ADMIN)
                .build());
        return login(email, password);
    }

    protected String login(String email, String password) throws Exception {
        var res = mvc.perform(post("/api/auth/login")
                        .contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of("email", email, "password", password))))
                .andExpect(status().isOk())
                .andReturn();
        return tokenOf(res.getResponse().getContentAsString());
    }

    protected String bearer(String token) {
        return "Bearer " + token;
    }

    protected JsonNode readJson(String body) throws Exception {
        return json.readTree(body);
    }

    private String tokenOf(String body) throws Exception {
        return json.readTree(body).get("token").asText();
    }
}
