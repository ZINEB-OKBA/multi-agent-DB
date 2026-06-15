package com.binewvision.Motulbackend.services.administration;

import com.binewvision.Motulbackend.dtos.administration.UserDto;
import org.springframework.data.domain.Page;

public interface UserService {
    Page<UserDto> findAll(UserDto filter);
    void save(UserDto dto);
    void delete(Long id);
    UserDto findById(Long id);
}
