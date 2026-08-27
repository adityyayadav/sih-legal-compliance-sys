package com.packsure.backend.product.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
public class ProductResponse {
    private UUID id;
    private String name;
    private String category;
    private String brand;
    private String createdBy; // Inspector/User's username
    private LocalDateTime createdAt;
}
