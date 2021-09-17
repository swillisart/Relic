=========================================
Management
=========================================


Ingest
--------

Filesystem 
~~~~~~~~~~~~
    .. note:: For existing 3D assets you have to open them individually to clean them up and export into the library from within the native application.
        See: :ref:`application-rl`

    Ingesting from the filesystem is the ideal method for existing elements:
        #. Start by selecting the category to ingest into.
        #. Drag the root folder that contains the element(s) into the library backdrop.
        #. Select the ingest filter type. (Different File types should go into thier respective categories) 
        #. Optional: Check Categorize by parent folder if they are already organized by folder structure.
        #. All Done! The previews and proxies will generate in the backround and depending on the length / size of the element(s) may take some time. 
    
        * **Review Step Demonstration**

        .. image:: FilesystemIngest1.gif
            :width: 1200


    Next up:
        :ref:`organize-rl`

.. _application-rl:

Application
~~~~~~~~~~~~

    Export Assets / Elements from DCC applcation 

    .. image:: dragapp.gif
        :width: 1200

    *  Launching / Configuring:
        To get the library into your application just simply **Middle-Click** drag the title bar into the desired application.

    *  Clean up the scene:
        Make sure only the intended files / sources are kept in the scene.
        If image-planes or unnecessary file textures are included the asset size will be larger and take longer to create and even more so to retrieve every time.
        (Consider resizing some into proxies for illustration purposes)
        
        .. tip:: The larger inefficient assets are less likely to be used
            and more likely a moderator will remove it and tell you to re-do it all over agin. 

    * Export:
        #. To export give a name.
        #. Write a thourough description. (Specifiying a Class is optional.)
        #. Set a Class. (Set as Model to export an additonal 3d Preview for the viewer.)
        #. Finally Select the category from the tree on the left. (For maya use Modeling or for FX Elements)

    .. image:: exportiwindow.png
        :width: 1200

.. _organize-rl:

Organization
-------------

To start organizing you need to enable Management mode.
    .. image:: managementmode.jpg
        :width: 300

    .. note:: This is for permission management and to ensure assets aren't accidentally moved when not in management mode (edit mode).

Organize Assets     
~~~~~~~~~~~~~~~~~~~~~~~~
    Organization of assets is simply **middle-click** dragging and dropping from the asset icon view into the Sub-Category tree.
    
    .. warning:: You cannot drag between two separate main categories. You will need to delete and re-ingest.

    .. note:: The files on disk are moved when an item is dropped so ensure the destination is correct.

    .. image:: organization1.gif
        :width: 400



Organize Sub-Categories
~~~~~~~~~~~~~~~~~~~~~~~~~
    *  Create or Remove:
        To create or remove **right-click** an item in the tree view and select an option. (A popup will appear to let you input a name if creating a new subcategory). 

        .. image:: newcategory.gif
            :width: 300

    *  Restructure:
        To Move a Sub-Category in the tree **middle-click** drag and drop. 

        .. tip:: Synchronize the Sub-Category counts to refresh the numbered counters in the tree.

        .. image:: restructurecategory.gif
            :width: 400

    .. note:: Sub-categories must have unique names.

