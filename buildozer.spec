[app]
# (str) Title of your application
title = 点收单识别  # 手机上显示的App名称

# (str) Package name
package.name = receiptocr     # 包名（小写，无空格）

# (str) Package domain (needed for android/ios packaging)
package.domain = org.ocr      # 域名（随便填，格式对就行）

# (str) Source code where the main.py live
source.dir = .       # 代码目录（当前文件夹）

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = venv,test,docs,bin,build

# (list) List of exclusions using pattern matching
# Do not prefix with './'
source.exclude_patterns = license,*.pyc,*.pyo

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
# 依赖配置（最终版，无遗漏）
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow==10.1.0,requests==2.31.0,tencentcloud-sdk-python==3.0.1104,plyer==2.1.0,datetime

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21  # 新增：支持安卓5.0+

# (int) Android SDK version to use
android.sdk = 24

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use.
android.ndk_api = 21

# 新增：防止内存溢出
android.ndk_heap_size = 512m

# (list) Put these files or directories in the apk assets directory.
android.add_assets =.

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

# 新增：自动接受SDK许可证
android.accept_sdk_license = True

# 新增：适配KivyMD的安卓主题
android.apptheme = "@android:style/Theme.Material.Light.NoActionBar"

# 新增：跳过字节编译（加速打包）
android.no-byte-compile-python = False

# 新增：强制UTF-8编码（解决中文乱码）
android.encoding = utf-8

# 新增：允许所有网络访问
android.whitelist = *

# 新增：复制库文件提升兼容性
android.copy_libs = 1

# 新增：剥离调试符号（减小APK体积）
android.strip = True

# 注释：无图标文件时不要启用
# android.icon = icon.png       # 可选：放一个图标文件（没有就注释掉）

#
# Python for android (p4a) specific
#
# 新增：强制使用SDL2引导（Kivy推荐）
p4a.bootstrap = sdl2

# 新增：禁用setup.py避免冲突
p4a.setup_py = false

# 新增：跳过SDK更新（加速打包）
p4a.extra_args = --no-update-sdk

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1