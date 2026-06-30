package com.binewvision.Motulbackend.controllers.Staffing;

import com.binewvision.Motulbackend.entities.Staffing.Collaborator;
import com.binewvision.Motulbackend.entities.Staffing.Imputation;
import com.binewvision.Motulbackend.entities.Project.Project;
import com.binewvision.Motulbackend.repositories.Staffing.CollaboratorRepository;
import com.binewvision.Motulbackend.repositories.Staffing.ImputationRepository;
import com.binewvision.Motulbackend.repositories.Project.Projectrepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/staffing")
@RequiredArgsConstructor
@CrossOrigin(origins = "${cors.allowed-origins:http://localhost:4200}")
public class StaffingController {

    private final CollaboratorRepository collaboratorRepository;
    private final ImputationRepository imputationRepository;
    private final Projectrepository projectRepository;

    @GetMapping("/collaborateurs")
    public ResponseEntity<List<Collaborator>> getCollaborators() {
        return ResponseEntity.ok(collaboratorRepository.findAll());
    }

    @PostMapping("/collaborateurs")
    public ResponseEntity<Collaborator> createCollaborator(@RequestBody Collaborator collaborator) {
        return ResponseEntity.status(HttpStatus.CREATED).body(collaboratorRepository.save(collaborator));
    }

    @DeleteMapping("/collaborateurs/{id}")
    public ResponseEntity<Void> deleteCollaborator(@PathVariable Long id) {
        collaboratorRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/imputations")
    public ResponseEntity<List<Imputation>> getImputations() {
        return ResponseEntity.ok(imputationRepository.findAll());
    }

    @PostMapping("/imputations")
    public ResponseEntity<Imputation> createImputation(@RequestBody Imputation imputation) {
        return ResponseEntity.status(HttpStatus.CREATED).body(imputationRepository.save(imputation));
    }

    @DeleteMapping("/imputations/{id}")
    public ResponseEntity<Void> deleteImputation(@PathVariable Long id) {
        imputationRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/projets")
    public ResponseEntity<List<Project>> getProjects() {
        return ResponseEntity.ok(projectRepository.findAll());
    }

    @PostMapping("/projets")
    public ResponseEntity<Project> createProject(@RequestBody Project project) {
        return ResponseEntity.status(HttpStatus.CREATED).body(projectRepository.save(project));
    }

    @DeleteMapping("/projets/{id}")
    public ResponseEntity<Void> deleteProject(@PathVariable Long id) {
        projectRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
