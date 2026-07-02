package com.binewvision.Motulbackend.repositories.Staffing;

import com.binewvision.Motulbackend.entities.Staffing.Imputation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ImputationRepository extends JpaRepository<Imputation, Long> {
}
