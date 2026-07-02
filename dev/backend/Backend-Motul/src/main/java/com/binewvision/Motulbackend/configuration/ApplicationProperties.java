package com.binewvision.Motulbackend.configuration;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.xml.crypto.dsig.spec.XSLTTransformParameterSpec;

@Data
@Configuration
public class ApplicationProperties {

    private SecurityConfig security;
    private FailedAttempts failedAttempts;
    private AuthenticationAttemptsConfig attempts;

    @Bean
    @ConfigurationProperties(prefix = "auth.security.jwt")
    public SecurityConfig getSecurityConfig() {
        return new SecurityConfig();
    }

    @Data
    public static class SecurityConfig {
        private String secret;
        private long jwtExpiration;
        private long refreshExpiration;
    }

    @Bean
    @ConfigurationProperties(prefix = "commons.config")
    public CommonsConfig getCommonsConfig() {
        return new CommonsConfig();
    }

    @Data
    public static class CommonsConfig {
        private String reportPath;
        private String timeZone;
    }

    @Bean
    @ConfigurationProperties(prefix = "file.upload")
    public UploadConfig getUploadConfig() {
        return new UploadConfig();
    }

    @Data
    public static class UploadConfig {
        private long maxSize;
        private long maxSizeLogo;
        private long maxSizeImage;
        private long maxSizeProfileImage;
        private String[] allowedExtensions;
        public long getMaxUpload() {
            return maxSize;
        }
    }

    @Bean
    @ConfigurationProperties(prefix = "auth.attempts")
    public AuthenticationAttemptsConfig getAuthenticationAttemptsConfig() {
        return new AuthenticationAttemptsConfig();
    }

    @Bean
    @ConfigurationProperties(prefix = "auth.failed.attempts")
    public FailedAttempts getMaxFailedAttempts(){
        return new FailedAttempts();
    } ;
    @Data
    public static class FailedAttempts {
        private int login;
        private  int forgotPwd ;
    }

    @Data
    public static class AuthenticationAttemptsConfig {
        private int login;
        private int forgotPassword;
    }


    @Bean
    @ConfigurationProperties(prefix = "external.ai")
    public AiConfig getExternalAiConfig() {
        return new AiConfig();
    }

    @Data
    public static class AiConfig {
        private String url;       // pointera vers /api/chat
        private String projects;  // pointera vers /api/projects
        private String documents;
        private String dex;
    }


    @Bean
    @ConfigurationProperties(prefix = "smtp")
    public SmtpConfig getSmtpConfig() {
        return new SmtpConfig();
    }

    @Data
    public static class SmtpConfig {
        private boolean auth;
        private String encryptionMethod;
        private String server;
        private int port;
        private String sender;
        private String username;
        private String password;
    }



    @Bean
    @ConfigurationProperties(prefix = "application.web")
    public WebUrl getWebUrl() {
        return new WebUrl();
    }

    @Data
    public static class WebUrl {
        private String url;
    }


    @Bean
    @ConfigurationProperties(prefix = "mail.templates")
    public MailTemplatesConfig getMailTemplatesConfig() {
        return new MailTemplatesConfig();
    }

    @Data
    public static class MailTemplatesConfig {
        private String mailTemplatePath;
        private String RegisterMailContent;
        private String ForgetPasswordMailContent;
    }

}
