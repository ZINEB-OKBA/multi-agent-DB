package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.dtos.administration.UserDto;
import com.binewvision.Motulbackend.entities.administration.ListeEntity;
import com.binewvision.Motulbackend.entities.administration.ProfileEntity;
import com.binewvision.Motulbackend.entities.administration.UserEntity;
import com.binewvision.Motulbackend.exceptions.BusinessException;
import com.binewvision.Motulbackend.repositories.administration.UserRepository;
import com.binewvision.Motulbackend.services.administration.MailService;
import com.binewvision.Motulbackend.services.administration.MailTemplateService;
import com.binewvision.Motulbackend.services.administration.UserService;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import com.binewvision.Motulbackend.utils.OtpGenerator;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.criteria.Predicate;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {
    @PersistenceContext
    private final EntityManager entityManager;
    private final MailService mailService;
    private final OtpGenerator otpGenerator;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final MailTemplateService mailTemplateService;
    private final ApplicationProperties applicationProperties;


    @Override
    public Page<UserDto> findAll(UserDto filter) {
        
        int pageSize = filter.getPage().getSize() > 0 ? filter.getPage().getSize() : Integer.MAX_VALUE;

        Page<UserEntity> result = userRepository.findAll(getSpecification(filter), PageRequest.of(filter.getPage().getPage(), pageSize));
        return result.map((object -> ObjectMapper.map(object, UserDto.class)));
    }

    private Specification<UserEntity> getSpecification(UserDto filter) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getTerm() != null && !filter.getTerm().isEmpty()) {
                Predicate predicate_1 = cb.like(cb.lower(root.get("firstName")),  "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_2 = cb.like(cb.lower(root.get("email")),  "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_3 = cb.like(cb.lower(root.get("phone")),  "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_4 = cb.like(cb.lower(root.get("lastName")),  "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_5 = cb.like(cb.lower(root.get("profile").get("name")),  "%" + filter.getTerm().toLowerCase() + "%");

                predicates.add(cb.or(predicate_1, predicate_2, predicate_3, predicate_4, predicate_5));
            }

            if (filter.getProfile() != null && !filter.getProfile().getName().isEmpty()) {
                predicates.add(cb.equal(root.get("role"),  filter.getProfile().getName()));
            }

            query.orderBy(cb.desc(root.get("id")));
            predicates.add(cb.equal(root.get("deleted"), false));
            Predicate[] predicatesArray = new Predicate[predicates.size()];
            return cb.and(predicates.toArray(predicatesArray));

        };
    }

    @Override
    @Transactional
    public void save(UserDto dto) {
        UserEntity userEntity = null;
        Optional<UserEntity> optional = null;
        byte[] imageData = null;
        
        if (dto.getCurrentPassword() != null  && !dto.getCurrentPassword().isEmpty()
                && dto.getNewPassword() != null && !dto.getNewPassword().isEmpty()
                && dto.getCurrentPassword().equals(dto.getNewPassword()))
            throw new BusinessException("SAME-PASSWORD", HttpStatus.CONFLICT);
            
        if (dto.getImage() != null && !dto.getImage().isEmpty())
            imageData = Base64.getDecoder().decode(dto.getImage());


        if(dto.getId() == null){
            optional = userRepository.findByEmailAndDeletedFalse(dto.getEmail());

            if(optional.isPresent()){
                throw new BusinessException("USER-EXIST", HttpStatus.CONFLICT);
            }else {
                userEntity = ObjectMapper.map(dto, UserEntity.class);
                userEntity.setCreatedAt(LocalDateTime.now());

                userEntity = userRepository.save(userEntity);
                sendRegisterEmail(userEntity);
            }
        }else {
            optional = userRepository.findById(dto.getId());
            userEntity = optional.get();
            if(dto.getCurrentPassword()!= null && !dto.getCurrentPassword().isEmpty() && dto.getNewPassword()!= null && !dto.getNewPassword().isEmpty()){
                if (passwordEncoder.matches(dto.getCurrentPassword(), userEntity.getPassword())) {
                    userEntity.setPassword(passwordEncoder.encode(dto.getNewPassword()));
                }else {
                    throw new BusinessException("WRONG-PASSWORD", HttpStatus.CONFLICT);
                }
            }

            userEntity.setFirstName(dto.getFirstName());
            userEntity.setLastName(dto.getLastName());
            userEntity.setPhone(dto.getPhone());
            userEntity.setEmail(dto.getEmail());
            userEntity.setAddress(dto.getAddress());
            if (dto.getProfile() != null) {
                userEntity.setProfile(ObjectMapper.map(dto.getProfile(), ProfileEntity.class));
            }

            if (dto.getService() != null) {
                userEntity.setService(ObjectMapper.map(dto.getService(), ListeEntity.class));
            }

            userEntity.setEnabled(dto.isEnabled());
            userEntity.setLocked(dto.isLocked());
            userEntity.setLocked(dto.isLocked());
            userEntity.setImage(imageData);

            userRepository.save(userEntity);
        }
    }

    @Override
    public void delete(Long id) {
        Optional<UserEntity> entity = userRepository.findById(id);
        if(entity.isPresent()){
            UserEntity user = entity.get();
            user.setDeleted(true);
            userRepository.save(user);
        }
    }

    @Override
    public UserDto findById(Long id) {
        Optional<UserEntity> entity = userRepository.findById(id);
        return entity.map(userEntity -> ObjectMapper.map(userEntity, UserDto.class)).orElse(null);
    }

    @Transactional
    protected void sendRegisterEmail(UserEntity user) {
        Map<String, String> model = new HashMap<>();

        String otp =  user.getEmail() + ":" + this.otpGenerator.generateOTP(user.getEmail(), 16);
        String secret = Base64.getUrlEncoder().encodeToString(otp.getBytes());
        String url = this.applicationProperties.getWebUrl().getUrl() + "/" + secret;


        // Charger le contenu HTML
        String content = loadHtmlTemplate()
                .replace("[content]", applicationProperties.getMailTemplatesConfig().getRegisterMailContent())
                .replace("[first_name]", user.getFirstName())
                .replace("[last_name]", user.getLastName())
                .replace("[email]", user.getEmail())
                .replace("[Link_create_account]", url);

        // prepare model
        model.put("content", content);
        model.put("receiver", user.getEmail());
        model.put("subject", "Création de votre accès à l'application Capital Trust");

        // send mail
        mailService.send(model);
    }

    private String loadHtmlTemplate() {
        try {
            String path = applicationProperties.getMailTemplatesConfig().getMailTemplatePath();
            if (path.startsWith("classpath:")) {
                path = path.substring("classpath:".length());
            }
            org.springframework.core.io.ClassPathResource resource = new org.springframework.core.io.ClassPathResource(path + "mail_template.html");
            try (java.io.InputStream is = resource.getInputStream()) {
                return org.springframework.util.StreamUtils.copyToString(is, java.nio.charset.StandardCharsets.UTF_8);
            }
        } catch (Exception e) {
            throw new RuntimeException("ERROR_LOADING_TEMPLATE_HTML", e);
        }
    }


}
