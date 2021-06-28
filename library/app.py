import ctypes
import math
import os
import sys
from functools import partial
# -- Third-party --
from PySide6.QtCore import Slot, QPoint, QModelIndex
from PySide6.QtGui import QFontDatabase, QFont, QIcon, QColor, Qt, QTextDocument, QTextCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon,
    QMenu, QWidget, QSizePolicy,QFrame, QGraphicsDropShadowEffect, QLabel, QTextBrowser)

# -- First-party --
from sequencePath import sequencePath as Path

# -- Module --
from library.ui.dialog import Ui_RelicMainWindow
from library.config import relic_preferences, kohaiPreview
from library.objectmodels import Library, db, polymorphicItem
from library.widgets.assets import assetItemModel, assetListView
from library.widgets.subcategoriesViews import ExpandableTab, CategoryManager
from library.widgets.metadataView import metadataFormView
from library.widgets.relationshipView import LinkViewWidget
from library.widgets.util import DialogOverlay
from library.widgets.ingest import IngestForm


raw_md = """
Historical background and objectives
================================================================================

Historical background and objectives

Closure mixture representation  
--------------------------------------------------------------------------------
----
Component              | Closure         | Description
-----------------------|-----------------|-----------------------------------
Transparency           | `transparency`  | simple pass-through (can be thought of as a delta BTDF)
Coating                | `specular_brdf` | dielectric microfacet BRDF (GGX)
Emission               | `emission`      | diffuse emission
Metal                  | `metal_brdf`    | conductor microfacet BRDF (GGX)
Specular reflection    | `specular_brdf` | dielectric microfacet BRDF (GGX)
Specular transmission* | `specular_btdf` | dielectric microfacet BTDF (GGX)
Sheen*                 | `sheen_brdf`    | retro-reflective dielectric microfacet BRDF [#Estevez2017]
Subsurface scattering* | `subsurface`    | subsurface scattering (e.g. diffusion or random-walk)
Diffuse transmission*  | `diffuse_btdf`  | diffuse microfacet BTDF (Oren-Nayar)
Diffuse reflection     | `diffuse_brdf`  | diffuse microfacet BRDF (Oren-Nayar)
Sean buddy     | did something cool  | 1. aaaaaa  

` `

Coating
--------------------------------------------------------------------------------
----
The topmost scattering layer is a dielectric coating with a GGX microfacet BRDF closure `coat_brdf`. As a dielectric, this BRDF is not energy preserving (i.e. its directional reflectance is generally less than one) as it obeys Fresnel reflection laws. The layer is assumed to be infinitely thin, and the remaining non-reflected light is passed directly to the underlying layer without refraction. The reflection color is fixed to white, though the coat medium color can be user controlled.

` `

The closure combination formula is
---------------------------------------
----

| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |

> 1. This is a complete item
> 2.  fun
> 3.  dead


- [x] @mentions, #refs, [links](), **formatting**, and <del>tags</del> supported
- [x] list syntax required (any unordered or ordered list supported)
- [x] this is a complete item
- [ ] this is an incomplete item
- [ ]  gross

###### This is a tiny tag


_6/18/2021 1:14 AM_
--------------------------------------------------------------------------------

Task     | Description
---------|-----------------------------------
Completed stupid stuff which you have no idea about   | simple pass-through  of my not gaead dkajljsdfkljdkla fsdkjfkldasjfk ldasjfklasj;ldfkjas dklfjasdfkj dddlasjf;jsfkldsf jadklsfj  dsflasdkjf ldjasfkldjasfkldj asfkljasdf kljlasdfjkld asflkjas dflkjasdklf jasldfjd sfklasjdlfkja sdklfjdasfklas djflkja sdflkjasdf  sdjlafjdsa kl asdkl jkasdfkjads ladskfj asjkdf

` `

Reciprocity
--------------------------------------------------------------------------------

A physically correct BSDF must satisfy reciprocity (i.e. symmetry under exchange of the incoming and outgoing directions). However, in our proposed model, even if the leaf-level BSDFs are reciprocal, the closure combination is *not*. This is due to the introduction of the `reflectance(...)` function which depends on the incoming direction only. This may present a problem if the shading model were to be incorporated in certain light transport algorithms, such as bidirectional path tracing, which typically rely on this property to hold.

However, enforcing reciprocity would be likely to significantly complicate the mathematical form of our model, without producing a qualitatively better visual appearance. For many renderers, including Arnold -- a unidirectional path tracer, the physical constraint of reciprocity can be violated, even in the leaf BSDFs, without causing any real problems. Furthermore, enforcing reciprocity of a layered material in a truly physically correct manner [#Jakob2014] is currently too complicated and cumbersome to implement in a production renderer. Models in actual production use that achieve reciprocity, such as the coating scheme of Kulla and Estevez [#Kulla2017], do so by introducing drastic approximations with inaccuracy likely similar to the non-reciprocal approach described here.

Therefore, for the time being we do not consider the incorporation of reciprocity in our model to be a strict necessity.

` `

Layering model
--------------------------------------------------------------------------------

Our layering model ensures energy conservation by construction, and attempts also to ensure energy preservation where possible. However, as a relatively simple model which is simply a linear combination of closures with weights adjusted according to an approximate `reflectance(...)` function, it is not a physically accurate simulation of the light transport in the layers that we describe.

A number of more accurate treatments of the full light transport in layered media have appeared recently [#Jakob2014] [#Belcour2018] [#Zeltner2018]. These models incorporate the effect of the various modes of reflection and transmission through the whole stack of layers, which generates a final BSDF (or in general BSSRDF) which is not a simple linear combination of the per-layer BSDFs. 

In future, we would like to investigate transitioning to a more accurate model such as this. However, currently it seems all the available models are more expensive to compute and much more complex to implement. 

We attempt at least in our model to incorporate some of the most important effects which arise due to the inter-layer interaction by hand. For example, we allow the roughness of the coating to affect the roughness of (some of) the underlying layers. 

` `

Surface orientation
--------------------------------------------------------------------------------

In transmissive situations, light may be incident from above or below the surface normal. The transmission layer is sensitive to this and ensures that light correctly refracts through the interface. However, the other layers are oriented w.r.t. the *facing* normal, so the scattering behavior is the same when objects are hit from outside and from inside. This again is a non-physical approximation, which is useful in practice as it simplifies the logic without introducing obvious visual artifacts.

"""

