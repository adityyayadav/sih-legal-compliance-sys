package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlAnalyzeResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;

/**
 * Real ML service client — {@code multipart/form-data POST} to
 * {@code ${ml.service.base-url}/analyze} with an {@code images} file part and a
 * {@code product_id} form field. Disabled under dev/test (see {@link MockMlAnalysisClient}).
 */
@Slf4j
@Service
@Profile("!dev & !test")
public class MlServiceClient implements MlAnalysisClient {

    private static final Duration TIMEOUT = Duration.ofSeconds(30);

    private final WebClient webClient;

    public MlServiceClient(@Value("${ml.service.base-url}") String mlBaseUrl) {
        this.webClient = WebClient.builder()
                .baseUrl(mlBaseUrl)
                .codecs(c -> c.defaultCodecs().maxInMemorySize(8 * 1024 * 1024))
                .build();
    }

    @Override
    public MlAnalyzeResponse analyze(byte[] imageBytes, String filename, String contentType, String scanId) {
        MultipartBodyBuilder body = new MultipartBodyBuilder();
        body.part("images", new ByteArrayResource(imageBytes) {
            @Override
            public String getFilename() {
                return (filename == null || filename.isBlank()) ? "label.jpg" : filename;
            }
        }).contentType(contentType != null ? MediaType.parseMediaType(contentType) : MediaType.IMAGE_JPEG);
        body.part("product_id", scanId);

        long start = System.currentTimeMillis();
        try {
            MlAnalyzeResponse res = webClient.post()
                    .uri("/analyze")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(body.build()))
                    .retrieve()
                    .bodyToMono(MlAnalyzeResponse.class)
                    .block(TIMEOUT);
            log.info("ML /analyze returned in {} ms", System.currentTimeMillis() - start);
            return res;
        } catch (Exception e) {
            throw new RuntimeException("ML service call failed: " + e.getMessage(), e);
        }
    }
}
