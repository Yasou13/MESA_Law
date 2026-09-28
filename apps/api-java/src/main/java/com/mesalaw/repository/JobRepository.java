package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.queue.Job;
import com.mesalaw.entity.queue.JobStatus;

@Repository
public interface JobRepository extends JpaRepository<Job, String> {

    List<Job> findByTenantIdAndStatus(String tenantId, JobStatus status);

    List<Job> findByMatterId(String matterId);

    @Query(value = """
            SELECT * FROM legal_jobs
            WHERE status = 'PENDING'
              AND run_at <= NOW()
              AND (locked_until IS NULL OR locked_until < NOW())
            ORDER BY run_at ASC
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
            """, nativeQuery = true)
    List<Job> findClaimableJobs(int limit);
}
