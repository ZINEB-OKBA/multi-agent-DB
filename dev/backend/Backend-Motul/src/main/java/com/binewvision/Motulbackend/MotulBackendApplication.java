package com.binewvision.Motulbackend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class MotulBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(MotulBackendApplication.class, args);
    }

}