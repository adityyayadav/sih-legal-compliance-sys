package com.packsure.backend.scan;

import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "declarations")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Declaration {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "scan_id", nullable = false)
    private Scan scan;

    @Column(nullable = false)
    private String declarationType;

    @Column(nullable = false)
    private boolean isPresent;

    @Column(columnDefinition = "TEXT")
    private String extractedValue;

    private Double confidenceScore;

    @Column(columnDefinition = "TEXT")
    private String boundingBox;
}
