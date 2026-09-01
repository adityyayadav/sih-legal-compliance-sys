package com.packsure.backend;

import com.packsure.backend.support.AbstractIntegrationTest;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class ScanApiTest extends AbstractIntegrationTest {

    @Test
    void submit_rejects_non_image_with_400() throws Exception {
        String token = registerInspector("sam", "sam@test.com", "secret123");
        var file = new MockMultipartFile("file", "note.txt", "text/plain", "hello".getBytes());

        mvc.perform(multipart("/api/scans").file(file)
                        .param("productId", "11111111-1111-1111-1111-111111111111")
                        .header("Authorization", bearer(token)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value(org.hamcrest.Matchers.containsString("JPEG and PNG")));
    }

    @Test
    void submit_missing_file_returns_400() throws Exception {
        String token = registerInspector("tina", "tina@test.com", "secret123");
        mvc.perform(multipart("/api/scans")
                        .param("productId", "11111111-1111-1111-1111-111111111111")
                        .header("Authorization", bearer(token)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void submit_without_token_returns_401() throws Exception {
        var file = new MockMultipartFile("file", "x.png", "image/png", new byte[]{1, 2, 3});
        mvc.perform(multipart("/api/scans").file(file).param("productId", "x"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void status_of_unknown_scan_returns_404() throws Exception {
        String token = registerInspector("uma", "uma@test.com", "secret123");
        mvc.perform(get("/api/scans/22222222-2222-2222-2222-222222222222/status")
                        .header("Authorization", bearer(token)))
                .andExpect(status().isNotFound());
    }
}
