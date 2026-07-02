package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.entities.administration.SmtpEntity;
import com.binewvision.Motulbackend.repositories.administration.SmtpRepository;
import com.binewvision.Motulbackend.services.administration.MailService;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Optional;
import java.util.Properties;

@Service
@RequiredArgsConstructor
public class MailServiceImpl implements MailService {

    private final ApplicationProperties applicationProperties;
    private final SmtpRepository smtpRepository;
    @Override
    public boolean send(Map<String, String> model) {
        Optional<SmtpEntity> optional = smtpRepository.findById(0L);
        try {
            SmtpEntity smtpEntity = optional.get();
            JavaMailSender mailSender = connect(smtpEntity);
            MimeMessage message = mailSender.createMimeMessage();

            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setTo(model.get("receiver"));
            helper.setFrom(smtpEntity.getSender());
            helper.setSubject(model.get("subject"));
            helper.setText(model.get("content"), true);

            mailSender.send(message);
            return true;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }


    private JavaMailSender connect(SmtpEntity smtpEntity) {

        JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
        mailSender.setHost(smtpEntity.getMailServer());
        mailSender.setPort(smtpEntity.getPort().intValue());
        mailSender.setUsername(smtpEntity.getUsername());
        mailSender.setPassword(smtpEntity.getPassword());

        Properties props = mailSender.getJavaMailProperties();
        props.put("mail.smtp.ssl.enable", "true");
        props.put("mail.smtp.auth", String.valueOf(smtpEntity.isAuth()));

        switch (smtpEntity.getEncryptionMethod()) {
            case SSL -> {
                props.put("mail.smtp.ssl.enable", "true");
                props.put("mail.smtp.starttls.enable", "false");
            }
            case TLS -> {
                props.put("mail.smtp.starttls.enable", "true");
                props.put("mail.smtp.ssl.enable", "false");
            }
            default -> {
                props.put("mail.smtp.starttls.enable", "false");
                props.put("mail.smtp.ssl.enable", "false");
            }
        }

        props.put("mail.debug", "true");

        return mailSender;
    }
}
