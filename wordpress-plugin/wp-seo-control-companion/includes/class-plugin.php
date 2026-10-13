<?php
/**
 * Main plugin class. Wires up REST routes and admin notices.
 *
 * @package WP_SEO_Control
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class WPSEO_Control_Plugin {

    /**
     * Called on plugin activation.
     * Records the plugin version so future migrations can run.
     */
    public static function activate(): void {
        update_option( 'wpseo_control_version', WPSEO_CONTROL_VERSION );
        update_option( 'wpseo_control_activated_at', time() );
    }

    /**
     * Called on plugin deactivation.
     * Does NOT delete user data — data removal is handled by uninstall.php.
     */
    public static function deactivate(): void {
        // Intentionally minimal.
    }

    /**
     * Boot the plugin. Called on plugins_loaded.
     */
    public static function init(): void {
        $controller = new WPSEO_Control_REST_Controller();
        add_action( 'rest_api_init', array( $controller, 'register_routes' ) );
    }
}