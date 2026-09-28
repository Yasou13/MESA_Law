package com.mesalaw.entity.research;

import com.mesalaw.entity.base.BaseEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A curated collection of legal sources (e.g. "Turkish Labor Law 2025").
 * Replaces Python's {@code SourcePackage} from models/research.py.
 */
@Entity
@Table(name = "source_packages")
@Getter
@Setter
@NoArgsConstructor
public class SourcePackage extends BaseEntity {

    @Column(name = "name", nullable = false, unique = true)
    private String name;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "version", nullable = false)
    private String version = "1.0.0";
}
