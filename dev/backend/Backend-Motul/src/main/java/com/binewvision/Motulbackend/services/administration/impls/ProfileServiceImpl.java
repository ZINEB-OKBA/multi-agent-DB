package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.administration.ModuleDto;
import com.binewvision.Motulbackend.dtos.administration.ProfileDto;
import com.binewvision.Motulbackend.dtos.administration.RoleDto;
import com.binewvision.Motulbackend.entities.administration.ModuleEntity;
import com.binewvision.Motulbackend.entities.administration.ProfileEntity;
import com.binewvision.Motulbackend.entities.administration.RoleEntity;
import com.binewvision.Motulbackend.entities.administration.UserEntity;
import com.binewvision.Motulbackend.repositories.administration.ModuleRepository;
import com.binewvision.Motulbackend.repositories.administration.ProfileRepository;
import com.binewvision.Motulbackend.repositories.administration.RoleRepository;
import com.binewvision.Motulbackend.repositories.administration.UserRepository;
import com.binewvision.Motulbackend.security.config.AuthenticationFacade;
import com.binewvision.Motulbackend.services.administration.ProfileService;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class ProfileServiceImpl implements ProfileService {

    private final AuthenticationFacade authenticationFacade;
    private final ProfileRepository profileRepository;
    private final UserRepository userRepository;
    private final ModuleRepository moduleRepository;
    private final RoleRepository roleRepository;

    @Override
    public Page<ProfileDto> findAll(ProfileDto filter) {
        Page<ProfileEntity> entities = profileRepository.findAll(getSpecification(filter), getPageRequest(filter.getPage()));
        return entities.map((object -> ObjectMapper.map(object, ProfileDto.class)));
    }

    @Override
    public ProfileDto findById(Long id) {
        Optional<ProfileEntity> entity = profileRepository.findById(id);
        return entity.map(profileEntity -> ObjectMapper.map(profileEntity, ProfileDto.class)).orElse(null);
    }

    @Override
    public ProfileDto save(ProfileDto object) {
        ProfileEntity entity = ObjectMapper.map(object, ProfileEntity.class);
        if (entity.getId() == null){
            entity.setCreatedOn(LocalDateTime.now());
            entity.setCreatedBy(authenticationFacade.getCurrentUser());
        }else {
            entity.setUpdatedOn(LocalDateTime.now());
            entity.setUpdatedBy(authenticationFacade.getCurrentUser());
        }
        entity = profileRepository.save(entity);
        return ObjectMapper.map(entity, ProfileDto.class);
    }

    @Override
    public void delete(Long id) {
        Optional<ProfileEntity> optional = profileRepository.findById(id);
        if(optional.isPresent()){
            ProfileEntity entity = optional.get();

            entity.setDeleted(true);
            profileRepository.save(entity);
        }
    }

    @Override
    public List<ModuleDto> getModules() {
        List<ModuleEntity> entities = moduleRepository.findAllByOrderByOrdre();
        return ObjectMapper.mapAll(entities, ModuleDto.class);
    }

    @Override
    public List<RoleDto> getRolesByModules(ModuleDto module) {
        List<RoleEntity> entities = roleRepository.findAllByModule(ObjectMapper.map(module , ModuleEntity.class));
        return ObjectMapper.mapAll(entities, RoleDto.class);
    }

    @Override
    public List<RoleDto> getCurrentUserRoles() {
        Optional<UserEntity> currentUser = this.userRepository.findByEmailAndDeletedFalse(this.authenticationFacade.getCurrentUser());
        if(currentUser.isPresent()){
            return ObjectMapper.mapAll(currentUser.get().getProfile().getRoles(), RoleDto.class);
        }
        return List.of();
    }


    private Specification<ProfileEntity> getSpecification(ProfileDto filter) {
        return (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getTerm() != null && !filter.getTerm().isEmpty()) {
                Predicate predicate_1 = criteriaBuilder.like(criteriaBuilder.lower(root.get("name")),  "%" + filter.getTerm().toLowerCase() + "%");

                predicates.add(criteriaBuilder.or(predicate_1));
            }

            if (filter.getName() != null && !filter.getName().isEmpty()) {
                predicates.add(criteriaBuilder.like(criteriaBuilder.lower(root.get("name")), "%" + filter.getName().toLowerCase() + "%"));
            }

            predicates.add(criteriaBuilder.equal(root.<Boolean>get("deleted"), false));
            Predicate[] predicatesArray = new Predicate[predicates.size()];

            return criteriaBuilder.and(predicates.toArray(predicatesArray));
        };
    }

    private  PageRequest getPageRequest(PageDto pageDto){
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


}
