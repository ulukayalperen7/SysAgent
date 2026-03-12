package com.sysagent.sysagent_backend.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceDto {
    private Long id;
    private String name;
    private String status;
    private Integer cpu;
    private Integer ram;
    private String type;
}
