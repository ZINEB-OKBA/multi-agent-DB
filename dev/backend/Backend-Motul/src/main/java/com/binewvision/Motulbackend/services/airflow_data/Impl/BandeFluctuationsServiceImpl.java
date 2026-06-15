package com.binewvision.Motulbackend.services.airflow_data.Impl;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.airflow_data.BandeFluctuationsDto;
import com.binewvision.Motulbackend.entities.airflow_data.BandeFluctuationsEntity;
import com.binewvision.Motulbackend.repositories.airflow_data.BandeFluctuationsRepository;
import com.binewvision.Motulbackend.services.airflow_data.BandeFluctuationsService;
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
public class BandeFluctuationsServiceImpl implements BandeFluctuationsService {
    private final BandeFluctuationsRepository bandeFluctuationsRepository;
    @Override
    public Page<BandeFluctuationsDto> findAll(BandeFluctuationsDto filter) {
        Page<BandeFluctuationsEntity> entities = bandeFluctuationsRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, BandeFluctuationsDto.class));
    }

    private Specification<BandeFluctuationsEntity> getSpecification(BandeFluctuationsDto filter) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getTerm() != null && !filter.getTerm().trim().isEmpty()) {

                String likeTerm = "%" + filter.getTerm().toLowerCase() + "%";
                Predicate devisePredicate = cb.like(cb.lower(root.get("devises")), likeTerm);
                predicates.add(cb.or(devisePredicate));
            }

            if (filter.getStartDate() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("scrapingDate"), filter.getStartDate()));
            }

            if (filter.getEndDate() != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("scrapingDate"), filter.getEndDate()));
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
