=== WP SEO Control Companion ===
Contributors: wpseocontrol
Tags: seo, rankmath, rest-api, woocommerce
Requires at least: 6.0
Tested up to: 6.6
Requires PHP: 8.0
Stable tag: 0.1.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

A small companion plugin that exposes a safe, minimal REST API for the
WP SEO Control Studio. It registers only the endpoints the studio needs,
with strict capability checks and sanitization.

== Description ==

WordPress does not expose Rank Math's per-post SEO metadata through the
standard REST API. This plugin fills that gap without touching Rank Math's
own database tables or admin UI.

Endpoints (namespace `wp-seo-control/v1`):

* `GET  /status` — public, non-sensitive info (plugin version, Rank Math active).
* `GET  /rankmath/meta/{post_id}` — read supported Rank Math meta.
* `POST /rankmath/meta/{post_id}` — write supported Rank Math meta.

Only these Rank Math keys are read/written:

* `rank_math_title`
* `rank_math_description`
* `rank_math_focus_keyword`
* `rank_math_canonical_url`
* `rank_math_robots`
* `rank_math_facebook_title`
* `rank_math_facebook_description`
* `rank_math_facebook_image`
* `rank_math_twitter_title`
* `rank_math_twitter_description`
* `rank_math_twitter_image`

== Security ==

* All mutating requests require a logged-in user with the `edit_post`
  capability on the target post.
* All field values are sanitized before being written.
* No endpoint accepts raw PHP, SQL, or HTML.
* No endpoint modifies Rank Math settings globally.
* The plugin never reads or writes WordPress database tables directly.

== Installation ==

1. Upload the `wp-seo-control-companion` folder to `/wp-content/plugins/`.
2. Activate the plugin in WordPress.
3. Configure the WP SEO Control Studio to use an Application Password
   for a user with rights to create and edit content.

== Uninstallation ==

Deleting the plugin from the WordPress admin removes its options.
Per-post Rank Math metadata is never touched — it belongs to Rank Math.

== Changelog ==

= 0.1.0 =
* Initial release.