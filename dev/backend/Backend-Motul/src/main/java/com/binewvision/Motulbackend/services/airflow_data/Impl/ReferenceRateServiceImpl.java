package com.binewvision.Motulbackend.services.airflow_data.Impl;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.airflow_data.ReferenceRateDto;
import com.binewvision.Motulbackend.entities.airflow_data.ReferenceRateEntity;
import com.binewvision.Motulbackend.repositories.airflow_data.ReferenceRateRepository;
import com.binewvision.Motulbackend.services.airflow_data.ReferenceRateService;
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
public class ReferenceRateServiceImpl implements ReferenceRateService {
    private final ReferenceRateRepository referenceRateRepository;
    @Override
    public Page<ReferenceRateDto> findAll(ReferenceRateDto filter) {
        Page<ReferenceRateEntity> entities = referenceRateRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, ReferenceRateDto.class));
    }

    private Specification<ReferenceRateEntity> getSpecification(ReferenceRateDto filter) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getStartDate() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("date"), filter.getStartDate()));
            }

            if (filter.getEndDate() != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("date"), filter.getEndDate()));
            }

            if (filter.getTerm() != null && !filter.getTerm().trim().isEmpty()) {

                String likeTerm = "%" + filter.getTerm().toLowerCase() + "%";
                Predicate devisePredicate = cb.like(cb.lower(root.get("devise")), likeTerm);
                predicates.add(cb.or(devisePredicate));
            }


            query.orderBy(cb.desc(root.get("id")));
            Predicate[] predicatesArray = new Predicate[predicates.size()];

            return cb.and(predicates.toArray(predicatesArray));
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
