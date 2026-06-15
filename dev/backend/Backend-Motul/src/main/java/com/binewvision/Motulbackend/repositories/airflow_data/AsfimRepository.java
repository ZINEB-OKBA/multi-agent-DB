package com.binewvision.Motulbackend.repositories.airflow_data;

import com.binewvision.Motulbackend.entities.airflow_data.AsfimEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface AsfimRepository extends JpaRepository<AsfimEntity,Long>, JpaSpecificationExecutor<AsfimEntity> {
}
