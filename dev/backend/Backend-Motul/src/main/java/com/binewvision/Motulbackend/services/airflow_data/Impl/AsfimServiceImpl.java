package com.binewvision.Motulbackend.services.airflow_data.Impl;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.airflow_data.AsfimDto;
import com.binewvision.Motulbackend.entities.airflow_data.AsfimEntity;
import com.binewvision.Motulbackend.repositories.airflow_data.AsfimRepository;
import com.binewvision.Motulbackend.services.airflow_data.AsfimService;
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
public class AsfimServiceImpl implements AsfimService {
    private final AsfimRepository asfimRepository;
    @Override
    public Page<AsfimDto> findAll(AsfimDto filter) {
        Page<AsfimEntity> entities = asfimRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, AsfimDto.class));
    }

    private Specification<AsfimEntity> getSpecification(AsfimDto filter) {
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
