import os
import contextlib

from . import style
from .. import io
from .tree import TreeModel, Node
from .proxy import RecursiveSortFilterProxyModel
from .deselectabletreeview import DeselectableTreeView
from ..vendor import qtawesome as qta
from ..vendor.Qt import QtWidgets, QtCore, QtGui

import logging
log = logging.getLogger(__name__)


def _iter_model_rows(model,
                     column,
                     include_root=False):
    """Iterate over all row indices in a model."""
    indices = [QtCore.QModelIndex()]  # start iteration at root

    for index in indices:

        # Add children to the iterations
        child_rows = model.rowCount(index)
        for child_row in range(child_rows):
            child_index = model.index(child_row, column, index)
            indices.append(child_index)

        if not include_root and not index.isValid():
            continue

        yield index


@contextlib.contextmanager
def preserve_expanded_rows(tree_view,
                           column=0,
                           role=QtCore.Qt.DisplayRole):
    """Preserves expanded row in QTreeView by column's data role.

    This function is created to maintain the expand vs collapse status of
    the model items. When refresh is triggered the items which are expanded
    will stay expanded and vise versa.

    :param tree_view: the tree view which is nested in the application
    :type tree_view: QWidgets.QTreeView

    :param column: the column to retrieve the data from
    :type column: int

    :param role: the role which dictates what will be returned
    :type role: int

    :return: None
    """
    model = tree_view.model()

    expanded = set()

    for index in _iter_model_rows(model,
                                  column=column,
                                  include_root=False):
        if tree_view.isExpanded(index):
            value = index.data(role)
            expanded.add(value)

    try:
        yield
    finally:
        if not expanded:
            return

        for index in _iter_model_rows(model,
                                      column=column,
                                      include_root=False):
            value = index.data(role)
            state = value in expanded
            if state:
                tree_view.expand(index)
            else:
                tree_view.collapse(index)


@contextlib.contextmanager
def preserve_selection(tree_view,
                       column=0,
                       role=QtCore.Qt.DisplayRole,
                       current_index=True):
    """Preserves row selection in QTreeView by column's data role.

    This function is created to maintain the selection status of
    the model items. When refresh is triggered the items which are expanded
    will stay expanded and vise versa.

    :param tree_view: the tree view which is nested in the application
    :type tree_view: QWidgets.QTreeView

    :param column: the column to retrieve the data from
    :type column: int

    :param role: the role which dictates what will be returned
    :type role: int

    :return: None
    """

    model = tree_view.model()
    selection_model = tree_view.selectionModel()
    flags = selection_model.Select | selection_model.Rows

    if current_index:
        current_index_value = tree_view.currentIndex().data(role)
    else:
        current_index_value = None

    selected_rows = selection_model.selectedRows()
    if not selected_rows:
        yield
        return

    selected = set(row.data(role) for row in selected_rows)
    try:
        yield
    finally:
        if not selected:
            return

        # Go through all indices, select the ones with similar data
        for index in _iter_model_rows(model,
                                      column=column,
                                      include_root=False):

            value = index.data(role)
            state = value in selected
            if state:
                selection_model.select(index, flags)

            if current_index_value and value == current_index_value:
                tree_view.setCurrentIndex(index)


def _list_project_silos():
    """List the silos from the project's configuration"""
    project = io.find_one({"type": "project"})
    silos = project['config'].get("silos", [])
    if not silos:
        log.warning("Project '%s' has no silos in configuration",
                    project['name'])

    return list(sorted(silos))


def _list_assets(silo):
    """Get all assets for the active project in a specific silo."""
    return io.find({"type": "asset", "silo": silo})


