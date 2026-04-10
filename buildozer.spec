[app]
title = VPN Shield
package.name = vpnshield
package.domain = org.vpnshield
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.3.0,pillow
orientation = portrait
fullscreen = 1
android.presplash_color = #070B18
android.gradient_colors = #070B18,#0A0E1A

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34
android.archs = arm64-v8a
android.allow_backup = False
android.release_artifact = apk
