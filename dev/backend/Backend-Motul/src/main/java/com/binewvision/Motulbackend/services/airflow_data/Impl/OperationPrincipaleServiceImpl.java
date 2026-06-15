package com.binewvision.Motulbackend.services.airflow_data.Impl;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.airflow_data.OperationPrincipaleDto;
import com.binewvision.Motulbackend.entities.airflow_data.OperationPrincipaleEntity;
import com.binewvision.Motulbackend.enums.InstrumentTypeEnum;
import com.binewvision.Motulbackend.repositories.airflow_data.OperationPrincipaleRepository;
import com.binewvision.Motulbackend.services.airflow_data.OperationPrincipaleService;
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
public class OperationPrincipaleServiceImpl implements OperationPrincipaleService {
    private final OperationPrincipaleRepository operationPrincipaleRepository;
    @Override
    public Page<OperationPrincipaleDto> findAll(OperationPrincipaleDto filter) {
        Page<OperationPrincipaleEntity> entities = operationPrincipaleRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, OperationPrincipaleDto.class));
    }

    private Specification<OperationPrincipaleEntity> getSpecification(OperationPrincipaleDto filter) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getStartDate() != null || filter.getEndDate() != null) {
                Predicate dateDeValeurPredicate = cb.conjunction();
                Predicate dateAppelOffresPredicate = cb.conjunction();

                if (filter.getStartDate() != null) {
                    dateDeValeurPredicate = cb.and(dateDeValeurPredicate, cb.greaterThanOrEqualTo(root.get("dateDeValeur"), filter.getStartDate()));
                    dateAppelOffresPredicate = cb.and(dateAppelOffresPredicate, cb.greaterThanOrEqualTo(root.get("dateAppelOffres"), filter.getStartDate()));
                }

                if (filter.getEndDate() != null) {
                    dateDeValeurPredicate = cb.and(dateDeValeurPredicate, cb.lessThanOrEqualTo(root.get("dateDeValeur"), filter.getEndDate()));
                    dateAppelOffresPredicate = cb.and(dateAppelOffresPredicate, cb.lessThanOrEqualTo(root.get("dateAppelOffres"), filter.getEndDate()));
                }

                predicates.add(cb.or(dateDeValeurPredicate, dateAppelOffresPredicate));
            }

            if (filter.getInstrument() != null && !filter.getInstrument().trim().isEmpty()) {

                Predicate instrumentPredicate;
                
                if (InstrumentTypeEnum.AVANCES_7_JOURS.name().equals(filter.getInstrument())){
                    instrumentPredicate = cb.like(cb.lower(root.get("instrument")), "%avances%");
                    predicates.add(instrumentPredicate);
                } else if (InstrumentTypeEnum.REPRISE_LIQUIDITE_7_JOURS.name().equals(filter.getInstrument())) {
                    instrumentPredicate = cb.like(cb.lower(root.get("instrument")), "%reprise%");
                    predicates.add(instrumentPredicate);

                }


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