class AssetModel(TreeModel):
    """The Items in the pipeline

    This will list "Folders" and "Items" up to a maximum depth as a tree-based
    data model.

    """

    COLUMNS = ["label", "tags", "deprecated"]
    Name = 0
    Deprecated = 2
    ObjectId = 3

    ObjectIdRole = QtCore.Qt.UserRole + 1

    def __init__(self, silo=None, parent=None):
        super(AssetModel, self).__init__(parent=parent)

        self._silo = None

        if silo is not None:
            self.set_silo(silo, refresh=True)

    def set_silo(self, silo, refresh=True):
        """Set the root path to the ItemType root."""
        self._silo = silo
        if refresh:
            self.refresh()

    def _add_hierarchy(self, parent=None):

        if parent is None:
            parent_id = io.find_one({"type": "project"})["_id"]
        else:
            # Assume the parent is a Node that houses the assets'
            # id in the database in the `_id` key.
            parent_id = parent['_id']

        # Parent to root silo those that have the project itself
        # as parent
        assets = io.find({"type": "asset",
                          "silo": self._silo,
                          "parent": parent_id})

        for asset in assets:

            # get label from data, otherwise use name
            label = asset.get("data", {}).get("label", asset['name'])

            # store for the asset for optimization
            deprecated = "deprecated" in asset.get("tags", [])

            node = Node({
                "_id": asset['_id'],
                "name": asset["name"],
                "label": label,
                "type": asset['type'],
                "tags": ", ".join(asset.get("tags", [])),
                "deprecated": deprecated,
            })
            self.add_child(node, parent=parent)

            # Add asset's children recursively
            self._add_hierarchy(node)

    def refresh(self):
        """Retrieves the data for the model so it can show it"""

        self.clear()
        self.beginResetModel()
        self._add_hierarchy(parent=None)
        self.endResetModel()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):

        if role == QtCore.Qt.DecorationRole:        # icon

            column = index.column()
            node = index.internalPointer()
            if column == self.Name:

                # define color, including darker state
                # when the asset is deprecated
                color = style.default
                if node.get("deprecated", False):
                    color = QtGui.QColor(color).darker(250)

                # If it has children show a full folder
                if self.rowCount(index) > 0:
                    return qta.icon("fa.folder", color=color)
                else:
                    return qta.icon("fa.folder-o", color=color)

        if role == QtCore.Qt.ForegroundRole:        # font color

            node = index.internalPointer()
            if "deprecated" in node.get("tags", []):
                return QtGui.QColor(style.light).darker(250)

        if role == self.ObjectIdRole:
            node = index.internalPointer()
            return node.get("_id", None)

        return super(AssetModel, self).data(index, role)


class AssetView(DeselectableTreeView):
    """Item view.

    This implements a context menu.

    """
    def __init__(self):
        super(AssetView, self).__init__()
        self.setIndentation(15)
        #self.setHeaderHidden(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    #     self.customContextMenuRequested.connect(self.on_contextMenu)
    #
    # def on_contextMenu(self, point):
    #     """Context menu for the item hierarchy view"""
    #
    #     index = self.currentIndex()
    #     if not index or not index.isValid():
    #         return
    #
    #     path = get_data(index, AssetModel.FilePathRole)
    #     if not path or not os.path.exists(path):
    #         logger.error("Item path does not exist. This is a bug.")
    #         return
    #
    #     menu = QtWidgets.QMenu(self)
    #
    #     metadata = {"path": path}
    #     from cbra.actions.generic import ShowPathInExplorerAction
    #     from cbra.action import _to_action
    #
    #     action = _to_action(ShowPathInExplorerAction(),
    #                         metadata,
    #                         parent=menu)
    #
    #     menu.addAction(action)
    #
    #     # Start context menu
    #     globalPoint = self.mapToGlobal(point)
    #     menu.exec_(globalPoint)


