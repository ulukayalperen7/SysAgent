package com.sysagent.sysagent_backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.sysagent.sysagent_backend.model.dto.DeviceRegistrationTokenResponseDto;
import com.sysagent.sysagent_backend.model.entity.DeviceRegistrationTokenEntity;
import com.sysagent.sysagent_backend.repository.DeviceRegistrationTokenRepository;
import com.sysagent.sysagent_backend.repository.DeviceRepository;
import com.sysagent.sysagent_backend.security.TokenHashingService;

@ExtendWith(MockitoExtension.class)
class DeviceServiceTest {

    @Mock
    private DeviceRepository deviceRepository;

    @Mock
    private DeviceRegistrationTokenRepository registrationTokenRepository;

    private final TokenHashingService tokenHashingService = new TokenHashingService();

    @Test
    void registrationTokenUsesConfiguredPublicBackendUrlInBootstrapCommand() {
        when(registrationTokenRepository.save(any(DeviceRegistrationTokenEntity.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));
        DeviceService service = new DeviceService(deviceRepository, registrationTokenRepository, tokenHashingService);
        ReflectionTestUtils.setField(service, "publicBackendUrl", "https://sysagent.example.com/");

        DeviceRegistrationTokenResponseDto response = service.createRegistrationToken("user-1", "Laptop");

        assertThat(response.getBootstrapCommand())
                .startsWith("sysagent-node register --server https://sysagent.example.com --token ");
    }
}
