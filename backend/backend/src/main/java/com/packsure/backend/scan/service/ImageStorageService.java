package com.packsure.backend.scan.service;

import org.springframework.web.multipart.MultipartFile;

/**
 * Stores an uploaded label image and returns a URL to it.
 * Real implementation: Cloudinary. Dev/test implementation: local disk.
 */
public interface ImageStorageService {
    String uploadImage(MultipartFile file);
}
