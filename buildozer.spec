[app]

# (str) Title of your application
title = My Vault App

# (str) Package name
package.name = myvault

# (str) Package domain (needed for android packaging)
package.domain = org.aadu

# (str) Source code where the main.py is located
source.dir = .

# (list) Source files to include (let's include everything)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 0.1

# (list) Application requirements
# CRITICAL: You must include flet here!
requirements = python3, flet

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Android API to use (33 is standard for now)
android.api = 33

# (int) Minimum API your app will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use the private storage for the app
android.private_storage = True

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off)
warn_on_root = 1
