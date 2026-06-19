package com.sysagent.sysagent_backend.model.dto;

import lombok.Data;

@Data
public class AuthRegisterRequestDto {

    private String email;
    private String password;
    private String displayName;
}
