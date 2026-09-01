package com.packsure.backend.exception;

/** Thrown when an upload to the external file store (Cloudinary) fails. Maps to HTTP 502. */
public class FileUploadException extends RuntimeException {
    public FileUploadException(String message, Throwable cause) {
        super(message, cause);
    }
}
