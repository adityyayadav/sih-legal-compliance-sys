package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlAnalyzeResponse;
import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

/**
 * Real ML service client — {@code multipart/form-data POST} to
 * {@code ${ml.service.base-url}/analyze} with an {@code images} file part and a
 * {@code product_id} form field. Active unless {@code app.ml.mock=true}
 * (see {@link MockMlAnalysisClient}).
 */
@Slf4j
@Service
@ConditionalOnProperty(prefix = "app.ml", name = "mock", havingValue = "false", matchIfMissing = true)
public class MlServiceClient implements MlAnalysisClient {

    private static final int CONNECT_TIMEOUT_MS = 3_000;
    private static final Duration RESPONSE_TIMEOUT = Duration.ofSeconds(90);
    private static final Duration HARD_TIMEOUT = Duration.ofSeconds(100);

    private final WebClient webClient;

    public MlServiceClient(@Value("${ml.service.base-url}") String mlBaseUrl) {
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, CONNECT_TIMEOUT_MS)
                .responseTimeout(RESPONSE_TIMEOUT)
                .doOnConnected(conn -> conn.addHandlerLast(
                        new ReadTimeoutHandler(RESPONSE_TIMEOUT.toSeconds(), TimeUnit.SECONDS)));

        this.webClient = WebClient.builder()
                .baseUrl(mlBaseUrl)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .codecs(c -> c.defaultCodecs().maxInMemorySize(16 * 1024 * 1024))
                .build();
        log.info("MlServiceClient -> {} (connect {}ms, response {}s)",
                mlBaseUrl, CONNECT_TIMEOUT_MS, RESPONSE_TIMEOUT.toSeconds());
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
                    .block(HARD_TIMEOUT);
            log.info("ML /analyze OK in {} ms", System.currentTimeMillis() - start);
            return res;
        } catch (Exception e) {
            throw new RuntimeException("ML service call failed after "
                    + (System.currentTimeMillis() - start) + " ms: " + e.getMessage(), e);
        }
    }
}
