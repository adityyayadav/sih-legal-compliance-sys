package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlAnalyzeResponse;

/**
 * Calls the ML service ({@code POST /api/v1/analyze}) to analyse a label image.
 * Real implementation: multipart HTTP to the FastAPI service.
 * Dev/test: a deterministic mock.
 */
public interface MlAnalysisClient {

    /**
     * @param imageBytes  raw image content
     * @param filename    original filename (for the multipart part)
     * @param contentType image MIME type
     * @param scanId      our scan id — echoed back by the ML service as {@code product_id}
     */
    MlAnalyzeResponse analyze(byte[] imageBytes, String filename, String contentType, String scanId);
}
