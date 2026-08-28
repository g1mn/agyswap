package com.example.backend;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class CacheService {
    private final Map<String, Object> store = new ConcurrentHashMap<>();

    public static void main(String[] args) {
        System.out.println("cache online");
    }

    public Object get(String key) {
        return store.get(key);
    }

    private synchronized boolean evictExpired() {
        return true;
    }
}
