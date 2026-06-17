package com.sysagent.sysagent_backend.config;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;
import org.springframework.util.StreamUtils;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class DatabaseSchemaMigration implements ApplicationRunner {

    private final JdbcTemplate jdbcTemplate;

    @Override
    public void run(ApplicationArguments args) {
        executeStatement("ALTER TABLE IF EXISTS tasks ALTER COLUMN intent TYPE TEXT");
        executeSqlResource("db/migration/phase6_agent_hub_foundation.sql");
    }

    private void executeStatement(String sql) {
        try {
            jdbcTemplate.execute(sql);
        } catch (Exception e) {
            log.warn("Database migration statement failed: {}", e.getMessage());
        }
    }

    private void executeSqlResource(String classpathLocation) {
        try {
            ClassPathResource resource = new ClassPathResource(classpathLocation);
            String sql = StreamUtils.copyToString(resource.getInputStream(), StandardCharsets.UTF_8);
            Arrays.stream(sql.split(";\\s*(?:\\r?\\n|$)"))
                    .map(String::trim)
                    .filter(statement -> !statement.isBlank())
                    .forEach(this::executeStatement);
            log.info("Applied database migration resource: {}", classpathLocation);
        } catch (Exception e) {
            log.warn("Could not apply database migration resource {}: {}", classpathLocation, e.getMessage());
        }
    }
}
