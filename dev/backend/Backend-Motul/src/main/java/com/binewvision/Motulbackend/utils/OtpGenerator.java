package com.binewvision.Motulbackend.utils;

import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import org.springframework.stereotype.Service;

import java.util.Random;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Service
public class OtpGenerator {
    private final LoadingCache<String, String> otpCache;

    public OtpGenerator(){
        otpCache = CacheBuilder.newBuilder()
                .expireAfterWrite(60, TimeUnit.MINUTES)
                .build(new CacheLoader<>() {
                    @Override
                    public String load(String s){
                        return "0";
                    }
                });
    }

    /**
     * Method for generating OTP and put it in cache.
     *
     * @param key - cache key
     * @param length - opt length
     * @return cache value (generated OTP number)
     */
    public Integer generateOTP(String key, int length) {
        Random random = new Random();
        int rang = (int)Math.pow(10, length-1);
        int OTP = rang + random.nextInt(9* rang);
        otpCache.put(key, String.valueOf(OTP));

        return OTP;
    }

    /**
     * Method for generating OTP and put it in cache.
     *
     * @param length - opt length
     * @return cache value (generated OTP number)
     */
    public String generateOTP(int length) {
        String AB = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#&$@-abcdefghijklmnopqrstuvwxyz";
        Random rnd = new Random();

        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(AB.charAt(rnd.nextInt(AB.length())));
        }
        return sb.toString();
    }

    public String generateUUID(String key) {
        String uuid = UUID.randomUUID().toString();
        otpCache.put(key, uuid);

        return uuid;
    }

    /**
     * Method for getting OTP value by key.
     *
     * @param key - target key
     * @return OTP value
     */
    public String getOPTByKey(String key) {
        return otpCache.getIfPresent(key);
    }

    /**
     * Method for removing key from cache.
     *
     * @param key - target key
     */
    public void clearOTPFromCache(String key) {
        otpCache.invalidate(key);
    }

    /**
     * Method for validating provided OTP
     *
     * @param key       - provided key
     * @param otp - provided OTP number
     * @return boolean value (true|false)
     */
    public boolean validateOTP(String key, String otp) {
        // get OTP from cache
        String cacheOTP = getOPTByKey(key);
        if (cacheOTP != null && cacheOTP.equals(otp)) {
            clearOTPFromCache(key);
            return true;
        }
        return false;
    }
}
