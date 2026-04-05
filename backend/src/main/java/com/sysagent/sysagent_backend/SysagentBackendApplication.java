package com.sysagent.sysagent_backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SysagentBackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(SysagentBackendApplication.class, args);
	}

}
