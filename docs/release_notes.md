# Release Notes 

### **Big** New Features :
- Automatic Ingest Asset Type Filtering for destination Categorories.
- Overhauled the web backend functionality for realtime user exprience.
- Introducing a Markdown editor for asset / tutorial documentation.

### **Major** Changes :
- Attribute view has been visually updated and supports grouping.
- Removal of ffmpeg & OpenCV in favor of PyAV. Reduces Relics file size.
- Faster (13x) filesystem iteration collection for ingestion.
- Faster (4x) proxy + preview file generation LDR (jpg, png, tif).
- Faster (2-3x) proxy + preview file generation HDR (exr, hdr).

### **Small** New Features :
- User Preferences editor. 
- Choose whether to copy or move files on ingest.
- Ingests completion triggers a windows notification.
- Drag and drop files to begin ingesting them.

#### **Minor** Changes & Tweaks :
- Converted python scripts into Executables via PyInstaller.
- Status indicators.
- UI Indication of Admin mode when enabled.
- References icon changed to better represent the category purpose and color.
- Batch update selected assets across multiple categories.
- Trigger visual udpate for subcategory counters after deletion of asset.

### **Bug Fixes** :
1. Fix session stall isses when rapidly changing subcategory selections.
2. prevent drag & drop for same-selection assets.
3. Fix tag and user count updating / clearing.
    #### **Plugins** :
    1. Undo changes to file paths after export (both cases of success or failure)
    2. Sanitize spaces and unsupported special characters in file path sources.
    3. (Nuke) Converts any reformat knobs from the dynamic "**root.format**" to a static "**root(asset)**".
    4. (Nuke) Export ignores viewer nodes and removes then if contained inside a group.
    5. (Nuke) Export pre-converts all gizmos to groups.


### Development notes :
Needs backend SQL command run: `UPDATE Subcategory SET "Count"=0 WHERE "Count" ISNULL;`
