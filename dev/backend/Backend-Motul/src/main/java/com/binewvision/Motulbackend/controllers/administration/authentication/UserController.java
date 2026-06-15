package com.binewvision.Motulbackend.controllers.administration.authentication;

import com.binewvision.Motulbackend.dtos.administration.UserDto;
import com.binewvision.Motulbackend.services.administration.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;


    @PostMapping("/save")
    public ResponseEntity<Boolean> save(@RequestBody UserDto user)  {
        userService.save(user);
        return ResponseEntity.ok(true);
    }

    @GetMapping(value = "/delete/{id}")
    public ResponseEntity<Boolean> delete(@PathVariable("id") Long id){
        userService.delete(id);
        return new ResponseEntity<>(true, HttpStatus.OK);
    }

    @PostMapping(value = "/find")
    public ResponseEntity<Page<UserDto>> find(@RequestBody UserDto filter){
        Page<UserDto> result = userService.findAll(filter);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @GetMapping(value = "/get/{id}")
    public ResponseEntity<UserDto> get(@PathVariable("id") Long id) {
        UserDto result = userService.findById(id);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

}