class AssetWidget(QtWidgets.QWidget):
    """A Widget to display a tree of assets with filter

    To list the assets of the active project:
        >>> # widget = AssetWidget()
        >>> # widget.refresh()
        >>> # widget.show()

    """

    silo_changed = QtCore.Signal(str)    # on silo combobox change
    assets_refreshed = QtCore.Signal()   # on model refresh
    selection_changed = QtCore.Signal()  # on view selection change
    current_changed = QtCore.Signal()    # on view current index change

    def __init__(self, parent=None):
        super(AssetWidget, self).__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QtWidgets.QHBoxLayout()

        silo = QtWidgets.QComboBox()
        silo.setFixedHeight(28)
        silo.setStyleSheet("QComboBox {padding-left: 10px;}")
        font = QtGui.QFont()
        font.setBold(True)
        silo.setFont(font)

        icon = qta.icon("fa.refresh", color=style.light)
        refresh = QtWidgets.QPushButton(icon, "")
        refresh.setToolTip("Refresh items")

        header.addWidget(silo)
        header.addStretch(1)
        header.addWidget(refresh)

        # Tree View
        model = AssetModel()
        proxy = RecursiveSortFilterProxyModel()
        proxy.setSourceModel(model)
        proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        view = AssetView()
        view.setModel(proxy)

        filter = QtWidgets.QLineEdit()
        filter.textChanged.connect(proxy.setFilterFixedString)
        filter.setPlaceholderText("Filter")

        # Layout
        layout.addLayout(header)
        layout.addWidget(view)
        layout.addWidget(filter)

        # Signals/Slots
        selection = view.selectionModel()
        selection.selectionChanged.connect(self.selection_changed)
        selection.currentChanged.connect(self.current_changed)
        silo.currentIndexChanged.connect(self._on_silo_changed)
        silo.currentIndexChanged.connect(self._refresh_model)
        refresh.clicked.connect(self.refresh)

        self.refreshButton = refresh
        self.silo = silo
        self.model = model
        self.proxy = proxy
        self.view = view

    def _on_silo_changed(self, index):
        """Callback for silo combobox change"""

        self._refresh_model()
        silo = self.silo.itemText(index)
        self.silo_changed.emit(silo)
        self.selection_changed.emit()

    def _refresh_model(self):
        silo = self.silo.currentText()
        with preserve_expanded_rows(self.view,
                                    column=0,
                                    role=self.model.ObjectIdRole):
            with preserve_selection(self.view,
                                    column=0,
                                    role=self.model.ObjectIdRole):
                self.model.set_silo(silo)
                self.view.expandAll()

        self.assets_refreshed.emit()

    def refresh(self):

        current_silo = self.silo.currentText()

        # Populate the silo combobox without emitting signals
        self.silo.blockSignals(True)
        self.silo.clear()
        self.silo.addItems(_list_project_silos())
        self.set_silo(current_silo)
        self.silo.blockSignals(False)

        # Only emit a silo changed signal if the new signal
        # after refresh is not the same as prior to it (e.g.
        # when the silo was removed, or alike.)
        if current_silo != self.silo.currentText():
            self.silo.currentIndexChanged.emit(self.silo.currentIndex())

        self._refresh_model()

    def set_silo(self, silo):
        """Set the active silo by name or index.

        Args:
            silo (str or int): The silo name or index.
            emit (bool): Whether to emit the change signals

        """

        # Already set
        if silo == self.silo.currentText():
            return

        # Otherwise change the silo box to the name
        for i in range(self.silo.count()):
            text = self.silo.itemText(i)
            if text == silo:
                self.silo.setCurrentIndex(i)
                break

    def get_current_silo(self):
        return self.silo.currentText()

    def get_active_asset(self):
        """Get the object id in the database for the active asset"""
        current = self.view.currentIndex()
        return current.data(self.model.ObjectIdRole)

    def get_selected_assets(self):
        """Return the assets that are selected.
        
        """
        selection = self.view.selectionModel()
        rows = selection.selectedRows()
        return [row.data(self.model.ObjectIdRole) for row in rows]

    # def set_asset_selection(self, assets, expand=False):
    #     """Select the relative items.
    #
    #     Also expands the tree view when `expand=True`.
    #
    #     Args:
    #         assets (list): A list of asset names.
    #
    #     """
    #
    #     # TODO: Implement to select by unique asset "name"
    #     if not isinstance(assets, (list, tuple)):
    #         raise TypeError("Set items takes a list of items to set")
    #
    #     selection_model = self.view.selectionModel()
    #     selection_model.clearSelection()
    #     mode = selection_model.Select | selection_model.Rows
    #
    #     for asset in assets:
    #
    #         index = self.model.find_index(asset)
    #         if not index or not index.isValid():
    #             continue
    #
    #         index = self.proxy.mapFromSource(index)
    #         selection_model.select(index, mode)
    #
    #         if expand:
    #             # TODO: Implement expanding to the item
    #             pass
    #
    #     self.selection_changed.emit()
