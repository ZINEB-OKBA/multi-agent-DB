package com.binewvision.Motulbackend.services.airflow_data.Impl;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.airflow_data.MarcheMonetaireDto;
import com.binewvision.Motulbackend.entities.airflow_data.MarcheMonetaireEntity;
import com.binewvision.Motulbackend.repositories.airflow_data.MarcheMonetaireRepository;
import com.binewvision.Motulbackend.services.airflow_data.MarcheMonetaireService;
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
public class MarcheMonetaireServiceImpl implements MarcheMonetaireService {
    private final MarcheMonetaireRepository marcheMonetaireRepository;
    @Override
    public Page<MarcheMonetaireDto> findAll(MarcheMonetaireDto filter) {
        Page<MarcheMonetaireEntity> entities = marcheMonetaireRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, MarcheMonetaireDto.class));
    }

    private Specification<MarcheMonetaireEntity> getSpecification(MarcheMonetaireDto filter) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getStartDate() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("date"), filter.getStartDate()));
            }

            if (filter.getEndDate() != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("date"), filter.getEndDate()));
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
