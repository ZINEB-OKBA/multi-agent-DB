package com.binewvision.Motulbackend.repositories.Project;


import com.binewvision.Motulbackend.entities.Project.Project;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface Projectrepository extends JpaRepository<Project, Long> {

    Optional<Project> findByName(String name);

    boolean existsByName(String name);

    /** Liste des projets triés du plus récent au plus ancien. */
    List<Project> findAllByOrderByCreatedAtDesc();

    /**
     * Projets avec le nombre de documents pré-chargé pour éviter le N+1.
     * Utilisé par la liste principale affichée dans le front.
     */
    @Query("""
        SELECT DISTINCT p FROM Project p
        LEFT JOIN FETCH p.documents d
        ORDER BY p.createdAt DESC
    """)
    List<Project> findAllWithDocuments();
}