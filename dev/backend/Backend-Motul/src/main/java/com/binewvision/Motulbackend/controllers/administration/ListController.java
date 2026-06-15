package com.binewvision.Motulbackend.controllers.administration;

import com.binewvision.Motulbackend.dtos.administration.ListeDto;
import com.binewvision.Motulbackend.services.administration.ListService;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


@RestController
@RequestMapping("lists")
@AllArgsConstructor
public class ListController {

    private final ListService listService;

    @PostMapping(value = "/find")
    public ResponseEntity<Page<ListeDto>> findAll(@RequestBody ListeDto filter) {
        Page<ListeDto> pages = listService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @GetMapping(value = "/find/{id}")
    public ResponseEntity<ListeDto> findById(@PathVariable("id") Long id) {
        ListeDto list = listService.findById(id);
        return new ResponseEntity<>(list, HttpStatus.OK);
    }

    @PostMapping(value = "/save")
    public ResponseEntity<ListeDto> save(@RequestBody ListeDto object) {
        object = listService.save(object);
        return new ResponseEntity<>(object, HttpStatus.OK);
    }

    @GetMapping(value = "/delete/{id}")
    public ResponseEntity<Boolean> delete(@PathVariable("id") Long id) {
        listService.delete(id);
        return new ResponseEntity<>(true, HttpStatus.OK);
    }

}
