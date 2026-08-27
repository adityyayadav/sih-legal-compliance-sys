package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlScanRequest;
import com.packsure.backend.scan.dto.MlScanResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
@RequiredArgsConstructor
public class MlServiceClient {

    @Value("${ml.service.base-url}")
    private String mlBaseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public MlScanResponse analyzeImageViaMl(String imageUrl) {
        MlScanRequest request = new MlScanRequest(imageUrl);
        String url = mlBaseUrl + "/analyze";
        
        try {
            // Send the POST request to the Python ML server
            return restTemplate.postForObject(url, request, MlScanResponse.class);
        } catch (Exception e) {
            // For now, if the ML server is off/fails, throw an exception
            throw new RuntimeException("Failed to communicate with ML Service: " + e.getMessage(), e);
        }
    }
}
