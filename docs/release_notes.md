# Release Notes

### **Big** New Features :
1. Automatic Asset Type Filtering for Categorories.
2. 100% Overhaul to the web backend static REST calls to realtime Web Sockets.
3. Introducing a Markdown editor for asset / tutorial documentation.

#### **Small** New Features:
1. Attribute view has been visually updated and supports grouping.

### **Major** Changes :
1. Removal of ffmpeg & OpenCV in favor of PyAV. Reduces file size.
2. Faster (13x) filesystem iteration collection for ingestion.
3. Faster (4x) proxy + preview file generation LDR (jpg, png, tif).
4. Faster (2-3x) proxy + preview file generation HDR (exr, hdr).
5. Converted python to Executables via PyInstaller.

#### **Minor** Changes & Tweaks :
1. UI Indication of Admin mode when enabled.
2. Batch update selected assets across multiple categories.
3. Ability to create lower quality / smaller GIFs in capture.

### **Bug Fixes** :
1. Fix session stall isses when rapidly changing subcategory selections.
