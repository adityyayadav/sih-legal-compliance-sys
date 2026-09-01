package com.packsure.backend.scan.service;

import com.cloudinary.Cloudinary;
import com.cloudinary.utils.ObjectUtils;
import com.packsure.backend.exception.FileUploadException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

/** Production image store. Disabled under the dev/test profiles (see {@link LocalImageStorageService}). */
@Slf4j
@Service
@Profile("!dev & !test")
@RequiredArgsConstructor
public class CloudinaryService implements ImageStorageService {

    private final Cloudinary cloudinary;

    /** Uploads the file to Cloudinary and returns its (https) URL. */
    @Override
    public String uploadImage(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("Uploaded file is empty");
        }
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> result = cloudinary.uploader().upload(
                    file.getBytes(),
                    ObjectUtils.asMap("folder", "packsure/scans"));
            Object url = result.get("secure_url");
            if (url == null) {
                url = result.get("url");
            }
            if (url == null) {
                throw new FileUploadException("Cloudinary returned no URL", null);
            }
            return url.toString();
        } catch (FileUploadException e) {
            throw e;
        } catch (Exception e) {
            log.error("Cloudinary upload failed", e);
            throw new FileUploadException("Failed to upload image to Cloudinary", e);
        }
    }
}
