package com.binewvision.Motulbackend.services.airflow_data.Impl;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.airflow_data.AsfimDataDto;
import com.binewvision.Motulbackend.entities.airflow_data.AsfimDataEntity;
import com.binewvision.Motulbackend.repositories.airflow_data.AsfimDataRepository;
import com.binewvision.Motulbackend.services.airflow_data.AsfimDataService;
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
public class AsfimDataServiceImpl implements AsfimDataService {
    private final AsfimDataRepository asfimDataRepository;
    @Override
    public Page<AsfimDataDto> findAll(AsfimDataDto filter) {
        Page<AsfimDataEntity> entities = asfimDataRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, AsfimDataDto.class));
    }

    private Specification<AsfimDataEntity> getSpecification(AsfimDataDto filter) {
        return (root, query, cb) -> {

            List<Predicate> predicates = new ArrayList<>();

            if (filter.getDateDepotFrom() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("dateDepot"), filter.getDateDepotFrom()));
            }

            if (filter.getDateDepotTo() != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("dateDepot"), filter.getDateDepotTo()));
            }

            if (filter.getTerm() != null && !filter.getTerm().trim().isEmpty()) {

                String likeTerm = "%" + filter.getTerm().toLowerCase() + "%";

                Predicate fondPredicate = cb.like(cb.lower(root.get("fond")), likeTerm);

                Predicate categoriePredicate = cb.like(cb.lower(root.get("categorie")), likeTerm);

                Predicate societeGestionPredicate = cb.like(cb.lower(root.get("societeGestion")), likeTerm);

                predicates.add(cb.or(fondPredicate, categoriePredicate, societeGestionPredicate));
            }

            query.orderBy(cb.desc(root.get("dateDepot")), cb.desc(root.get("id")));

            return cb.and(predicates.toArray(new Predicate[0]));
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