CATEGORIES = []

class RelicMainWindow(Ui_RelicMainWindow, QMainWindow):
    def __init__(self, *args, **kwargs):
        super(RelicMainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.app_icon = QIcon(':/resources/icons/app_icon.svg')
        self.tray = QSystemTrayIcon(self.app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()
        #self.tray.showMessage('Relic', 'Relic is now running...', self.app_icon, 2)
        # Assign the dock's title bar to search widget 
        # then set the dock's widget to an empty widget so separators disappear
        empty_widget = QWidget(self)
        empty_widget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self.searchDock.setTitleBarWidget(self.searchDock.widget())
        self.searchDock.setWidget(empty_widget)
        self.resizeDocks([self.searchDock], [0], Qt.Horizontal) # (QTBUG-65592) fixes dock resize
        self.library = Library()
        self.category_manager = CategoryManager(self)
        self.category_manager.onSelection.connect(self.updateAssetView)
        self.searchBox.returnPressed.connect(self.updateAssetView)
        self.pageSpinBox.valueChanged.connect(self.updateAssetView)

        category_widgets = self.category_manager.assembleCategories(self.library.categories)
        for index, category in enumerate(category_widgets):
            category.verticalControl.hide()
            self.categoryLayout.insertWidget(index, category)

        self.categoryDock.setTitleBarWidget(self.dockTitleFrame)
        self.attributeDock.setTitleBarWidget(self.attributeDockTitle)
        self.linksDock.setTitleBarWidget(self.linkDockTitle)
        self.linksDock.hide()

        # Shadow graphics
        shadow = QGraphicsDropShadowEffect(self, blurRadius=6.0,
                color=QColor(31, 31, 31), offset=QPoint(0, 0))
        self.categoryDock.setGraphicsEffect(shadow)
        shadow = QGraphicsDropShadowEffect(self, blurRadius=8.0,
                color=QColor(31, 31, 31), offset=QPoint(1, 1))
        self.attributeDock.setGraphicsEffect(shadow)
        shadow = QGraphicsDropShadowEffect(self, blurRadius=8.0,
                color=QColor(31, 31, 31), offset=QPoint(0, 0))
        self.linksDock.setGraphicsEffect(shadow)
        self.attributeDock.setAutoFillBackground(True)
        self.categoryDock.setAutoFillBackground(True)
        self.linksDock.setAutoFillBackground(True)


        # Creates asset view
        self.assets_view = assetListView(self)
        self.asset_item_model = assetItemModel(self.assets_view)
        self.centralwidget.layout().insertWidget(2, self.assets_view)

        self.links_view = LinkViewWidget(self)
        self.metatdata_view = metadataFormView(self)
        self.attributeDock.setWidget(self.metatdata_view)
        self.linksDock.setWidget(self.links_view)

        # Signals / Slots
        self.filterBox.textChanged.connect(self.category_manager.filterAll)
        self.linkFilterBox.textChanged.connect(self.links_view.filterAll)
        self.actionPortal.toggled.connect(self.hideDocks)
        self.actionIngest.triggered.connect(self.beginIngest)
        self.actionDocumentation.triggered.connect(self.showDocumentation)
        self.attrExpandButton.toggled.connect(self.attributeDock.widget().setVisible)
        self.categoryExpandButton.toggled.connect(self.categoryDock.widget().setVisible)
        self.assets_view.selmod.selectionChanged.connect(self.loadAssetData)
        self.assets_view.onLinkLoad.connect(self.loadLinkData)
        self.backButton.clicked.connect(self.assetViewing)
        self.documentationFilterBox.textChanged.connect(self.searchPage)
        self.documentationFilterBox.returnPressed.connect(self.findNextInPage)


        db.accessor.imageStreamData.connect(self.updateIcons)
        self.actionAdministration_Mode.setChecked(int(relic_preferences.edit_mode))

        self.documentationDock.setTitleBarWidget(self.documentationDockTitle)
        self.documentationDock.hide()
        self.documentationDock.setAutoFillBackground(True)

    @Slot()
    def showDocumentation(self):
        self.documentationTextBrowser.setMarkdown(raw_md)
        wat = DialogOverlay(self, self.documentationDock)

    @Slot()
    def searchPage(self, text):
        textCursor = self.documentationTextBrowser.textCursor()
        textCursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor, 1)
        self.documentationTextBrowser.setTextCursor(textCursor)
        self.documentationTextBrowser.find(text)

    @Slot()
    def findNextInPage(self):
        self.documentationTextBrowser.find(self.documentationFilterBox.text())

    @Slot()
    def beginIngest(self):
        ingest = IngestForm()
        #ingest.baaaaaaa.connect(self.doit)
        self.verticalSpacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum) 
        ingest.setCategoryView(self.categoryDock, self.categoryLayout)
        ingest.beforeClose.connect(self.onIngestClosed)
        self.category_manager.blockSignals(True)
        DialogOverlay(self, ingest, modal=False)


    @Slot()
    def onIngestClosed(self, dock):
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.category_manager.blockSignals(False)
        self.verticalSpacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding) 


    def hideDocks(self, state):
        self.categoryExpandButton.setChecked(state)
        self.attrExpandButton.setChecked(state)

    @Slot()
    def updateIcons(self, data):
        img, id = data
        models = [self.links_view.model, self.assets_view.model]
        for model in models:
            for i in range(model.rowCount()):
                index = model.index(i, 0)
                item = model.itemFromIndex(index)
                if item.id == id:
                    item.icon = img
                    item.emitDataChanged()

    @Slot()
    def assetViewing(self):
        self.links_view.clear()
        self.linksDock.hide()
        self.assets_view.show()

    @Slot()
    def updateAssetView(self, obj=None):
        sender = self.sender()
        if isinstance(obj, dict):
            categories = obj.copy()
        else:
            categories = self.category_manager.selected_subcategories.copy()

        # Only re-query the database if the searchbox has changed
        new_search = False
        limit = int(relic_preferences.assets_per_page)

        # Split text into list of search term keywords
        text = self.searchBox.text()
        terms = text.split(' ') if text else None
        new_search = self.library.search(terms, categories)
        asset_total = len(self.library.assets)
            
        self.assets_view.clear()

        if new_search or sender not in [self.searchBox, self.category_manager]:
            page = self.pageSpinBox.value()

            for item in self.library.load(page, limit, categories):
                self.assets_view.addItem(item)
            asset_total = len(self.library.assets_filtered)

            self.assets_view.scrollTo(self.assets_view.model.index(0, 0, QModelIndex()))
        page_count = math.ceil(asset_total / limit) or 1
        self.pageSpinBox.setSuffix('/' + str(page_count))
        self.pageSpinBox.setMaximum(page_count)
        msg = 'Search results: {} Assets...'.format(asset_total)
        self.statusbar.showMessage(msg)

    @Slot()
    def loadAssetData(self, selection):
        sender = self.sender()
        indexes = selection.indexes()

        if indexes:
            asset = indexes[0].data(polymorphicItem.Object)
            asset.related(noassets=True)
            self.metatdata_view.loadAsset(asset)
            if self.previewCheckBox.isChecked():
                path = str(asset.local_path)
                kohaiPreview(path)

    @Slot()
    def loadLinkData(self, index):
        """Load related assets via links from relationships.

        Parameters
        ----------
        index : QModelIndex
            the index which this slot connects to
        """

        self.assets_view.hide()
        self.linksDock.show()

        indices = set(self.assets_view.selectedIndexes())
        indices.add(index)

        for index in indices:
            asset = index.data(polymorphicItem.Object)
            asset.related()
            self.links_view.updateGroups(asset.upstream)

    @Slot()
    def toggleVisibility(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.grab()
            self.setVisible(not self.isVisible())
            self.activateWindow()
            self.raise_()

    @Slot()
    def toggleAdminMode(self, toggle):
        #TODO: query the databse for permissions level
        relic_preferences.edit_mode = int(toggle)


def main(args):
    app = qApp or QApplication(sys.argv)
    ctypes.windll.kernel32.SetConsoleTitleW("Relic")
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.relic")
    window = RelicMainWindow()
    window.resize(1500, 925)
    window.show()
    sys.exit(app.exec_())
