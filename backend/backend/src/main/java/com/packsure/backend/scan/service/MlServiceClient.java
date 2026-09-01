package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlScanRequest;
import com.packsure.backend.scan.dto.MlScanResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

/** Real ML service client. Disabled under dev/test (see {@link MockMlAnalysisClient}). */
@Service
@Profile("!dev & !test")
@RequiredArgsConstructor
public class MlServiceClient implements MlAnalysisClient {

    @Value("${ml.service.base-url}")
    private String mlBaseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public MlScanResponse analyzeImageViaMl(String imageUrl) {
        MlScanRequest request = new MlScanRequest(imageUrl);
        String url = mlBaseUrl + "/analyze";

        try {
            return restTemplate.postForObject(url, request, MlScanResponse.class);
        } catch (Exception e) {
            throw new RuntimeException("Failed to communicate with ML Service: " + e.getMessage(), e);
        }
    }
}
