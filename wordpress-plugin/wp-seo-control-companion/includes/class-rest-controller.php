<?php
/**
 * REST endpoints exposed by the companion plugin.
 *
 * Namespace: wp-seo-control/v1
 *
 * Endpoints:
 *   GET  /status                     — public; plugin version, Rank Math active.
 *   GET  /rankmath/meta/{post_id}    — requires edit_post on the target post.
 *   POST /rankmath/meta/{post_id}    — requires edit_post on the target post.
 *   GET  /rankmath/settings          — requires manage_options.
 *   POST /rankmath/settings          — requires manage_options.
 *
 * Security:
 *   - All mutations require a valid logged-in user (Application Password).
 *   - Global settings require `manage_options`.
 *   - Every field is sanitized through WPSEO_Control_Sanitizer.
 *   - No endpoint accepts raw PHP, SQL, or HTML.
 *
 * @package WP_SEO_Control
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class WPSEO_Control_REST_Controller {

    public function register_routes(): void {
        register_rest_route(
            WPSEO_CONTROL_NAMESPACE,
            '/status',
            array(
                'methods'             => 'GET',
                'callback'            => array( $this, 'get_status' ),
                'permission_callback' => '__return_true',
            )
        );

        register_rest_route(
            WPSEO_CONTROL_NAMESPACE,
            '/rankmath/meta/(?P<post_id>\d+)',
            array(
                array(
                    'methods'             => 'GET',
                    'callback'            => array( $this, 'get_rankmath_meta' ),
                    'permission_callback' => array( $this, 'can_edit_post' ),
                    'args'                => array(
                        'post_id' => array(
                            'validate_callback' => fn( $v ) => is_numeric( $v ) && (int) $v > 0,
                            'sanitize_callback' => 'absint',
                        ),
                    ),
                ),
                array(
                    'methods'             => 'POST',
                    'callback'            => array( $this, 'set_rankmath_meta' ),
                    'permission_callback' => array( $this, 'can_edit_post' ),
                    'args'                => array(
                        'post_id' => array(
                            'validate_callback' => fn( $v ) => is_numeric( $v ) && (int) $v > 0,
                            'sanitize_callback' => 'absint',
                        ),
                    ),
                ),
            )
        );

        register_rest_route(
            WPSEO_CONTROL_NAMESPACE,
            '/rankmath/settings',
            array(
                array(
                    'methods'             => 'GET',
                    'callback'            => array( $this, 'get_settings' ),
                    'permission_callback' => array( $this, 'can_manage_options' ),
                ),
                array(
                    'methods'             => 'POST',
                    'callback'            => array( $this, 'set_settings' ),
                    'permission_callback' => array( $this, 'can_manage_options' ),
                ),
            )
        );
    }

    /**
     * Public status endpoint.
     */
    public function get_status(): WP_REST_Response {
        return new WP_REST_Response(
            array(
                'ok'              => true,
                'plugin_version'  => WPSEO_CONTROL_VERSION,
                'wp_version'      => get_bloginfo( 'version' ),
                'rank_math_active' => WPSEO_Control_RankMath_Bridge::is_active(),
                'rank_math_version' => WPSEO_Control_RankMath_Settings::version(),
                'namespace'       => WPSEO_CONTROL_NAMESPACE,
            ),
            200
        );
    }

    /**
     * Permission callback: user must be able to edit the target post.
     */
    public function can_edit_post( WP_REST_Request $request ) {
        $post_id = (int) $request->get_param( 'post_id' );
        if ( $post_id <= 0 ) {
            return new WP_Error( 'wpseo_invalid_post_id', 'Invalid post ID.', array( 'status' => 400 ) );
        }
        $post = get_post( $post_id );
        if ( ! $post ) {
            return new WP_Error( 'wpseo_post_not_found', 'Post not found.', array( 'status' => 404 ) );
        }
        if ( ! current_user_can( 'edit_post', $post_id ) ) {
            return new WP_Error( 'wpseo_forbidden', 'You do not have permission to edit this post.', array( 'status' => 403 ) );
        }
        return true;
    }

    /**
     * Permission callback for global settings: manage_options.
     */
    public function can_manage_options() {
        if ( ! current_user_can( 'manage_options' ) ) {
            return new WP_Error( 'wpseo_forbidden', 'You do not have permission to manage settings.', array( 'status' => 403 ) );
        }
        return true;
    }

    /**
     * Read Rank Math meta for a post.
     */
    public function get_rankmath_meta( WP_REST_Request $request ) {
        if ( ! WPSEO_Control_RankMath_Bridge::is_active() ) {
            return new WP_Error( 'wpseo_rankmath_inactive', 'Rank Math is not active on this site.', array( 'status' => 409 ) );
        }
        $post_id = (int) $request->get_param( 'post_id' );
        $meta    = WPSEO_Control_RankMath_Bridge::get_meta( $post_id );
        return new WP_REST_Response( array( 'ok' => true, 'post_id' => $post_id, 'meta' => $meta ), 200 );
    }

    /**
     * Write Rank Math meta for a post.
     */
    public function set_rankmath_meta( WP_REST_Request $request ) {
        if ( ! WPSEO_Control_RankMath_Bridge::is_active() ) {
            return new WP_Error( 'wpseo_rankmath_inactive', 'Rank Math is not active on this site.', array( 'status' => 409 ) );
        }
        $post_id = (int) $request->get_param( 'post_id' );
        $body    = $request->get_json_params();
        if ( ! is_array( $body ) ) {
            return new WP_Error( 'wpseo_invalid_body', 'Request body must be a JSON object.', array( 'status' => 400 ) );
        }
        $allowed = array_keys( WPSEO_Control_RankMath_Bridge::META_KEYS );
        $data    = array();
        foreach ( $allowed as $field ) {
            if ( array_key_exists( $field, $body ) ) {
                $data[ $field ] = $body[ $field ];
            }
        }
        $result = WPSEO_Control_RankMath_Bridge::set_meta( $post_id, $data );
        return new WP_REST_Response( array( 'ok' => true, 'post_id' => $post_id, 'meta' => $result ), 200 );
    }

    /**
     * Read global Rank Math settings.
     */
    public function get_settings() {
        if ( ! WPSEO_Control_RankMath_Settings::is_active() ) {
            return new WP_Error( 'wpseo_rankmath_inactive', 'Rank Math is not active on this site.', array( 'status' => 409 ) );
        }
        return new WP_REST_Response(
            array(
                'ok'      => true,
                'version' => WPSEO_Control_RankMath_Settings::version(),
                'settings' => WPSEO_Control_RankMath_Settings::get_all(),
            ),
            200
        );
    }

    /**
     * Update global Rank Math settings. Only provided fields are written.
     */
    public function set_settings( WP_REST_Request $request ) {
        if ( ! WPSEO_Control_RankMath_Settings::is_active() ) {
            return new WP_Error( 'wpseo_rankmath_inactive', 'Rank Math is not active on this site.', array( 'status' => 409 ) );
        }
        $body = $request->get_json_params();
        if ( ! is_array( $body ) ) {
            return new WP_Error( 'wpseo_invalid_body', 'Request body must be a JSON object.', array( 'status' => 400 ) );
        }
        $allowed = array_keys( WPSEO_Control_RankMath_Settings::FIELD_MAP );
        $data = array();
        foreach ( $allowed as $field ) {
            if ( array_key_exists( $field, $body ) ) {
                $data[ $field ] = $body[ $field ];
            }
        }
        if ( empty( $data ) ) {
            return new WP_Error( 'wpseo_no_fields', 'No recognized settings provided.', array( 'status' => 400 ) );
        }
        $updated = WPSEO_Control_RankMath_Settings::set( $data );
        return new WP_REST_Response(
            array(
                'ok' => true,
                'version' => WPSEO_Control_RankMath_Settings::version(),
                'settings' => $updated,
            ),
            200
        );
    }
}