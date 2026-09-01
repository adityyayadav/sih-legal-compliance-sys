package com.packsure.backend.product.service;

import com.packsure.backend.product.Product;
import com.packsure.backend.product.ProductRepository;
import com.packsure.backend.product.dto.ProductRequest;
import com.packsure.backend.product.dto.ProductResponse;
import com.packsure.backend.exception.ResourceNotFoundException;
import com.packsure.backend.user.User;
import com.packsure.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;
    private final UserRepository userRepository;

    @Transactional
    public ProductResponse createProduct(ProductRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        Product product = Product.builder()
                .name(request.getName())
                .category(request.getCategory())
                .brand(request.getBrand())
                .createdBy(user)
                .build();

        Product saved = productRepository.save(product);
        return mapToResponse(saved);
    }

    @Transactional(readOnly = true)
    public List<ProductResponse> getAllProducts() {
        return productRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public ProductResponse getProductById(UUID id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found"));
        return mapToResponse(product);
    }

    private ProductResponse mapToResponse(Product product) {
        return ProductResponse.builder()
                .id(product.getId())
                .name(product.getName())
                .category(product.getCategory())
                .brand(product.getBrand())
                .createdBy(product.getCreatedBy().getUsername())
                .createdAt(product.getCreatedAt())
                .build();
    }
}
