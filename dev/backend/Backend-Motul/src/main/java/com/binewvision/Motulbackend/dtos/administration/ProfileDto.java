package com.binewvision.Motulbackend.dtos.administration;


import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Setter
@Getter
public class ProfileDto {

    private Long id;
    private String name;
    private List<RoleDto> roles;

    private PageDto page;

    private String histoType;
    private String createdBy;
    private String updatedBy;
    private LocalDateTime createdOn;
    private LocalDateTime updatedOn;
    private String term;
    private boolean deleted;
}
