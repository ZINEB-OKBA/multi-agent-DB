package com.binewvision.Motulbackend.security.config;

import com.binewvision.Motulbackend.security.jwt.JwtService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;


@Component
@RequiredArgsConstructor
public class AuthenticationFacade {

    private final JwtService jwtService;

    private String getToken(){
        HttpServletRequest request = ((ServletRequestAttributes) RequestContextHolder.currentRequestAttributes()).getRequest();
        String header = request.getHeader("Authorization");

        if(header != null && header.startsWith("Bearer")){
            return header.substring(7);
        }else if(header != null && header.startsWith("Basic")){

            return header.substring(6);
        }
        else {
            return null;
        }
    }

    public String getCurrentUser() {
        String token = getToken();
        return jwtService.extractUsername(token);
    }

    public String getCurrentStore() {
        String token = getToken();
        return jwtService.extractClaim(token, "key");
    }

    public boolean hasRole(String profile) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        return authentication.getAuthorities().stream()
                .anyMatch(r -> r.getAuthority().equals(profile));
    }

}
