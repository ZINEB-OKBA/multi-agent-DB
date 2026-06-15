package com.binewvision.Motulbackend.services.airflow_data.Impl;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.airflow_data.AmmcDto;
import com.binewvision.Motulbackend.entities.airflow_data.AmmcEntity;
import com.binewvision.Motulbackend.repositories.airflow_data.AmmcRepository;
import com.binewvision.Motulbackend.services.airflow_data.AmmcService;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AmmcServiceImpl implements AmmcService {

    private final AmmcRepository ammcRepository;

    @Override
    public Page<AmmcDto> findAll(AmmcDto filter) {
        Page<AmmcEntity> entities = ammcRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, AmmcDto.class));
    }

    private Specification<AmmcEntity> getSpecification(AmmcDto filter) {
        return (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();

            query.orderBy(criteriaBuilder.desc(root.get("id")));
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
