package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.dtos.administration.UserDto;
import com.binewvision.Motulbackend.dtos.administration.authentication.AuthenticationResponseDto;
import com.binewvision.Motulbackend.entities.administration.ProfileEntity;
import com.binewvision.Motulbackend.entities.administration.UserEntity;
import com.binewvision.Motulbackend.enums.ExceptionsEnum;
import com.binewvision.Motulbackend.exceptions.BusinessException;
import com.binewvision.Motulbackend.repositories.administration.UserRepository;
import com.binewvision.Motulbackend.security.jwt.JwtService;
import com.binewvision.Motulbackend.services.administration.AttemptAuthenticationService;
import com.binewvision.Motulbackend.services.administration.AuthService;
import com.binewvision.Motulbackend.services.administration.MailService;
import com.binewvision.Motulbackend.services.administration.MailTemplateService;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import com.binewvision.Motulbackend.utils.OtpGenerator;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserRepository repository;
    private final PasswordEncoder passwordEncoder;
    private final MailTemplateService mailTemplateService;
    private final JwtService jwtService;
    private final MailService mailService;
    private final ApplicationProperties applicationProperties;
    private final OtpGenerator otpGenerator;


    private final AuthenticationManager authenticationManager;
    private final AttemptAuthenticationService attemptAuthenticationService;

    @Override
    public AuthenticationResponseDto authenticate(String email, String password) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(email,password)
        );
        UserEntity user = repository.findByEmailAndDeletedFalse(email).orElseThrow();
        UserDto userDto = ObjectMapper.map(user, UserDto.class);
        String jwtToken = jwtService.generateToken(userDto, user.getProfile());
        String refreshToken = jwtService.generateRefreshToken(userDto, user.getProfile());
        return AuthenticationResponseDto.builder()
                .refreshToken(refreshToken)
                .accessToken(jwtToken)
                .authenticate(true)
                .id(userDto.getId())
                .name(userDto.getFirstName() + " " + userDto.getLastName())
                .email(userDto.getEmail())
                .authority(userDto.getProfile().getName())
                .image(userDto.getImage())
                .maxUpload(applicationProperties.getUploadConfig().getMaxSizeProfileImage())
                .build();
    }


    private Optional<UserDto> getByEmail(String email) {
        Optional<UserEntity> user = repository.findByEmailAndDeletedFalse(email);

        return user.map(userEntity -> ObjectMapper.map(userEntity, UserDto.class));
    }

    @Override
    public AuthenticationResponseDto refreshToken(String refreshToken) {

        if ((refreshToken != null) && (!refreshToken.isEmpty())){

            String email = jwtService.extractUsername(refreshToken);
            Optional<UserDto> optional = getByEmail(email);

            if(optional.isPresent()){
                UserDto user = optional.get();
                ProfileEntity profile = ObjectMapper.map(user.getProfile(), ProfileEntity.class);

                String generatedRefreshToken = jwtService.generateRefreshToken(user, profile);
                String jwtToken = jwtService.generateToken(user, profile);
                return AuthenticationResponseDto.builder()
                        .refreshToken(generatedRefreshToken)
                        .accessToken(jwtToken)
                        .authenticate(true)
                        .build();
            }


        }
        return null;
    }
    @Override
    public boolean setNewPassword(UserDto dto) {

        byte[] decodedBytes = Base64.getUrlDecoder().decode(dto.getSecret());
        String secret = new String(decodedBytes);
        String[] secretParts = secret.split(":", 2);

        boolean isValid = this.otpGenerator.validateOTP(secretParts[0], secretParts[1]);
        if (isValid){
            Optional<UserEntity> optional = repository.findByEmailAndDeletedFalse(secretParts[0]);
            if (optional.isPresent()){
                UserEntity user = optional.get();
                if (Objects.equals(dto.getNewPassword(), dto.getPassword())){
                    user.setPassword(passwordEncoder.encode(dto.getPassword()));
                    user.setEnabled(true);
                    user.setLocked(false);
                    this.repository.save(user);
                }
            }
            return true;
        }
        return false;
    }

    @Override
    @Transactional
    public boolean forgotPassword(String email) {

        Optional<UserEntity> optional = repository.findByEmailAndDeletedFalse(email);
        if(optional.isPresent()){
            UserEntity user = optional.get();
            if (!attemptAuthenticationService.reachedMaxForgotPasswordAttempt(user)){
                HttpServletRequest request = ((ServletRequestAttributes) RequestContextHolder.currentRequestAttributes()).getRequest();
                attemptAuthenticationService.forgotPasswordSave(request, user);

                String newPassword = otpGenerator.generateOTP(16);
                user.setPassword(passwordEncoder.encode(newPassword));
                if (user.isLocked()){
                    user.setLocked(false);
                }

                repository.save(user);

                sendForgotPasswordMail(user);
            }else {
                return false;
            }
        }
        return true;
    }

    @Transactional
    protected void sendForgotPasswordMail(UserEntity user){

        Map<String, String> model = new HashMap<>();

        String otp =  user.getEmail() + ":" + this.otpGenerator.generateOTP(user.getEmail(), 16);
        String secret = Base64.getUrlEncoder().encodeToString(otp.getBytes());
        String url = this.applicationProperties.getWebUrl().getUrl() + "/" + secret;

        // Charger le contenu HTML
        String content = loadHtmlTemplate()
                .replace("[content]", applicationProperties.getMailTemplatesConfig().getForgetPasswordMailContent())
                .replace("[first_name]", user.getFirstName())
                .replace("[last_name]", user.getLastName())
                .replace("[email]", user.getEmail())
                .replace("[Link_create_account]", url);

        // prepare model
        model.put("content", content);
        model.put("receiver", user.getEmail());
        model.put("subject", "Réinitialisation de votre mot de passe");

        // send mail
        mailService.send(model);
    }

    private String loadHtmlTemplate() {
        try {
            String filePath = applicationProperties.getMailTemplatesConfig().getMailTemplatePath() + "mail_template.html";

            byte[] fileBytes = Files.readAllBytes(Path.of(filePath));
            return new String(fileBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException("ERROR_LOADING_TEMPLATE_HTML", e);
        }
    }

    @Override
    public boolean updatePassword(UserDto dto) {
        if (dto.getPassword() == null || dto.getNewPassword() == null) {
            return false;
        }
        Optional<UserEntity> optional = repository.findByIdAndDeletedFalse(dto.getId());
        if (optional.isPresent()) {
            UserEntity user = optional.get();
            if (passwordEncoder.matches(dto.getPassword(), user.getPassword())){
                if (passwordEncoder.matches(dto.getNewPassword(), user.getPassword())) {
                    throw new BusinessException(ExceptionsEnum.NEW_PASSWORD_MATCHES_OLD.name(), HttpStatus.CONFLICT);
                }
                user.setPassword(passwordEncoder.encode(dto.getNewPassword()));
                repository.save(user);
                return true;
            }
            throw new BusinessException(ExceptionsEnum.INCORRECT_OLD_PASSWORD.name(), HttpStatus.CONFLICT);
        }
        return false;
    }


}
