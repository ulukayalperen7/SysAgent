package com.sysagent.sysagent_backend.config;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

/**
 * Reserved for real bootstrap data only.
 *
 * Device records are no longer seeded with demo machines; remote device
 * registration will be introduced with Auth and pairing flows.
 */
@Component
public class DataSeeder implements CommandLineRunner {

    @Override
    public void run(String... args) {
        // Intentionally empty.
    }
}
