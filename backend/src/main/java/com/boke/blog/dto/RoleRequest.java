package com.boke.blog.dto;

import java.util.List;

public record RoleRequest(String name, String description, List<Long> resourceIds) {
}
