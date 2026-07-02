package com.binewvision.Motulbackend.controllers.Project;


import com.binewvision.Motulbackend.dtos.Projectdto;
import com.binewvision.Motulbackend.services.Project.Projectservice;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/projects")
@RequiredArgsConstructor
@CrossOrigin(origins = "${cors.allowed-origins:http://localhost:4200}")
public class Projectcontroller {

    private final Projectservice projectService;

    /**
     * GET /api/projects
     * Liste légère de tous les projets pour la vue principale Angular
     * (grille de cards, chaque card affiche nom + nb docs + nb indexés).
     */
    @GetMapping
    public ResponseEntity<List<Projectdto.Summary>> listProjects() {
        return ResponseEntity.ok(projectService.listAll());
    }

    /**
     * POST /api/projects
     * Crée un nouveau projet depuis le formulaire Angular.
     * Body : { "name": "mon_projet", "description": "..." }
     */
    @PostMapping
    public ResponseEntity<Projectdto.Response> createProject(
            @Valid @RequestBody Projectdto.CreateRequest req
    ) {
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(projectService.create(req));
    }

    /**
     * GET /api/projects/{id}
     * Détail complet d'un projet avec la liste de tous ses documents.
     * Appelé quand l'utilisateur clique sur une card de projet.
     */
    @GetMapping("/{id}")
    public ResponseEntity<Projectdto.Response> getProject(@PathVariable Long id) {
        return ResponseEntity.ok(projectService.getById(id));
    }

    /**
     * DELETE /api/projects/{id}
     * Supprime le projet et tous ses documents (cascade).
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteProject(@PathVariable Long id) {
        projectService.delete(id);
        return ResponseEntity.noContent().build();
    }
}