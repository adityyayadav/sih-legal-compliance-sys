package com.packsure.backend.product.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ProductRequest {
    @NotBlank(message = "Product name is required")
    private String name;

    @NotBlank(message = "Product category is required")
    private String category;

    private String brand;
}
