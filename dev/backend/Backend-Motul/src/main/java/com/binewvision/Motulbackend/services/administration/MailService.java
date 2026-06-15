package com.binewvision.Motulbackend.services.administration;

import java.util.Map;

public interface MailService {
    boolean send(Map<String, String> model);
}