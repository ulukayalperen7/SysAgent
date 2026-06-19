package com.sysagent.sysagent_backend.model.dto;

import lombok.Data;

@Data
public class AuthLoginRequestDto {

    private String email;
    private String password;
}
