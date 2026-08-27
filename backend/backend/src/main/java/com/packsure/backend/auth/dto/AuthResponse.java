package com.packsure.backend.auth.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AuthResponse {
    private String token;
    private String refreshToken;
    private String username;
    private String email;
    private String role;
}
