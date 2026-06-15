package com.binewvision.Motulbackend.controllers.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.AsfimDto;
import com.binewvision.Motulbackend.services.airflow_data.AsfimDataService;
import com.binewvision.Motulbackend.services.airflow_data.AsfimService;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("asfim")
@AllArgsConstructor
public class AsfimController {
    private AsfimService asfimService;
    private AsfimDataService asfimDataService;
    @PostMapping(value = "/find")
    public ResponseEntity<Page<AsfimDto>> findAll(@RequestBody AsfimDto filter) {
        Page<AsfimDto> pages = asfimService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }
}
