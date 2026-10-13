<?php
/**
 * Sanitization helpers for the companion plugin.
 *
 * Every value received over REST is sanitized through here before being
 * passed to update_post_meta. We never accept raw HTML for Rank Math
 * fields — Rank Math itself uses text for title/description/keyword.
 *
 * @package WP_SEO_Control
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class WPSEO_Control_Sanitizer {

    /**
     * Sanitize a plain-text field (title, description, focus keyword).
     */
    public static function text( $value ): string {
        if ( null === $value ) {
            return '';
        }
        return sanitize_text_field( (string) $value );
    }

    /**
     * Sanitize a URL field (canonical, social image).
     */
    public static function url( $value ): string {
        if ( null === $value ) {
            return '';
        }
        return esc_url_raw( (string) $value );
    }

    /**
     * Sanitize an array of robots directives.
     * Only a known set of values is allowed.
     *
     * @return string[]
     */
    public static function robots( $value ): array {
        if ( ! is_array( $value ) ) {
            return array();
        }
        $allowed = array(
            'index',
            'noindex',
            'follow',
            'nofollow',
            'noarchive',
            'nosnippet',
            'noimageindex',
            'max-snippet:-1',
            'max-video-preview:-1',
            'max-image-preview:large',
        );
        $clean = array();
        foreach ( $value as $item ) {
            $item = sanitize_text_field( (string) $item );
            if ( in_array( $item, $allowed, true ) ) {
                $clean[] = $item;
            }
        }
        return array_values( array_unique( $clean ) );
    }
}