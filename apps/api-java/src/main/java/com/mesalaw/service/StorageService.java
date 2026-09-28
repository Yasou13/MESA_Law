package com.mesalaw.service;

import java.net.URI;
import java.time.Duration;

import org.springframework.stereotype.Service;

import com.mesalaw.config.AppProperties;

import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.HeadObjectRequest;
import software.amazon.awssdk.services.s3.model.HeadObjectResponse;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;

/**
 * S3/MinIO storage service for presigned URL generation and object operations.
 * Replaces Python's {@code core/storage.py StorageService}.
 */
@Service
@Slf4j
public class StorageService {

    private final S3Client s3Client;
    private final S3Presigner presigner;
    private final String bucket;
    private final int uploadTtl;
    private final int downloadTtl;

    public StorageService(AppProperties props) {
        AppProperties.Storage storage = props.getStorage();
        this.bucket = storage.getBucket();
        this.uploadTtl = storage.getUploadUrlTtlSeconds();
        this.downloadTtl = storage.getDownloadUrlTtlSeconds();

        AwsBasicCredentials credentials = AwsBasicCredentials.create(
                storage.getAccessKey(), storage.getSecretKey());

        this.s3Client = S3Client.builder()
                .endpointOverride(URI.create(storage.getEndpoint()))
                .credentialsProvider(StaticCredentialsProvider.create(credentials))
                .region(Region.US_EAST_1) // MinIO doesn't use regions
                .forcePathStyle(true)     // Required for MinIO
                .build();

        this.presigner = S3Presigner.builder()
                .endpointOverride(URI.create(storage.getEndpoint()))
                .credentialsProvider(StaticCredentialsProvider.create(credentials))
                .region(Region.US_EAST_1)
                .build();
    }

    /**
     * Generate a presigned PUT URL for uploading.
     * Replaces Python: storage_service.generate_presigned_upload_url()
     */
    public String generatePresignedUploadUrl(String key, String contentType) {
        PutObjectRequest putRequest = PutObjectRequest.builder()
                .bucket(bucket)
                .key(key)
                .contentType(contentType)
                .build();

        PutObjectPresignRequest presignRequest = PutObjectPresignRequest.builder()
                .signatureDuration(Duration.ofSeconds(uploadTtl))
                .putObjectRequest(putRequest)
                .build();

        return presigner.presignPutObject(presignRequest).url().toString();
    }

    /**
     * Generate a presigned GET URL for downloading.
     * Replaces Python: storage_service.generate_presigned_download_url()
     */
    public String generatePresignedDownloadUrl(String key) {
        GetObjectRequest getRequest = GetObjectRequest.builder()
                .bucket(bucket)
                .key(key)
                .build();

        GetObjectPresignRequest presignRequest = GetObjectPresignRequest.builder()
                .signatureDuration(Duration.ofSeconds(downloadTtl))
                .getObjectRequest(getRequest)
                .build();

        return presigner.presignGetObject(presignRequest).url().toString();
    }

    /**
     * Get object metadata (size, content type).
     * Replaces Python: storage_service.get_object_metadata()
     */
    public HeadObjectResponse getObjectMetadata(String key) {
        HeadObjectRequest headRequest = HeadObjectRequest.builder()
                .bucket(bucket)
                .key(key)
                .build();

        return s3Client.headObject(headRequest);
    }

    /**
     * Get object bytes.
     * Replaces Python: storage_service.get_object_bytes()
     */
    public byte[] getObjectBytes(String key) {
        GetObjectRequest getRequest = GetObjectRequest.builder()
                .bucket(bucket)
                .key(key)
                .build();

        return s3Client.getObjectAsBytes(getRequest).asByteArray();
    }
}
