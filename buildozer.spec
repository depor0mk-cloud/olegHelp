[app]
title = VPN Shield
package.name = vpnshield
package.domain = org.vpnshield
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.2.1
orientation = portrait
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 23b
android.sdk = 31
android.ndk_api = 21
android.archs = arm64-v8a
android.allow_backup = False
android.accept_sdk_license = True
android.skip_update = False
