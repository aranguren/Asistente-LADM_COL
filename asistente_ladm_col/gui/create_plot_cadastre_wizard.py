# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              Asistente LADM_COL
                             --------------------
        begin                : 2017-12-09
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF Swissphoto)
        email                : gcarrillo@linuxmail.org
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import (QCoreApplication,
                              QSettings)
from qgis.PyQt.QtWidgets import QWizard
from qgis.core import (QgsMapLayerProxyModel,
                       QgsWkbTypes,
                       Qgis)

from ..config.help_strings import HelpStrings
from ..config.general_config import FIELD_MAPPING_PATH
from ..config.table_mapping_config import PLOT_TABLE
from ..utils import get_ui_class

WIZARD_UI = get_ui_class('wiz_create_plot_cadastre.ui')

class CreatePlotCadastreWizard(QWizard, WIZARD_UI):
    def __init__(self, iface, db, qgis_utils, parent=None):
        QWizard.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self._plot_layer = None
        self._db = db
        self.qgis_utils = qgis_utils
        self.help_strings = HelpStrings()

        self.restore_settings()

        self.rad_plot_from_boundaries.toggled.connect(self.adjust_page_1_controls)
        self.rad_plot_from_boundaries.toggled.emit(True)
        self.button(QWizard.FinishButton).clicked.connect(self.finished_dialog)
        self.button(QWizard.HelpButton).clicked.connect(self.show_help)

        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)

    def adjust_page_1_controls(self):
        self.cbo_mapping.clear()
        self.cbo_mapping.addItem("")
        self.cbo_mapping.addItems(self.qgis_utils.get_field_mappings_file_names(PLOT_TABLE))

        if self.rad_refactor.isChecked():
            self.lbl_refactor_source.setEnabled(True)
            self.mMapLayerComboBox.setEnabled(True)
            self.lbl_field_mapping.setEnabled(True)
            self.cbo_mapping.setEnabled(True)
            finish_button_text = QCoreApplication.translate("CreatePlotCadastreWizard", "Import")
            self.txt_help_page_1.setHtml(self.help_strings.get_refactor_help_string(PLOT_TABLE, True))

        elif self.rad_plot_from_boundaries.isChecked():
            self.lbl_refactor_source.setEnabled(False)
            self.mMapLayerComboBox.setEnabled(False)
            self.lbl_field_mapping.setEnabled(False)
            self.cbo_mapping.setEnabled(False)
            finish_button_text = QCoreApplication.translate("CreatePlotCadastreWizard", "Finish")
            self.txt_help_page_1.setHtml(self.help_strings.WIZ_CREATE_PLOT_CADASTRE_PAGE_1_OPTION_BOUNDARIES)

        self.wizardPage1.setButtonText(QWizard.FinishButton,
                                       QCoreApplication.translate("CreatePlotCadastreWizard",
                                       finish_button_text))

    def finished_dialog(self):
        self.save_settings()

        if self.rad_refactor.isChecked():
            if self.mMapLayerComboBox.currentLayer() is not None:
                field_mapping = self.cbo_mapping.currentText()
                res_etl_model = self.qgis_utils.show_etl_model(self._db,
                                                               self.mMapLayerComboBox.currentLayer(),
                                                               PLOT_TABLE,
                                                               QgsWkbTypes.PolygonGeometry,
                                                               field_mapping)

                if res_etl_model:
                    if field_mapping:
                        self.qgis_utils.delete_old_field_mapping(field_mapping)

                    self.qgis_utils.save_field_mapping(PLOT_TABLE)
            else:
                self.iface.messageBar().pushMessage("Asistente LADM_COL",
                    QCoreApplication.translate("CreatePlotCadastreWizard",
                                               "Select a source layer to set the field mapping to '{}'.").format(PLOT_TABLE),
                    Qgis.Warning)

        elif self.rad_plot_from_boundaries.isChecked():
            self.qgis_utils.polygonize_boundaries(self._db)

    def save_settings(self):
        settings = QSettings()
        settings.setValue('Asistente-LADM_COL/wizards/plot_load_data_type', 'from_boundaries' if self.rad_plot_from_boundaries.isChecked() else 'refactor')

    def restore_settings(self):
        settings = QSettings()

        load_data_type = settings.value('Asistente-LADM_COL/wizards/plot_load_data_type') or 'from_boundaries'
        if load_data_type == 'refactor':
            self.rad_refactor.setChecked(True)
        else:
            self.rad_plot_from_boundaries.setChecked(True)

    def show_help(self):
        self.qgis_utils.show_help("create_plot")
