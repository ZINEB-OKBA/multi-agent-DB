package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.administration.ListeDto;
import com.binewvision.Motulbackend.entities.administration.ListeEntity;
import com.binewvision.Motulbackend.repositories.administration.ListRepository;
import com.binewvision.Motulbackend.repositories.administration.UserRepository;
import com.binewvision.Motulbackend.security.config.AuthenticationFacade;
import com.binewvision.Motulbackend.services.administration.ListService;
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
public class ListServiceImpl implements ListService {

    private final ListRepository listRepository;
    private final AuthenticationFacade authenticationFacade;
    private final UserRepository userRepository;

    @Override
    public Page<ListeDto> findAll(ListeDto filter) {
        Page<ListeEntity> entities = listRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, ListeDto.class));
    }


    @Override
    public ListeDto findById(Long id) {
        Optional<ListeEntity> entity = listRepository.findById(id);
        if(entity.isPresent()){
            return ObjectMapper.map(entity, ListeDto.class);
        }
        return null;
    }

    @Override
    public ListeDto save(ListeDto object) {
        ListeEntity entity = ObjectMapper.map(object, ListeEntity.class);

        if (entity.getId() == null) {
            entity.setCreatedOn(LocalDateTime.now());
            entity.setCreatedBy(authenticationFacade.getCurrentUser());
        } else {
            entity.setUpdatedOn(LocalDateTime.now());
            entity.setUpdatedBy(authenticationFacade.getCurrentUser());
        }

        entity = listRepository.save(entity);
        return ObjectMapper.map(entity, ListeDto.class);
    }

    @Override
    public void delete(Long id) {
        Optional<ListeEntity> optional = listRepository.findById(id);
        if(optional.isPresent()){
            ListeEntity entity = optional.get();
            entity.setDeleted(true);
            listRepository.save(entity);
        }
    }

    private Specification<ListeEntity> getSpecification(ListeDto filter) {
        return (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();


            if (filter.getNature() != null && !filter.getNature().isEmpty()) {
                predicates.add(criteriaBuilder.equal(criteriaBuilder.lower(root.get("nature")), filter.getNature().toLowerCase()));
            }

            if (filter.getLabel() != null && !filter.getLabel().isEmpty()) {
                predicates.add(criteriaBuilder.like(criteriaBuilder.lower(root.get("label")), "%" + filter.getLabel().toLowerCase() + "%"));
            }

            if (filter.getValue() != null && !filter.getValue().isEmpty()) {
                predicates.add(criteriaBuilder.like(criteriaBuilder.lower(root.get("value")), "%" + filter.getValue().toLowerCase() + "%"));
            }

            if (filter.getParent() != null) {
                predicates.add(criteriaBuilder.equal(root.get("parent").get("id"), filter.getParent().getId()));
                query.orderBy(criteriaBuilder.asc(root.get("label")));
            }else {
                query.orderBy(criteriaBuilder.desc(root.get("id")));
            }

            if (filter.getTerm() != null && !filter.getTerm().isEmpty()) {
                Predicate predicate_1 = criteriaBuilder.like(criteriaBuilder.lower(root.get("label")), "%" + filter.getTerm().toLowerCase() + "%");
                Predicate predicate_2 = criteriaBuilder.like(criteriaBuilder.lower(root.get("value")), "%" + filter.getTerm().toLowerCase() + "%");

                predicates.add(criteriaBuilder.or(predicate_1, predicate_2));
            }

            predicates.add(criteriaBuilder.equal(root.<Boolean>get("deleted"), false));
            Predicate[] predicatesArray = new Predicate[predicates.size()];

            return criteriaBuilder.and(predicates.toArray(predicatesArray));
        };
    }

    private PageRequest getPageRequest(PageDto pageDto) {
        int pageSize = pageDto.getSize();
        if (pageSize <= 0) {
            pageSize = Integer.MAX_VALUE;
        }
        int pageNumber = pageDto.getPage();
        if (pageDto.isSortable()) {
            String directionStr = pageDto.getDirection();
            String column = pageDto.getColumn();

            Sort.Direction direction = Sort.Direction.ASC;
            if ("DESC".equalsIgnoreCase(directionStr)) {
                direction = Sort.Direction.DESC;
            }

            Sort sort = Sort.by(direction, column);
            return PageRequest.of(pageNumber, pageSize, sort);
        }
        return PageRequest.of(pageNumber, pageSize);
    }

}
