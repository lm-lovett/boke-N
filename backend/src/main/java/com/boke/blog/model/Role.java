package com.boke.blog.model;

import java.util.ArrayList;
import java.util.List;

public class Role {
  private Long id;
  private String name;
  private String description;
  private List<Long> resourceIds = new ArrayList<>();

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public List<Long> getResourceIds() {
    return resourceIds;
  }

  public void setResourceIds(List<Long> resourceIds) {
    this.resourceIds = resourceIds;
  }
}
