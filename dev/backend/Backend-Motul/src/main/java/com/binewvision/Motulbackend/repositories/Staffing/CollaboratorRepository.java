package com.binewvision.Motulbackend.repositories.Staffing;

import com.binewvision.Motulbackend.entities.Staffing.Collaborator;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CollaboratorRepository extends JpaRepository<Collaborator, Long> {
}
