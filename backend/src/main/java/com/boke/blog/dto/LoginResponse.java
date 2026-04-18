package com.boke.blog.dto;

import com.boke.blog.model.Resource;
import com.boke.blog.model.Role;
import java.util.List;
import java.util.Map;

public record LoginResponse(String token, Map<String, Object> user, List<Role> roles, List<Resource> resources) {
}
