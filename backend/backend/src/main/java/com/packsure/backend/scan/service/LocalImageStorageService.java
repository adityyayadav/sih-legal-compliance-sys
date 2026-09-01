package com.packsure.backend.scan.service;

import com.packsure.backend.exception.FileUploadException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

/**
 * Dev/test image store — writes the upload to a local folder and returns a URL
 * served by {@code LocalUploadsWebConfig} at {@code /uploads/**}. No external
 * service needed, so the scan flow works offline.
 */
@Slf4j
@Service
@Profile("dev | test")
public class LocalImageStorageService implements ImageStorageService {

    private final Path dir;
    private final String baseUrl;

    public LocalImageStorageService(
            @Value("${app.uploads.dir:uploads}") String uploadsDir,
            @Value("${server.port:8080}") int serverPort) {
        this.dir = Paths.get(uploadsDir).toAbsolutePath();
        this.baseUrl = "http://localhost:" + serverPort + "/uploads/";
    }

    @Override
    public String uploadImage(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("Uploaded file is empty");
        }
        try {
            Files.createDirectories(dir);
            String ext = extensionOf(file.getContentType());
            String name = UUID.randomUUID() + ext;
            Files.write(dir.resolve(name), file.getBytes());
            log.info("[dev] stored upload locally: {}", dir.resolve(name));
            return baseUrl + name;
        } catch (IOException e) {
            throw new FileUploadException("Failed to store image locally", e);
        }
    }

    private String extensionOf(String contentType) {
        if ("image/png".equalsIgnoreCase(contentType)) return ".png";
        return ".jpg";
    }
}
