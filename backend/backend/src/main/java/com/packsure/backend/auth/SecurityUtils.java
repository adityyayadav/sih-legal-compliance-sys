package com.packsure.backend.auth;

import com.packsure.backend.common.Role;
import org.springframework.security.core.userdetails.UserDetails;

public final class SecurityUtils {

    private SecurityUtils() {
    }

    public static boolean hasRole(UserDetails user, Role role) {
        String authority = "ROLE_" + role.name();
        return user.getAuthorities().stream()
                .anyMatch(a -> authority.equals(a.getAuthority()));
    }

    public static boolean isAdmin(UserDetails user) {
        return hasRole(user, Role.ADMIN);
    }
}
