package com.packsure.backend.scan.service;

import lombok.extern.slf4j.Slf4j;

import javax.imageio.ImageIO;
import java.awt.Image;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;

/**
 * Shrinks a large photo before it is sent to the ML service. Phone photos are
 * often 4000+ px / several MB, and CPU OCR on those is very slow; a 1600 px
 * long-edge JPEG keeps label text legible while cutting analysis time sharply.
 */
@Slf4j
final class ImageDownscaler {

    private ImageDownscaler() {
    }

    static byte[] toMaxDimension(byte[] original, int maxEdge) {
        try {
            BufferedImage src = ImageIO.read(new ByteArrayInputStream(original));
            if (src == null) {
                return original; // not a decodable image — let the ML service reject it
            }
            int w = src.getWidth();
            int h = src.getHeight();
            double scale = Math.min(1.0, (double) maxEdge / Math.max(w, h));
            int nw = Math.max(1, (int) Math.round(w * scale));
            int nh = Math.max(1, (int) Math.round(h * scale));

            Image scaled = src.getScaledInstance(nw, nh, Image.SCALE_SMOOTH);
            BufferedImage out = new BufferedImage(nw, nh, BufferedImage.TYPE_INT_RGB);
            out.getGraphics().drawImage(scaled, 0, 0, null);

            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(out, "jpg", baos);
            byte[] result = baos.toByteArray();
            log.info("Downscaled image for ML: {}x{} ({} KB) -> {}x{} ({} KB)",
                    w, h, original.length / 1024, nw, nh, result.length / 1024);
            return result;
        } catch (Exception e) {
            log.warn("Image downscale failed ({}); sending original", e.getMessage());
            return original;
        }
    }
}
