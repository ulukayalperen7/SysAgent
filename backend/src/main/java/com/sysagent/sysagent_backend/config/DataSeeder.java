package com.sysagent.sysagent_backend.config;

import java.time.LocalDateTime;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import com.sysagent.sysagent_backend.model.entity.DeviceEntity;
import com.sysagent.sysagent_backend.model.enums.DeviceType;
import com.sysagent.sysagent_backend.repository.DeviceRepository;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    private final DeviceRepository deviceRepository;

    @Override
    public void run(String... args) throws Exception {
        if (deviceRepository.count() == 0) {
            DeviceEntity windowsPc = DeviceEntity.builder()
                    .name("Main Game Rig")
                    .ipAddress("192.168.1.105")
                    .status("online")
                    .type(DeviceType.WINDOWS)
                    .lastSeen(LocalDateTime.now())
                    .build();

            DeviceEntity macbook = DeviceEntity.builder()
                    .name("Work MacBook Pro")
                    .ipAddress("192.168.1.106")
                    .status("offline")
                    .type(DeviceType.MACOS)
                    .lastSeen(LocalDateTime.now().minusHours(2))
                    .build();

            DeviceEntity linuxServer = DeviceEntity.builder()
                    .name("Ubuntu Home Server")
                    .ipAddress("192.168.1.200")
                    .status("online")
                    .type(DeviceType.LINUX)
                    .lastSeen(LocalDateTime.now().minusMinutes(5))
                    .build();

            deviceRepository.save(windowsPc);
            deviceRepository.save(macbook);
            deviceRepository.save(linuxServer);
            
            System.out.println("--- MOCK DATA SEEDED: 3 Devices created ---");
        }
    }
}
