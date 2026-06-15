package com.binewvision.Motulbackend.controllers.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.*;
import com.binewvision.Motulbackend.services.airflow_data.*;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("bkam")
@AllArgsConstructor
public class BkamController {
    private CoursBilletService coursBilletService;
    private BandeFluctuationsService bandeFluctuationsService;
    private HistoriqueDecisionService historiqueDecisionService;
    private IndiceMoniaService indiceMoniaService;
    private MarcheMonetaireService marcheMonetaireService;
    private ReferenceRateService referenceRateService;
    private OperationPrincipaleService operationPrincipaleService;

    @PostMapping(value = "/cours-billets")
    public ResponseEntity<Page<CoursBilletDto>> findAll(@RequestBody CoursBilletDto filter) {
        Page<CoursBilletDto> pages = coursBilletService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @PostMapping(value = "/bande-fluctuation")
    public ResponseEntity<Page<BandeFluctuationsDto>> findAll(@RequestBody BandeFluctuationsDto filter) {
        Page<BandeFluctuationsDto> pages = bandeFluctuationsService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @PostMapping(value = "/historique-decision")
    public ResponseEntity<Page<HistoriqueDecisionDto>> findAll(@RequestBody HistoriqueDecisionDto filter) {
        Page<HistoriqueDecisionDto> pages = historiqueDecisionService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @PostMapping(value = "/indice-monia")
    public ResponseEntity<Page<IndiceMoniaDto>> findAll(@RequestBody IndiceMoniaDto filter) {
        Page<IndiceMoniaDto> pages = indiceMoniaService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @PostMapping(value = "/marche-monetaire")
    public ResponseEntity<Page<MarcheMonetaireDto>> findAll(@RequestBody MarcheMonetaireDto filter) {
        Page<MarcheMonetaireDto> pages = marcheMonetaireService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @PostMapping(value = "/reference-rate")
    public ResponseEntity<Page<ReferenceRateDto>> findAll(@RequestBody ReferenceRateDto filter) {
        Page<ReferenceRateDto> pages = referenceRateService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @PostMapping(value = "/operations-principales")
    public ResponseEntity<Page<OperationPrincipaleDto>> findAll(@RequestBody OperationPrincipaleDto filter) {
        Page<OperationPrincipaleDto> pages = operationPrincipaleService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }
}
