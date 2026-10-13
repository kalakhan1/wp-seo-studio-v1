<?php
/**
 * Uninstall cleanup.
 *
 * Removes only the options this plugin created. Never deletes post meta
 * that belongs to Rank Math. Never touches any WordPress core tables.
 *
 * @package WP_SEO_Control
 */

if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
    exit;
}

delete_option( 'wpseo_control_version' );
delete_option( 'wpseo_control_activated_at' );