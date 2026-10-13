<?php
/**
 * Global Rank Math settings bridge for the companion plugin.
 *
 * Rank Math stores its settings in a single WordPress option named
 * `rank-math-options-titles`, `rank-math-options-sitemap`, and so on.
 * Rather than guess every key, we expose a small, verified subset and
 * write to the correct option group per field.
 *
 * Safety:
 *   - Only the fields declared in FIELD_MAP are ever read or written.
 *   - Every value is sanitized through WPSEO_Control_Sanitizer.
 *   - No PHP execution, no SQL, no direct database writes.
 *
 * @package WP_SEO_Control
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class WPSEO_Control_RankMath_Settings {

    /**
     * Map of our field name to [ option_name, key, type ].
     *
     * Rank Math option group names have been stable for years. If a group
     * ever changes, only this map needs updating.
     */
    public const FIELD_MAP = array(
        // Titles
        'title_separator' => array( 'rank-math-options-titles', 'title_separator', 'text' ),
        'homepage_title' => array( 'rank-math-options-titles', 'homepage_title', 'text' ),
        'homepage_description' => array( 'rank-math-options-titles', 'homepage_description', 'text' ),

        // Sitemap
        'sitemap_enabled' => array( 'rank-math-options-sitemap', 'sitemap', 'bool_on' ),
        'sitemap_include_products' => array( 'rank-math-options-sitemap', 'pt_product_sitemap', 'bool_on' ),
        'sitemap_include_posts' => array( 'rank-math-options-sitemap', 'pt_post_sitemap', 'bool_on' ),
        'sitemap_include_pages' => array( 'rank-math-options-sitemap', 'pt_page_sitemap', 'bool_on' ),

        // Indexing
        'noindex_empty_category' => array( 'rank-math-options-titles', 'noindex_empty_category', 'bool_on' ),
        'noindex_search' => array( 'rank-math-options-titles', 'noindex_search', 'bool_on' ),
        'noindex_author_archives' => array( 'rank-math-options-titles', 'noindex_author_archive', 'bool_on' ),
        'noindex_date_archives' => array( 'rank-math-options-titles', 'noindex_date_archive', 'bool_on' ),

        // Breadcrumbs
        'breadcrumbs_enabled' => array( 'rank-math-options-general', 'breadcrumbs', 'bool_on' ),

        // WooCommerce
        'wc_remove_category_base' => array( 'rank-math-options-titles', 'wc_remove_category_base', 'bool_on' ),
        'wc_show_product_breadcrumbs' => array( 'rank-math-options-general', 'breadcrumbs_products', 'bool_on' ),
    );

    /**
     * Whether Rank Math is active.
     */
    public static function is_active(): bool {
        return defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' );
    }

    /**
     * Rank Math version string, if known.
     */
    public static function version(): string {
        if ( defined( 'RANK_MATH_VERSION' ) ) {
            return (string) RANK_MATH_VERSION;
        }
        return '';
    }

    /**
     * Read all supported settings.
     *
     * @return array<string, mixed>
     */
    public static function get_all(): array {
        $out = array();
        foreach ( self::FIELD_MAP as $field => $spec ) {
            list( $option_name, $key, $type ) = $spec;
            $option = get_option( $option_name, array() );
            if ( ! is_array( $option ) ) {
                $option = array();
            }
            $raw = array_key_exists( $key, $option ) ? $option[ $key ] : null;
            $out[ $field ] = self::cast_read( $type, $raw );
        }
        return $out;
    }

    /**
     * Update provided settings. Only keys present in $data are written.
     *
     * @param array<string, mixed> $data
     * @return array<string, mixed>  The settings after the write.
     */
    public static function set( array $data ): array {
        // Group updates by option_name so we read-modify-write once per group.
        $grouped = array();
        foreach ( $data as $field => $value ) {
            if ( ! isset( self::FIELD_MAP[ $field ] ) ) {
                continue;
            }
            list( $option_name, $key, $type ) = self::FIELD_MAP[ $field ];
            $grouped[ $option_name ][ $key ] = self::cast_write( $type, $value );
        }

        foreach ( $grouped as $option_name => $kv ) {
            $option = get_option( $option_name, array() );
            if ( ! is_array( $option ) ) {
                $option = array();
            }
            foreach ( $kv as $k => $v ) {
                $option[ $k ] = $v;
            }
            update_option( $option_name, $option );
        }

        return self::get_all();
    }

    /**
     * Cast a raw WordPress value to our external representation.
     */
    private static function cast_read( string $type, $raw ) {
        switch ( $type ) {
            case 'bool_on':
                return ( 'on' === $raw || true === $raw || 1 === $raw );
            case 'text':
            default:
                return is_string( $raw ) ? $raw : '';
        }
    }

    /**
     * Cast an external value to what Rank Math stores.
     */
    private static function cast_write( string $type, $value ) {
        switch ( $type ) {
            case 'bool_on':
                return $value ? 'on' : 'off';
            case 'text':
            default:
                return WPSEO_Control_Sanitizer::text( (string) $value );
        }
    }
}