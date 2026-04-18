package com.boke.blog.dto;

import java.util.List;

public record UserRequest(String username, String nickname, String password, List<Long> roleIds) {
}
