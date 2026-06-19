package com.sysagent.sysagent_backend.model.dto;

import com.sysagent.sysagent_backend.model.entity.AppUserEntity;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AuthUserDto {

    private String id;
    private String email;
    private String displayName;

    public static AuthUserDto fromEntity(AppUserEntity user) {
        return AuthUserDto.builder()
                .id(user.getId())
                .email(user.getEmail())
                .displayName(user.getDisplayName())
                .build();
    }
}
