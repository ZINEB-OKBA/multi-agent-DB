package com.binewvision.Motulbackend.security.jwt;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.entities.administration.ProfileEntity;
import com.binewvision.Motulbackend.entities.administration.RoleEntity;
import com.binewvision.Motulbackend.exceptions.BusinessException;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.security.Key;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class JwtService {

    private final ApplicationProperties properties;
    public String extractUsername(String token) {
        return token != null ? extractClaim(token, Claims::getSubject): null;
    }

    public String extractClaim(String token, String claim) {
        final Claims claims = extractAllClaims(token);

        return String.valueOf(claims.get(claim));
    }

    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    public String generateToken(UserDetails userDetails, ProfileEntity profile) {
        return generateToken(new HashMap<>(), userDetails, profile);
    }

    public String generateToken(
            Map<String, Object> extraClaims,
            UserDetails userDetails, ProfileEntity profile
    ) {
        return buildToken(extraClaims, userDetails, profile, properties.getSecurityConfig().getJwtExpiration());
    }

    public String generateRefreshToken(
            UserDetails userDetails, ProfileEntity profile
    ) {
        return buildToken(new HashMap<>(), userDetails, profile, properties.getSecurityConfig().getRefreshExpiration());
    }

    private String buildToken(
            Map<String, Object> extraClaims,
            UserDetails userDetails, ProfileEntity profile,
            long expiration
    ) {
        return Jwts
                .builder()
                .setClaims(extraClaims)
                .setSubject(userDetails.getUsername())
                .claim("authorities", profile.getRoles().stream()
                        .map(RoleEntity::getIdentifiant)
                        .collect(Collectors.toList()))
                .setIssuedAt(new Date(System.currentTimeMillis()))
                .setExpiration(new Date(System.currentTimeMillis() + expiration))
                .signWith(getSignInKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    public String generateStoreSecret(String user, String secret, String store) {
        Calendar c = Calendar.getInstance();
        c.setTime(new Date());
        c.add(Calendar.YEAR, 10);
        Date expirtationDate = c.getTime();

        return Jwts
                .builder()
                .setSubject(user)
                .claim("key", secret)
                .claim("store", store)
                .setIssuedAt(new Date(System.currentTimeMillis()))
                .setExpiration(expirtationDate)
                .signWith(getSignInKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        final String username = extractUsername(token);
        return (username.equals(userDetails.getUsername())) && !isTokenExpired(token);
    }

    private boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    private Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    private Claims extractAllClaims(String token) {
        Claims claims = null;
        try {
            claims = Jwts
                    .parserBuilder()
                    .setSigningKey(getSignInKey())
                    .build()
                    .parseClaimsJws(token)
                    .getBody();
        }catch (ExpiredJwtException e){
            System.err.println(token);
            throw new BusinessException("EXPIRED TOKEN", HttpStatus.UNAUTHORIZED);
        }
        return claims;
    }

    private Key getSignInKey() {
        byte[] keyBytes = Decoders.BASE64.decode(properties.getSecurityConfig().getSecret());
        return Keys.hmacShaKeyFor(keyBytes);
    }
}
