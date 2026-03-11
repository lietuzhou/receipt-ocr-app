[app]
title = 点收单识别 

package.name = receiptocr  

package.domain = org.ocr      

source.dir = .      

source.include_exts = py,png,jpg,kv,atlas

source.exclude_exts = spec

source.exclude_dirs = venv,test,docs,bin,build

source.exclude_patterns = license,*.pyc,*.pyo

version = 0.1

requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow==10.1.0,requests==2.31.0,tencentcloud-sdk-python==3.0.1104,plyer==2.1.0,datetime

orientation = portrait


fullscreen = 0

android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,ACCESS_NETWORK_STATE

android.api = 33

android.minapi = 21 

android.sdk = 24

android.ndk = 25b

android.ndk_api = 21

android.ndk_heap_size = 512m

android.add_assets =.

android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

android.debug_artifact = apk

android.accept_sdk_license = True

android.apptheme = "@android:style/Theme.Material.Light.NoActionBar"

android.no-byte-compile-python = False

android.encoding = utf-8

android.whitelist = *

android.copy_libs = 1

android.strip = True

android.icon = icon.png     


p4a.bootstrap = sdl2

p4a.setup_py = false


p4a.extra_args = --no-update-sdk

[buildozer]

log_level = 2

warn_on_root = 1
