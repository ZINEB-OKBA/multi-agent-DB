package com.binewvision.Motulbackend.controllers.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.AmmcDto;
import com.binewvision.Motulbackend.services.airflow_data.AmmcService;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("ammc")
@AllArgsConstructor
public class AmmcController {
    private AmmcService ammcService;
    @PostMapping(value = "/find")
    public ResponseEntity<Page<AmmcDto>> findAll(@RequestBody AmmcDto filter) {
        Page<AmmcDto> pages = ammcService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }
}
