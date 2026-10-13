<?php
/**
 * Bridge between the companion REST API and Rank Math post meta.
 *
 * Rank Math stores per-post SEO data as post meta with specific keys.
 * We only touch documented keys and always sanitize before writing.
 *
 * If Rank Math is not active, `is_active()` returns false and the bridge
 * refuses to read or write meta. This is intentional: we never guess.
 *
 * @package WP_SEO_Control
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class WPSEO_Control_RankMath_Bridge {

    /**
     * Map of our friendly field name => Rank Math meta key.
     *
     * These keys are stable across recent Rank Math versions. If a key is
     * ever renamed upstream, this map is the single place to update.
     */
    public const META_KEYS = array(
        'title'                => 'rank_math_title',
        'description'          => 'rank_math_description',
        'focus_keyword'        => 'rank_math_focus_keyword',
        'canonical_url'        => 'rank_math_canonical_url',
        'robots'               => 'rank_math_robots',
        'facebook_title'       => 'rank_math_facebook_title',
        'facebook_description' => 'rank_math_facebook_description',
        'facebook_image'       => 'rank_math_facebook_image',
        'twitter_title'        => 'rank_math_twitter_title',
        'twitter_description'  => 'rank_math_twitter_description',
        'twitter_image'        => 'rank_math_twitter_image',
    );

    /**
     * Whether Rank Math is active in this WordPress installation.
     */
    public static function is_active(): bool {
        // Rank Math defines RANK_MATH_VERSION when active.
        return defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' );
    }

    /**
     * Read all supported Rank Math meta for a post.
     *
     * @return array<string, mixed>
     */
    public static function get_meta( int $post_id ): array {
        $out = array();
        foreach ( self::META_KEYS as $field => $meta_key ) {
            $value = get_post_meta( $post_id, $meta_key, true );
            $out[ $field ] = $value;
        }
        return $out;
    }

    /**
     * Write supported Rank Math meta for a post.
     *
     * Only keys present in $data are written. Unknown keys are ignored.
     *
     * @param array<string, mixed> $data
     * @return array<string, mixed> The resulting meta after the write.
     */
    public static function set_meta( int $post_id, array $data ): array {
        if ( array_key_exists( 'title', $data ) ) {
            self::update( $post_id, 'title', WPSEO_Control_Sanitizer::text( $data['title'] ) );
        }
        if ( array_key_exists( 'description', $data ) ) {
            self::update( $post_id, 'description', WPSEO_Control_Sanitizer::text( $data['description'] ) );
        }
        if ( array_key_exists( 'focus_keyword', $data ) ) {
            self::update( $post_id, 'focus_keyword', WPSEO_Control_Sanitizer::text( $data['focus_keyword'] ) );
        }
        if ( array_key_exists( 'canonical_url', $data ) ) {
            self::update( $post_id, 'canonical_url', WPSEO_Control_Sanitizer::url( $data['canonical_url'] ) );
        }
        if ( array_key_exists( 'robots', $data ) ) {
            self::update( $post_id, 'robots', WPSEO_Control_Sanitizer::robots( $data['robots'] ) );
        }
        if ( array_key_exists( 'facebook_title', $data ) ) {
            self::update( $post_id, 'facebook_title', WPSEO_Control_Sanitizer::text( $data['facebook_title'] ) );
        }
        if ( array_key_exists( 'facebook_description', $data ) ) {
            self::update( $post_id, 'facebook_description', WPSEO_Control_Sanitizer::text( $data['facebook_description'] ) );
        }
        if ( array_key_exists( 'facebook_image', $data ) ) {
            self::update( $post_id, 'facebook_image', WPSEO_Control_Sanitizer::url( $data['facebook_image'] ) );
        }
        if ( array_key_exists( 'twitter_title', $data ) ) {
            self::update( $post_id, 'twitter_title', WPSEO_Control_Sanitizer::text( $data['twitter_title'] ) );
        }
        if ( array_key_exists( 'twitter_description', $data ) ) {
            self::update( $post_id, 'twitter_description', WPSEO_Control_Sanitizer::text( $data['twitter_description'] ) );
        }
        if ( array_key_exists( 'twitter_image', $data ) ) {
            self::update( $post_id, 'twitter_image', WPSEO_Control_Sanitizer::url( $data['twitter_image'] ) );
        }
        return self::get_meta( $post_id );
    }

    /**
     * Update a single meta key.
     */
    private static function update( int $post_id, string $field, $value ): void {
        $meta_key = self::META_KEYS[ $field ] ?? null;
        if ( ! $meta_key ) {
            return;
        }
        update_post_meta( $post_id, $meta_key, $value );
    }
}