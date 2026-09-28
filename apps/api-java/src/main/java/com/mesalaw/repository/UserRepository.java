package com.mesalaw.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.auth.User;

@Repository
public interface UserRepository extends JpaRepository<User, String> {

    Optional<User> findByKeycloakId(String keycloakId);

    Optional<User> findByEmail(String email);

    boolean existsByKeycloakId(String keycloakId);
}
