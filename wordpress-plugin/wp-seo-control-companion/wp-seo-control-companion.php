<?php
/**
 * Plugin Name:       WP SEO Control Companion
 * Plugin URI:        https://example.com/wp-seo-control-companion
 * Description:       Exposes a safe, minimal REST API for the WP SEO Control Studio. Registers only the endpoints the studio needs, with strict capability checks and sanitization.
 * Version:           0.1.0
 * Requires at least: 6.0
 * Requires PHP:      8.0
 * Author:            WP SEO Control Studio
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       wp-seo-control
 * Domain Path:       /languages
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'WPSEO_CONTROL_VERSION', '0.1.0' );
define( 'WPSEO_CONTROL_FILE', __FILE__ );
define( 'WPSEO_CONTROL_DIR', plugin_dir_path( __FILE__ ) );
define( 'WPSEO_CONTROL_URL', plugin_dir_url( __FILE__ ) );
define( 'WPSEO_CONTROL_NAMESPACE', 'wp-seo-control/v1' );

require_once WPSEO_CONTROL_DIR . 'includes/class-sanitizer.php';
require_once WPSEO_CONTROL_DIR . 'includes/class-rankmath-bridge.php';
require_once WPSEO_CONTROL_DIR . 'includes/class-rankmath-settings.php';
require_once WPSEO_CONTROL_DIR . 'includes/class-rest-controller.php';
require_once WPSEO_CONTROL_DIR . 'includes/class-plugin.php';

register_activation_hook( __FILE__, array( 'WPSEO_Control_Plugin', 'activate' ) );
register_deactivation_hook( __FILE__, array( 'WPSEO_Control_Plugin', 'deactivate' ) );

add_action( 'plugins_loaded', array( 'WPSEO_Control_Plugin', 'init' ) );