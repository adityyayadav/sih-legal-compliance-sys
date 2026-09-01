package com.packsure.backend.exception;

/** Thrown when creating an entity that conflicts with an existing one. Maps to HTTP 409. */
public class DuplicateResourceException extends RuntimeException {
    public DuplicateResourceException(String message) {
        super(message);
    }
}
