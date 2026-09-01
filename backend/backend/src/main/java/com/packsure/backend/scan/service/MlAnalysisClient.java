package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlScanResponse;

/**
 * Calls the ML service to analyse a label image.
 * Real implementation: HTTP to the FastAPI service. Dev/test: a deterministic mock.
 */
public interface MlAnalysisClient {
    MlScanResponse analyzeImageViaMl(String imageUrl);
}
