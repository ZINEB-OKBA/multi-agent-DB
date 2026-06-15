package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.administration.authentication.AttemptAuthenticationDto;
import com.binewvision.Motulbackend.entities.administration.UserEntity;
import com.binewvision.Motulbackend.entities.administration.authentication.AttemptAuthenticationEntity;
import com.binewvision.Motulbackend.entities.administration.authentication.AttemptFailedAuthenticationEntity;
import com.binewvision.Motulbackend.entities.administration.authentication.AttemptForgotPasswordEntity;
import com.binewvision.Motulbackend.repositories.administration.authentication.AttemptAuthenticationRepository;
import com.binewvision.Motulbackend.repositories.administration.authentication.AttemptFailedAuthenticationRepository;
import com.binewvision.Motulbackend.repositories.administration.authentication.AttemptForgotPasswordRepository;
import com.binewvision.Motulbackend.services.administration.AttemptAuthenticationService;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import jakarta.persistence.criteria.Predicate;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.security.authentication.event.AuthenticationFailureBadCredentialsEvent;
import org.springframework.security.authentication.event.AuthenticationSuccessEvent;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AttemptAuthenticationServiceImpl implements AttemptAuthenticationService {

    private final AttemptAuthenticationRepository attemptAuthenticationRepository;
    private final AttemptForgotPasswordRepository attemptForgotPasswordRepository;
    private final AttemptFailedAuthenticationRepository attemptFailedAuthenticationRepository;
    private final ApplicationProperties properties;


    @Override
    public Page<AttemptAuthenticationDto> findAll(AttemptAuthenticationDto filter) {
        Page<AttemptAuthenticationEntity> entities = attemptAuthenticationRepository.findAll(getSpecification(filter), getPageRequest(filter.getPage()));
        return entities.map((object -> ObjectMapper.map(object, AttemptAuthenticationDto.class)));
    }

    @Override
    public void save(HttpServletRequest request, AuthenticationSuccessEvent event) {

        AttemptAuthenticationEntity entity = new AttemptAuthenticationEntity();

        String userAgentHeader = request.getHeader("User-Agent");
        String browser = detectBrowser(userAgentHeader);

        entity.setSuccess(true);
        entity.setBrowser(browser);
        entity.setIp(request.getRemoteAddr());
        entity.setCreatedOn(LocalDateTime.now());
        entity.setUsername(event.getAuthentication().getName());

        attemptAuthenticationRepository.save(entity);
    }

    @Override
    public void failedSave(HttpServletRequest request, AuthenticationFailureBadCredentialsEvent event) {

        AttemptAuthenticationEntity entity = new AttemptAuthenticationEntity();
        AttemptFailedAuthenticationEntity failedAuthenticationEntity = new AttemptFailedAuthenticationEntity();

        String userAgentHeader = request.getHeader("User-Agent");
        String browser = detectBrowser(userAgentHeader);

        entity.setSuccess(false);
        entity.setBrowser(browser);
        entity.setIp(request.getRemoteAddr());
        entity.setCreatedOn(LocalDateTime.now());
        entity.setUsername(event.getAuthentication().getName());

        attemptAuthenticationRepository.save(entity);

        failedAuthenticationEntity.setBrowser(browser);
        failedAuthenticationEntity.setIp(request.getRemoteAddr());
        failedAuthenticationEntity.setUsername(event.getAuthentication().getName());

        attemptFailedAuthenticationRepository.save(failedAuthenticationEntity);
    }

    @Override
    public boolean reachedMaxFailedAttempt(String username) {
        List<AttemptFailedAuthenticationEntity> failedAuthenticationEntityList = attemptFailedAuthenticationRepository.findAllByUsername(username);
        return failedAuthenticationEntityList.size() >= properties.getMaxFailedAttempts().getLogin();
    }

    @Override
    @Transactional
    public void forgotPasswordSave(HttpServletRequest request, UserEntity user) {
        AttemptForgotPasswordEntity entity = new AttemptForgotPasswordEntity();

        String userAgentHeader = request.getHeader("User-Agent");
        String browser = detectBrowser(userAgentHeader);

        entity.setBrowser(browser);
        entity.setUsername(user.getEmail());
        entity.setIp(request.getRemoteAddr());
        entity.setCreatedOn(LocalDateTime.now());

        attemptForgotPasswordRepository.save(entity);
    }

    @Override
    public boolean reachedMaxForgotPasswordAttempt(UserEntity user) {
        List<AttemptForgotPasswordEntity> forgotPasswordEntityList = attemptForgotPasswordRepository.findAllByUsername(user.getEmail());
        return forgotPasswordEntityList.size() >= properties.getMaxFailedAttempts().getForgotPwd();
    }

    @Override
    @Transactional
    public void resetFailedAttempts(String username) {
        attemptFailedAuthenticationRepository.deleteAllByUsername(username);
    }

    @Override
    @Transactional
    public void resetForogotPasswordAttempts(String username) {
        attemptForgotPasswordRepository.deleteAllByUsername(username);
    }

    private String detectBrowser(String userAgent) {
        if (userAgent == null) return "Unknown";

        userAgent = userAgent.toLowerCase();

        if (userAgent.contains("edge")) return "Edge";
        if (userAgent.contains("edg")) return "Edge (Chromium)";
        if (userAgent.contains("chrome")) return "Chrome";
        if (userAgent.contains("safari") && !userAgent.contains("chrome")) return "Safari";
        if (userAgent.contains("firefox")) return "Firefox";
        if (userAgent.contains("opera") || userAgent.contains("opr")) return "Opera";
        if (userAgent.contains("msie") || userAgent.contains("trident")) return "Internet Explorer";

        return "Other";
    }

    private PageRequest getPageRequest(PageDto pageDto){
        int pageSize = pageDto.getSize();
        if (pageSize <= 0) {
            pageSize = Integer.MAX_VALUE;
        }
        int pageNumber = pageDto.getPage();
        if (pageDto.isSortable()) {
            String directionStr = pageDto.getDirection();
            String column = pageDto.getColumn();

            Sort.Direction direction = Sort.Direction.ASC;
            if (directionStr != null && directionStr.equalsIgnoreCase("DESC")) {
                direction = Sort.Direction.DESC;
            }

            Sort sort = Sort.by(direction, column);
            return PageRequest.of(pageNumber, pageSize, sort);
        }
        return PageRequest.of(pageNumber, pageSize);
    }

    private Specification<AttemptAuthenticationEntity> getSpecification(AttemptAuthenticationDto filter) {
        return (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getTerm() != null && !filter.getTerm().isEmpty()) {

                Predicate predicate_1 = criteriaBuilder.like(criteriaBuilder.lower(root.get("ip")),  "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_2 = criteriaBuilder.like(criteriaBuilder.lower(root.get("browser")),  "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_3 = criteriaBuilder.like(criteriaBuilder.lower(root.get("username")),  "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_4 = criteriaBuilder.like(criteriaBuilder.lower(criteriaBuilder.function("TO_CHAR", String.class, root.get("createdOn"), criteriaBuilder.literal("dd/MM/yyyy"))),  "%" + filter.getTerm().toLowerCase() + "%");

                predicates.add(criteriaBuilder.or(predicate_1, predicate_2, predicate_3, predicate_4));
            }

            Predicate[] predicatesArray = new Predicate[predicates.size()];
            query.orderBy(criteriaBuilder.desc(root.get("id")));
            return criteriaBuilder.and(predicates.toArray(predicatesArray));
        };
    }
}
