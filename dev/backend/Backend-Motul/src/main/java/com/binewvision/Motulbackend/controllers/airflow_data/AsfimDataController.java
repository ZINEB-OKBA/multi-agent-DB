package com.binewvision.Motulbackend.controllers.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.AsfimDataDto;
import com.binewvision.Motulbackend.services.airflow_data.AsfimDataService;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("asfim-data")
@AllArgsConstructor
public class AsfimDataController {
    private AsfimDataService asfimDataService;
    @PostMapping(value = "/find")
    public ResponseEntity<Page<AsfimDataDto>> findAll(@RequestBody AsfimDataDto filter) {
        Page<AsfimDataDto> pages = asfimDataService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }
}
