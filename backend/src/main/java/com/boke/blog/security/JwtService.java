package com.boke.blog.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

  private final Key key;
  private final long expireSeconds;

  public JwtService(@Value("${app.jwt.secret}") String secret,
      @Value("${app.jwt.expire-seconds}") long expireSeconds) {
    if (secret.length() >= 32) {
      this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    } else {
      byte[] padded = (secret + "00000000000000000000000000000000").substring(0, 32)
          .getBytes(StandardCharsets.UTF_8);
      this.key = Keys.hmacShaKeyFor(padded);
    }
    this.expireSeconds = expireSeconds;
  }

  public String issueToken(Long userId, String username, List<Long> roleIds, boolean isAdmin) {
    Instant now = Instant.now();
    return Jwts.builder()
        .subject(username)
        .claim("userId", userId)
        .claim("roleIds", roleIds)
        .claim("isAdmin", isAdmin)
        .issuedAt(Date.from(now))
        .expiration(Date.from(now.plusSeconds(expireSeconds)))
        .signWith(key)
        .compact();
  }

  @SuppressWarnings("unchecked")
  public AuthPrincipal parseToken(String token) {
    Claims claims = Jwts.parser().verifyWith((javax.crypto.SecretKey) key).build()
        .parseSignedClaims(token).getPayload();
    Object roleObject = claims.get("roleIds");
    List<Long> roleIds = new ArrayList<>();
    if (roleObject instanceof List<?> values) {
      for (Object value : values) {
        if (value instanceof Number number) {
          roleIds.add(number.longValue());
        }
      }
    }
    Number userIdNumber = claims.get("userId", Number.class);
    if (userIdNumber == null) {
      throw new IllegalArgumentException("token userId invalid");
    }
    return new AuthPrincipal(
        userIdNumber.longValue(),
        claims.getSubject(),
        roleIds,
        Boolean.TRUE.equals(claims.get("isAdmin", Boolean.class))
    );
  }
}
