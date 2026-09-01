package com.packsure.backend;

import com.packsure.backend.support.AbstractIntegrationTest;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class ProductApiTest extends AbstractIntegrationTest {

    @Test
    void create_list_get() throws Exception {
        String token = registerInspector("pia", "pia@test.com", "secret123");

        var created = mvc.perform(post("/api/products").header("Authorization", bearer(token))
                        .contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of(
                                "name", "Sunflower Oil 1L", "category", "EDIBLE_OIL", "brand", "SunGold"))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.createdBy").value("pia"))
                .andExpect(jsonPath("$.createdAt").exists())
                .andReturn();
        String id = readJson(created.getResponse().getContentAsString()).get("id").asText();

        mvc.perform(get("/api/products").header("Authorization", bearer(token)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(id));

        mvc.perform(get("/api/products/" + id).header("Authorization", bearer(token)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Sunflower Oil 1L"));
    }

    @Test
    void get_unknown_product_returns_404() throws Exception {
        String token = registerInspector("quinn", "quinn@test.com", "secret123");
        mvc.perform(get("/api/products/11111111-1111-1111-1111-111111111111")
                        .header("Authorization", bearer(token)))
                .andExpect(status().isNotFound());
    }

    @Test
    void create_without_token_returns_401() throws Exception {
        mvc.perform(post("/api/products").contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of("name", "X", "category", "Y"))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void create_missing_name_returns_400() throws Exception {
        String token = registerInspector("rob", "rob@test.com", "secret123");
        mvc.perform(post("/api/products").header("Authorization", bearer(token))
                        .contentType(APPLICATION_JSON)
                        .content(json.writeValueAsString(Map.of("category", "Y"))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.fieldErrors.name").exists());
    }
}
