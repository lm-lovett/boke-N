package com.boke.blog.security;

import java.util.List;

public record AuthPrincipal(Long userId, String username, List<Long> roleIds, boolean admin) {
}
