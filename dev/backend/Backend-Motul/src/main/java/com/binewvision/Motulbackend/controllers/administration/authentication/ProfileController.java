package com.binewvision.Motulbackend.controllers.administration.authentication;

import com.binewvision.Motulbackend.dtos.administration.ModuleDto;
import com.binewvision.Motulbackend.dtos.administration.ProfileDto;
import com.binewvision.Motulbackend.dtos.administration.RoleDto;
import com.binewvision.Motulbackend.services.administration.ProfileService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/profiles")
@RequiredArgsConstructor
public class ProfileController {

    private final ProfileService profileService;

    @PostMapping(value = "/find")
    public ResponseEntity<Page<ProfileDto>> findAll(@RequestBody ProfileDto filter) {
        Page<ProfileDto> pages = profileService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }

    @GetMapping(value = "/get/{id}")
    public ResponseEntity<ProfileDto> findById(@PathVariable("id") Long id) {
        ProfileDto list = profileService.findById(id);
        return new ResponseEntity<>(list, HttpStatus.OK);
    }

    @PostMapping(value = "/save")
    public ResponseEntity<ProfileDto> save(@RequestBody ProfileDto object) {
        object = profileService.save(object);
        return new ResponseEntity<>(object, HttpStatus.OK);
    }

    @GetMapping(value = "/delete/{id}")
    public ResponseEntity<Boolean> delete(@PathVariable("id") Long id) {
        profileService.delete(id);
        return new ResponseEntity<>(true, HttpStatus.OK);
    }

    @GetMapping(value = "/roles")
    public ResponseEntity<List<RoleDto>> getRoles(){
        List<RoleDto> result = profileService.getCurrentUserRoles();

        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @PostMapping(value = "/roles-by-module")
    public ResponseEntity<List<RoleDto>> getRolesByModule(@RequestBody ModuleDto module){
        List<RoleDto> result = profileService.getRolesByModules(module);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }


    @GetMapping(value = "/modules")
    public ResponseEntity<List<ModuleDto>> getModules(){
        List<ModuleDto> result = profileService.getModules();
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

}
