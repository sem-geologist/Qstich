#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

import sys
import os
from PyQt4 import QtCore, QtGui
from ui.Ui_exterminator import Ui_MainWindow
from ui.Ui_finalize import Ui_FinalImage
from ui.Ui_export_to_hdf5 import Ui_ExportHdf5
from etc import changelog
from lxml import objectify
import codecs
import numpy as np
#import time
#from pyqtgraph.flowchart import Flowchart, Node
#import pyqtgraph.flowchart.library as fclib
#from pyqtgraph.flowchart.library.common import CtrlNode
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter
import re
import tifffile as tf
from scipy import misc
#from memory_profiler import profile
from copy import deepcopy
import cv2

version = '0.1-beta'

#starttime = time.time()

#background colors used in lists in gui:
col_good = QtGui.QBrush(QtGui.QColor(185, 255, 155))
col_good.setStyle(QtCore.Qt.SolidPattern)
col_not_so_good = QtGui.QBrush(QtGui.QColor(255, 255, 140))
col_not_so_good.setStyle(QtCore.Qt.SolidPattern)
col_bad = QtGui.QBrush(QtGui.QColor(255, 180, 155))
col_bad.setStyle(QtCore.Qt.SolidPattern)
pen_tile = QtGui.QPen(QtGui.QColor(100, 200, 100))
brush_tile = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
pen_selection = QtGui.QPen(QtGui.QColor(100, 200, 100))
brush_selection = QtGui.QBrush(QtGui.QColor(255, 255, 150, 175))
pen_hover = QtGui.QPen(QtGui.QColor(255, 255, 255))

#bellow could be in class, but it is working faster as separate dictionaries
mapping_list = {}  # initiate global dictionary of tile files
final_list = {}  # initiate global dictionary of finalization tree
xstage = {}        # dict of global x coordinate of the stage
ystage = {}        # dict of global y -//-
image_size = {}
max_tiles = {}
tile_index = {}
pts = {}           # tile selected in vector overview of samples
stitchy = {}       # 3x3 tile selection of samples
filter_parameter_list = {}
base_image = {}  # detector type used as image in stitching (i.e.  BSE images)

#####################
#helper functions:
#####################


def image2numpy(filename):
    if filename.rsplit('.', 1)[-1] == 'txt':
        data = np.loadtxt(filename, delimiter=';', dtype='float32')
    else:
        data = misc.imread(filename)
        # in case of signal beeing more than 8 bit decrease the
        # bit depth to 32bit(float) else to unsigned 8bit:
    if data.max() <= 255:
        data = data.astype(np.uint8)
    return data


def waiting_effects(function):
    def new_function(self):
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(
                                                         QtCore.Qt.WaitCursor))
        function(self)
        QtGui.QApplication.restoreOverrideCursor()
    return new_function


def cos_(angle):
    return np.cos(angle * np.pi / 180)


def sin_(angle):
    return np.sin(angle * np.pi / 180)


def fill_mapping_dict(directory):
    global mapping_list
    """ function pupulates global dictionary of mapping tiles,
    function returns sum of counted apropriate files.
    Function requires these arguiments:
    Args:
        directory -- where to search files
    function uses standard python methods in splitting and finiding
    the basic metadata saved in file names or
    (TO_BE_DEVELOPED) in tags of TIFF """
    z = 0
    re_sample = re.compile('[\s](?=\(\d)')
    re_signal = re.compile('(?<=\d\))[_]')
    for i in next(os.walk(directory))[2]:
        header, ft = i.rsplit('.', 1)
        if np.shape(re.findall(r'\(\d+\,\d+\)', i))[0] == 1 and ft != 'bcf':
            z += 1
            j = re_sample.split(header)[0]
            #j = i.rsplit(" ", 1)[0]
            #k, ft = i.rsplit("_", 1)[1].rsplit(".", 1)
            #l = i.rsplit("_", 1)[0]
            l, k = re_signal.split(header)
            if j in mapping_list:
                if k in mapping_list[j]:
                    mapping_list[j][k][l] = directory + "/" + i
                else:
                    mapping_list[j][k] = {l: directory + "/" + i}
                    final_list[j][k] = {}
            else:
                mapping_list[j] = {k: {l: directory + "/" + i}}
                final_list[j] = {k: {}}
        elif np.shape(re.findall(r'\(\d+\,\d+\)', i))[0] == 2 and\
                                                  i.rsplit('.', 1)[1] != 'txt':
            z += 1
            smpl = i.split(" ")[0]
            tile = ' '.join([smpl, i.rsplit(" ", 1)[-1].split('_')[0]])
            data_type = i.rsplit(" ", 1)[1].split('_')[1].split('.')[0]
            if smpl in mapping_list:
                if data_type in mapping_list[smpl]:
                    mapping_list[smpl][data_type][tile] = directory + "/" + i
                else:
                    mapping_list[smpl][data_type] = {tile: directory + "/" + i}
                    final_list[smpl][data_type] = {}
            else:
                mapping_list[smpl] = {data_type: {tile: directory + "/" + i}}
                final_list[smpl] = {data_type: {}}

    return z


def fill_tile_index():
    """function which fills tile_index
    requires one arguement: dictionary with filenames"""
    global tile_index
    for i in mapping_list:
        for j in list(mapping_list[i][base_image[i]].keys()):  # eddited
            k = j.rsplit("(", 1)[1].strip(')').split(",")
            if i in tile_index:
                tile_index[i][j] = {'x': int(k[1]), 'y': int(k[0])}
            else:
                tile_index[i] = {j: {'x': int(k[1]), 'y': int(k[0])}}


#idea is good, but it doesn't work...:
# why?
#def cleanXML(xml):
    #roman = ['nulla', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']
    #for i in range(9):
        #xml = xml.replace(''.join(['<', str(i)]), ''.join(['<', roman[i]]))
        #xml = xml.replace(''.join(["<\", str(i)]), ''.join(["<\\", roman[i]]))

    #return xml


def parseXML(xmlFile):
    """ parse the broken bruker xml (.rtj) into python objects"""
    with codecs.open(xmlFile, encoding='cp1252') as f:
        next(f)  # skip the xml header
        #####################################################################
        #Why skiping? because Bruker are not using and will not use Unicode
        # in near future.
        # Additionally Bruker xmls are always broken:
        #tags contain or begin with forbiden charts.
        # So instead of directly opening
        # the xml with lxml.objectify, the file is opened in python as text
        # file, and then cleaned up (invalide tags, replaced with something
        # legal)
        ####################################################################
        xml = f.read()
        #xml = codecs.encode(xml, 'utf-8')
        #xml = xml.replace("WINDOWS-1252", "UTF-8")
        xml = xml.replace(":x", "x")  # clean da bruker shit up
        xml = xml.replace(":y", "y")  # clean da bruker shit up
        xml = xml.replace("2ndTier", "IIndTier")  # clean da bruker shit up
        #xml = cleanXML(xml) #  there would come handy function....
        #re.sub("<.?[0-9]",'</nr',xml)

    return objectify.fromstring(xml)


def imageSize():
    global image_size
    for sample in mapping_list:
        for i in mapping_list[sample]:
            for j in mapping_list[sample][i]:
                if mapping_list[sample][i][j].rsplit('.', 1)[-1] == 'txt':
                    tile = np.loadtxt(mapping_list[sample][i][j], delimiter=';')
                else:
                    tile = misc.imread(mapping_list[sample][i][j])
                break
            break
        image_size[sample] = np.shape(tile)

    return image_size


def filterImage(img, fltr, *args):
    if fltr == 'blur':
        out_img = cv2.blur(img, (args[0], args[0]))
    elif fltr == 'median':
        out_img = cv2.medianBlur(img, *args)
    elif fltr == 'gaussian':
        out_img = cv2.GaussianBlur(img, (args[0], args[0]), args[1])
    elif fltr == 'bilateral':
        out_img = cv2.bilateralFilter(img, *args)

    return out_img


def tile_name(sample, x, y):
    return sample + ' (' + str(y) + ',' + str(x) + ')'


def stitching_list(sample, tile):
    global stitchy
    stitchy[sample] = []
    x = tile_index[sample][tile]['x']
    y = tile_index[sample][tile]['y']
    for n in (x - 1, x, x + 1):
        for m in (y - 1, y, y + 1):
            stitchy[sample].append(tile_name(sample, n, m))


def maxTileNumberBr():
    """returns value of x and y tiles of mosaic
    requires dictionary with filenames per tile if data files
    have organized tile position in the file name:
    ''sample detector/element_line (y,x) tiles'"""
    global max_tiles
    for h in mapping_list:
        max_tiles[h] = {}
        a = []
        for j in mapping_list[h][base_image[h]]:
            a.append(j.rsplit(" ", 1)[1].strip("(").strip(")").split(","))
        x = []
        y = []
        for k in a:
            x.append(int(k[1]))
            y.append(int(k[0]))
        maxx = max(x)
        maxy = max(y)
        max_tiles[h]['maxx'] = maxx
        max_tiles[h]['maxy'] = maxy
    return max_tiles


class selectableRect(QtGui.QGraphicsRectItem):
    def __init__(self, name, *args):
        QtGui.QGraphicsRectItem.__init__(self, *args)
        self.setAcceptHoverEvents(True)
        self.name = name

    def hoverEnterEvent(self, ev):
        self.savedPen = self.pen()
        self.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
        ev.ignore()

    def hoverLeaveEvent(self, ev):
        self.setPen(self.savedPen)
        ev.ignore()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            ev.accept()
            myapp.reset_tile_graph_color()
            self.setBrush(QtGui.QBrush(brush_selection))
            sample = self.name.split()[0]
            pts[sample] = self.name
            stitching_list(sample, self.name)
            myapp.populate_img_dict(sample)
            try:
                if myapp.ui.stitchWidget.isVisible():
                    myapp.tweeke.vb.clear()
                    for i in myapp.img[sample]:
                        myapp.tweeke.vb.addItem(myapp.img[sample][i])
                    myapp.tweeke.vb.autoRange()
                if myapp.ui.filterDockWidget.isVisible():
                    myapp.set_filter_images()
            except:
                pass
        else:
            ev.ignore()


class BSEMissing(QtGui.QDialog):
    def __init__(self, sample, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Huston. We have a problem...')
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(
            'No image from chosen folder have the "BSE", "AsB" or "BEI" part '
            'in the filename. Please chose from list detector/element to be '
            'the base image (image showed while tweeking stitching parameters)')
        self.label.setWordWrap(True)
        self.verticalLayout.addWidget(self.label)
        self.listView = QtGui.QListView()
        self.verticalLayout.addWidget(self.listView)
        self.model = QtGui.QStringListModel(list(final_list[sample].keys()))
        self.listView.setModel(self.model)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.setEnabled(False)
        self.listView.clicked.connect(self.enableTheButton)
        self.buttonBox.accepted.connect(self.accept)

    def enableTheButton(self):
        self.buttonBox.setEnabled(True)
        self.listView.clicked.disconnect(self.enableTheButton)

    def returnSample(self):
        return self.model.itemData(self.listView.selectedIndexes()[0])[0]


class AboutDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("About")
        self.resize(600, 450)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        #self.dalek = QtGui.QLabel(parent=self)
        #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,
                                       #QtGui.QSizePolicy.MinimumExpanding)
        #sizePolicy.setHorizontalStretch(1)
        #sizePolicy.setVerticalStretch(1)
        #self.dalek.setSizePolicy(sizePolicy)
        #self.dalek.setMinimumSize(QtCore.QSize(140, 50))
        #self.dalek.setBaseSize(QtCore.QSize(140, 50))
        #self.dalek.setPixmap(QtGui.QPixmap('dalek.png'))
        #self.dalek.setScaledContents(True)
        #self.verticalLayout.addWidget(self.dalek)
        self.textBrowser = QtGui.QTextBrowser(self)
        self.verticalLayout.addWidget(self.textBrowser)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setCenterButtons(True)
        self.verticalLayout.addWidget(self.buttonBox)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"),
                               self.reject)
        self.textBrowser.setHtml("<html><head></head>\n"
        "<body>\n"
        "<p align=\"center\">\n"
        "<span style=\" font-size:16pt;\">Qstitch\n"
        "</span></p>\n"
        "<p> This software can be used for stiching tiled images and element\n"
        " mapping data from SEM or similar equipments.\n"
        "<ul>Copyright &copy; 2015 Petras Jokubauskas klavishas@gmail.com</p>\n"
        "<p>This program is free software: you can redistribute it and/or\n"
        " modify it \n"
        "under the terms of the GNU General Public License as published by\n"
        " the Free \n"
        "Software Foundation, version 3 of the License, or any\n"
        " later version.</p>\n"
        "<p>This program is distributed in the hope that it will be useful,\n"
        " but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
        " MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU\n"
        " General Public License for more details.</p>\n"
        "<p>You should have received a copy of the GNU General Public License\n"
        " along with this program. If not, see http://www.gnu.org/licenses/.\n"
        "</p>\n"
        "<p> If code is not available in repisitories such as github,\n"
        " you can ask author</p>"
        "<p>Program uses <span style=\" font-weight:600;\">pyqtgraph</span> \n"
        "(for graphical representation and graph visualisation\n"
        "),<span style=\" font-weight:600;\">os and \n"
        "sys</span> to deal with files; \n"
        "<span style=\" font-weight:600;\">pytables</span> are planed to be \n"
        "implemented for really huge elemental mappings and hdf5 support;\n"
        "<span style=\" font-weight:600;\">lxml</span> to parse xml like, \n"
        "<span style=\" color:#ff0000;\">BROKEN</span> by design \n"
        "BRUKER&trade;&copy;&reg; files (*.rtj) generated for jobs and \n"
        "project files (*.rtx);<span style=\" font-weight:600;\">numpy</span>\n"
        "is used for generating 2 dimentional array where all stiching\n"
        " happens by \n"
        "populating separate tiles into slice of the array.</p>\n"
        "<ul><li>At the begining the selected directory are searched for\n"
        " apropriate \n"
        "tiling files and indexed into hierachical list/tree: \n"
        "sample/element/tile/filename.</li>\n"
        "<li><span style=\" font-weight:600;\">2nd</span> the shitty bruker\n"
        " jobs \n"
        "file are opened, cleand up from the incompetent\n"
        " bruker&trade;&copy;&reg; \n"
        "&quot;engineers&quot; crap to compile with xml standard, and then \n"
        "objectified with lxml.objectify.</li>\n"
        "<li><span style=\" font-weight:600;\">3rd</span> from objectified\n"
        " xml, \n"
        "the main parameters (leaving behind the shitload&trade; of \n"
        "clusterfuck&trade; of the rest of 99.9% bruker\'s&trade;&copy;&reg; \n"
        "bullshit&trade;) are extracted.</li>\n"
        "<li><span style=\" font-weight:600;\">4th</span> from gathered\n"
        " information \n"
        "dummy array are generated </li>\n"
        "<li><span style=\" font-weight:600;\">5th</span> using 3x3 grid\n"
        " the main \n"
        "parameters of the image stiching can be setup.</li>\n"
        "<li><span style=\" font-weight:600;\">6th</span> after that huge\n"
        " numpy \n"
        "arrays can be generated and saved to appropriate \n"
        "format</li></ul></body></html>")


class ChangeLogDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("ChangeLog")
        self.resize(600, 450)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.textBrowser = QtGui.QTextBrowser(self)
        self.verticalLayout.addWidget(self.textBrowser)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setCenterButtons(True)
        self.verticalLayout.addWidget(self.buttonBox)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"),
                               self.reject)
        self.textBrowser.setText(changelog.changelog)


def filter_basic(sample):
    a_list = []
    temp_list = deepcopy(final_list[sample])
    for i in temp_list:
        a_list.append({'name': i,
                       'type': 'list',
                       'values': ['None',
                                  'median',
                                  'bilateral',
                                  'blur',
                                  'gaussian'],
                       'value': 'None'})
    return a_list

initial_filter_parameters = {'bilateral':
                              [{'name': 'd',
                                'type': 'int',
                                'value': 1},
                               {'name': 'sigmaColor',
                                'type': 'float',
                                'value': 1.0},
                               {'name': 'sigmaSpace',
                                'type': 'float',
                                'value': 1.0}
                              ],
                             'median':
                              [{'name': 'ksize',
                                'type': 'int',
                                'value': 1,
                                'step': 2,
                                'limits': (1, 255)
                               }],
                             'gaussian':
                              [{'name': 'ksize',
                                'type': 'int',
                                'value': 1,
                                'step': 2,
                                'limits': (1, 255)},
                               {'name': 'sigma',
                                'type': 'float',
                                'value': 1.0,
                                'limits': (0.0, 255.0)}],
                             'blur':
                              [{'name': 'ksize',
                                'type': 'int',
                                'value': 1,
                                'limits': (1, 255)}]}


def filter_parameters():
    global filter_parameter_list
    initial_list = deepcopy(final_list)  # copy dict
    for sample in initial_list:
        for detector in initial_list[sample]:
            initial_list[sample][detector] = deepcopy(initial_filter_parameters)
    filter_parameter_list = initial_list


def param_basic(sample):
    tree = [
        {'name': 'Image', 'type': 'group', 'children': [
            {'name': 'height', 'type': 'int', 'value': image_size[sample][0],
                'suffix': 'px', 'readonly': True},
            {'name': 'width', 'type': 'int', 'value': image_size[sample][1],
                'suffix': 'px', 'readonly': True},
            {'name': 'dx', 'type': 'float', 'value': 0.000001, 'suffix': 'm/px',
                'siPrefix': True, 'dec': True, 'step': 0.01},
            {'name': 'dy', 'type': 'float', 'value': 0.000001, 'suffix': 'm/px',
                'siPrefix': True, 'dec': True, 'step': 0.01},
            {'name': 'rotation', 'type': 'float', 'value': 0,
                'suffix': ' degree', 'step': 0.01},
            {'name': 'cutoff', 'type': 'group', 'children': [
                {'name': 'left', 'type': 'int', 'value': 0, 'suffix': 'px',
                    'limits': (0, image_size[sample][1] / 4)},
                {'name': 'right', 'type': 'int', 'value': 0, 'suffix': 'px',
                    'limits': (0, image_size[sample][1] / 4)},
                {'name': 'top', 'type': 'int', 'value': 0, 'suffix': 'px',
                    'limits': (0, image_size[sample][0] / 4)},
                {'name': 'bottom', 'type': 'int', 'value': 0, 'suffix': 'px',
                    'limits': (0, image_size[sample][0] / 4)},
            ]},
        ]},
        {'name': 'microscope', 'type': 'group', 'children': [
            {'name': 'magnification', 'type': 'float', 'value': 0},
            {'name': 'WD', 'type': 'float', 'value': 0, 'suffix': 'mm'},
            {'name': 'HV', 'type': 'float', 'value': 0, 'suffix': 'V',
                'siPrefix': True, 'dec': True, 'step': 1},
        ]},
        {'name': 'stage', 'type': 'group', 'children': [
            {'name': 'stage step x', 'type': 'float',
                'value': image_size[sample][1] / 1000000, 'suffix': 'm',
                'siPrefix': True, 'dec': True, 'step': 0.1
                },
            {'name': 'stage step y', 'type': 'float',
                'value': image_size[sample][0] / 1000000, 'suffix': 'm',
                'siPrefix': True, 'dec': True, 'step': 0.1
                },
        ]},
        {'name': 'mosaic tiles', 'type': 'group', 'children': [
            {'name': 'horizontal tiles', 'type': 'int',
                'value': max_tiles[sample]['maxx'], 'readonly': True},
            {'name': 'vertical tiles', 'type': 'int',
                'value': max_tiles[sample]['maxy'], 'readonly': True},
        ]},
    ]
    return tree


def param_first(sample, basic_part):
    tree = [
            {'name': sample, 'type': 'group', 'children': basic_part},
           ]
    return tree


def param_branch(sample, basic_part):
    tree = [
            {'name': sample, 'type': 'group', 'children': basic_part},
           ]
    return Parameter(name=sample, type='group', children=tree)


class StartQT4(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Qstitch v" + version)
        # signal connections:
        self.ui.actionImportDataFolder.triggered.connect(self.import_the_data)
        self.ui.actionImportMetadata.triggered.connect(self.import_the_jobs)
        self.ui.actionAbout.triggered.connect(self.help_about)
        self.ui.actionAbout_Qt.triggered.connect(self.help_about_Qt)
        self.ui.actionChangelog.triggered.connect(self.help_changelog)
        self.ui.actionExportImages.triggered.connect(self.export_image)
        self.ui.actionExportHdf5.triggered.connect(self.export_hdf5)
        self.ui.actionClear.triggered.connect(self.clear_the_data)
        self.ui.overviewComboBox.currentIndexChanged.connect(self.draw_tiles)
        self.ui.overviewComboBox.currentIndexChanged.connect(
                                                    self.change_nineImg_sample)
        self.ui.setAsDefault.clicked.connect(self.save_parameter_state)
        #dynamic widget hiding/showing trigger:
        self.ui.actionDynamicWidgets.triggered.connect(
                                               self.toggle_toggling_of_widgets)
        # initial enbale/disable of gui parts
        self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.tabWidget.setTabEnabled(2, False)
        self.ui.tabWidget.setTabEnabled(3, False)
        self.ui.overviewWidget.setVisible(False)
        self.ui.filterDockWidget.setVisible(False)
        self.toggle_filter_dock_action =\
                                    self.ui.filterDockWidget.toggleViewAction()
        self.toggle_overview_dock_action =\
                                    self.ui.overviewWidget.toggleViewAction()
        self.toggle_stitch_dock_action = self.ui.stitchWidget.toggleViewAction()
        self.toggle_stitch_dock_action.setText('Show/Hide 3x3 stitching view')
        self.toggle_overview_dock_action.setText('Show/Hide tile overview')
        self.toggle_filter_dock_action.setText('Show/Hide filtering preview')
        self.ui.menuView.addAction(self.toggle_overview_dock_action)
        self.ui.menuView.addAction(self.toggle_stitch_dock_action)
        self.ui.menuView.addAction(self.toggle_filter_dock_action)
        self.toggle_overview_dock_action.setShortcut("Ctrl+Alt+O")
        self.toggle_stitch_dock_action.setShortcut("Ctrl+Alt+T")
        self.toggle_filter_dock_action.setShortcut("Ctrl+Alt+F")
        self.toggle_debug = self.ui.consoleWidget.toggleViewAction()
        self.ui.menuView.addAction(self.toggle_debug)
        self.toggle_debug.setShortcut("Ctrl+Alt+D")
        self.ui.pythonConsole.localNamespace = globals()
        self.ui.consoleWidget.setVisible(False)
        self.ui.stitchWidget.setVisible(False)
        self.ov = self.ui.graphicalOverview
        self.vb = self.ov.addViewBox(0, 1)
        self.vb.setAspectLocked(True)
        xScale = pg.AxisItem(orientation='bottom', linkView=self.vb)
        self.ov.addItem(xScale, 1, 1)
        yScale = pg.AxisItem(orientation='left', linkView=self.vb)
        self.ov.addItem(yScale, 0, 0)
        self.op = pg.PlotDataItem()
        xScale.setLabel(units="m")
        yScale.setLabel(units='m')
        self.vb.addItem(self.op)
        self.vb.invertY()
        self.parameters = {}
        # setting part for filter visualisation:
        self.oi = self.ui.originalView
        self.fi = self.ui.filteredView
        self.fi.view.setXLink(self.oi.view)
        self.fi.view.setYLink(self.oi.view)
        self.fpt = self.ui.filtersTreeView
        self.fpt.itemSelectionChanged.connect(self.set_filter_images)
        # setting dictionaries for data for visualisation
        self.filters = {}
        self.rect = {}
        self.img = {}
        self.data1 = {}
        #initiation of simple models used in the Q*views:
        self.sampleListModel = QtGui.QStandardItemModel()
        # initiation of flags for import/append data
        self.data_append_flag = 0  # 0 import, 1 for append
        self.metadata_append_flag = 0  # same as above
        # icons for changing function of button (import/append)
        self.icon = QtGui.QIcon()
        self.icon.addPixmap(
              QtGui.QPixmap(":/exterminator/icons/import_from_dir.svg"),
              QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon1 = QtGui.QIcon()
        self.icon1.addPixmap(
              QtGui.QPixmap(":/exterminator/icons/import_rtj.svg"),
              QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_a = QtGui.QIcon()
        self.icon_a.addPixmap(
              QtGui.QPixmap(":/exterminator/icons/append_from_dir.svg"),
              QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon1_a = QtGui.QIcon()
        self.icon1_a.addPixmap(
              QtGui.QPixmap(":/exterminator/icons/append_rtj.svg"),
              QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #initialy triggered functions:
        self.toggle_toggling_of_widgets()
        self.ui.tabWidget.currentChanged.connect(self.unhide_tabs)

    def unhide_tabs(self):
        tab_name = self.ui.tabWidget.currentWidget().objectName()
        if tab_name == 'tab_param':
            self.ui.tabWidget.setTabEnabled(2, True)
        elif tab_name == 'tab_filters':
            self.ui.tabWidget.setTabEnabled(3, True)
            self.ui.tabWidget.currentChanged.disconnect(self.unhide_tabs)

    def toggle_toggling_of_widgets(self):
        if self.ui.actionDynamicWidgets.isChecked():
            self.ui.tabWidget.currentChanged.connect(self.toggle_widgets)
        else:
            try:
                self.ui.tabWidget.currentChanged.disconnect(self.toggle_widgets)
            except:
                pass

    def toggle_widgets(self):
        tab_name = self.ui.tabWidget.currentWidget().objectName()
        if (tab_name == 'tab_tiles') or (tab_name == 'tab_finish'):
            self.ui.overviewWidget.setVisible(False)
            self.ui.stitchWidget.setVisible(False)
            self.ui.filterDockWidget.setVisible(False)
        elif tab_name == 'tab_param':
            self.ui.overviewWidget.setVisible(True)
            self.ui.stitchWidget.setVisible(True)
            self.ui.filterDockWidget.setVisible(False)
        elif tab_name == 'tab_filters':
            self.ui.overviewWidget.setVisible(True)
            self.ui.stitchWidget.setVisible(False)
            self.ui.filterDockWidget.setVisible(True)

    def tweek_filter(self):
        if self.fpt.selectedItems() != [] and\
                                        self.fpt.selectedItems()[0].depth == 1:
            sample = self.fpt.selectedItems()[0].parent().param.name()
            detector = self.fpt.selectedItems()[0].param.name()
            a_filter = self.fpt.selectedItems()[0].param.value()
            self.ui.filterParamView.clear()
            if a_filter != 'None':
                temp_param = Parameter(name=a_filter,
                                       type='group',
                    children=filter_parameter_list[sample][detector][a_filter])
                self.ui.filterParamView.setParameters(temp_param)
                #temp_parent = self.ui.filterParamView.listAllItems()[0].param
                temp_param.sigTreeStateChanged.connect(self.filterParam2dict)
                temp_param.sigTreeStateChanged.connect(self.updateFilteredImage)
                #self.ui.filterParamView.setParameters(Parameter(name=a_filter,
                #type='group',
                #children=filter_parameter_list[sample][detector][a_filter]))
            else:
                try:
                    self.filtered_image *= 0
                    self.fi.updateImage()
                except:
                    pass

    def updateFilteredImage(self):
        if self.fpt.selectedItems() != [] and\
                                        self.fpt.selectedItems()[0].depth == 1:
            sample = self.fpt.selectedItems()[0].parent().param.name()
            detector = self.fpt.selectedItems()[0].param.name()
            a_filter = self.fpt.selectedItems()[0].param.value()
            fp = []
            if a_filter != 'None':
                for i in range(0,
                       len(filter_parameter_list[sample][detector][a_filter])):
                    fp.append(
                    self.ui.filterParamView.listAllItems()[i + 1].param.value())
                try:
                    self.filtered_image[::] = filterImage(self.original_image,
                                                          a_filter,
                                                          *fp)
                    self.fi.updateImage()
                    # the two below are required especialy when jumping
                    # from the 16bit to 8bit images or vica versa.
                    self.fi.setLevels(0, np.max(self.filtered_image))
                    self.fi.setHistogramRange(0, np.max(self.filtered_image))
                except (AttributeError, ValueError):
                    self.filtered_image = filterImage(self.original_image,
                                                      a_filter,
                                                      *fp)
                    self.fi.setImage(np.swapaxes(self.filtered_image, 0, 1))

    def filterParam2dict(self):
        if self.fpt.selectedItems() != [] and\
                                        self.fpt.selectedItems()[0].depth == 1:
            sample = self.fpt.selectedItems()[0].parent().param.name()
            detector = self.fpt.selectedItems()[0].param.name()
            a_filter = self.fpt.selectedItems()[0].param.value()
            for i in range(0,
                       len(filter_parameter_list[sample][detector][a_filter])):
                filter_parameter_list[sample][detector][a_filter][i]['value'] =\
                  self.ui.filterParamView.listAllItems()[i + 1].param.value()

    def set_filter_images(self):
        if self.fpt.selectedItems() != [] and\
                                        self.fpt.selectedItems()[0].depth == 1:
            sample = self.fpt.selectedItems()[0].parent().param.name()
            detector = self.fpt.selectedItems()[0].param.name()
            a_filter = self.fpt.selectedItems()[0].param.value()
            tile = pts[sample]
            self.original_image =\
                              image2numpy(mapping_list[sample][detector][tile])
            if self.original_image.dtype == 'float32':
                filter_parameter_list[sample][detector]['median'][0]['limits']\
                                                                  = (1, 5)
            self.oi.setImage(np.swapaxes(self.original_image, 0, 1))
            self.tweek_filter()
            #self.ui.filterParamView.clear()
            if a_filter != 'None':
                fp = []  # temporary list of filter parameters for given sample
                for i in range(0,
                       len(filter_parameter_list[sample][detector][a_filter])):
                    fp.append(
                    self.ui.filterParamView.listAllItems()[i + 1].param.value())
                self.filtered_image = filterImage(self.original_image,
                                             a_filter,
                                             *fp)
                self.fi.setImage(np.swapaxes(self.filtered_image, 0, 1))
            else:
                try:
                    self.filtered_image *= 0
                    self.filtered_image.astype(np.uin8)
                    self.fi.setImage(np.swapaxes(self.filtered_image, 0, 1))
                except:
                    pass

                #temp_param = Parameter(name=a_filter,
                                       #type='group',
                    #children=filter_parameter_list[sample][detector][a_filter])
                #self.ui.filterParamView.setParameters(temp_param)
                ##temp_parent = self.ui.filterParamView.listAllItems()[0].param
                #temp_param.sigTreeStateChanged.connect(self.filterParam2dict)
        else:
            self.ui.filterParamView.clear()
            try:
                self.filtered_image *= 0
                self.fi.updateImage()
            except:
                pass

    def help_about_Qt(self):
        self.about_Qt = QtGui.QMessageBox.aboutQt(self, "About Qt")

    def help_about(self):
        self.about = AboutDialog()
        self.about.exec_()

    def help_changelog(self):
        self.changelog = ChangeLogDialog()
        self.changelog.exec_()

    def export_image(self):
        self.update_final_list()
        self.save_images = ExportImageWindow()
        self.save_images.exec_()

    def update_final_list(self):
        for sample in final_list:
            for detector in final_list[sample]:
                final_list[sample][detector] = self.filters[sample].\
                                          param(sample).param(detector).value()

    def export_hdf5(self):
        self.save_hdf5 = ExportHdf5Window()
        self.save_hdf5.exec_()

    def fill_item(self, item, value):
        """helper function dic -> QTreeWidget"""
        item.setExpanded(True)
        if type(value) is dict:
            for key, val in sorted(value.items()):
                child = QtGui.QTreeWidgetItem()
                child.setText(0, str(key))
                item.addChild(child)
                self.fill_item(child, val)
        elif type(value) is list:
            for val in value:
                child = QtGui.QTreeWidgetItem()
                item.addChild(child)
                if type(val) is dict:
                    child.setText(0, '[dict]')
                    self.fill_item(child, val)
                elif type(val) is list:
                    child.setText(0, '[list]')
                    self.fill_item(child, val)
                else:
                    child.setText(0, str(value))
                child.setExpanded(True)
        else:
            child = QtGui.QTreeWidgetItem()
            child.setText(0, str(value))
            child.setToolTip(0, str(value))
            item.addChild(child)

    def fill_ft_widget(self, value):
        self.ui.treeDataTiles.clear()  # clear tile files tree widget
        self.fill_item(self.ui.treeDataTiles.invisibleRootItem(), value)

    def fill_final_widget(self, value):
        self.ui.treeFinalWidget.clear()  # clear tile files tree widget
        for i in final_list:
            item_0 = QtGui.QTreeWidgetItem(self.ui.treeFinalWidget)
            item_0.setCheckState(0, QtCore.Qt.Unchecked)
            item_0.setFlags(QtCore.Qt.ItemIsUserCheckable |
                            QtCore.Qt.ItemIsEditable |
                            QtCore.Qt.ItemIsEnabled |
                            QtCore.Qt.ItemIsTristate)
            item_0.setText(0, i)
            item_0.setText(1, i)
            for j in final_list[i]:
                item_1 = QtGui.QTreeWidgetItem(item_0)
                item_1.setCheckState(0, QtCore.Qt.Unchecked)
                item_1.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                QtCore.Qt.ItemIsEditable |
                                QtCore.Qt.ItemIsEnabled)
                item_1.setText(0, j)
                item_1.setText(1, j)

    def exportFinalTree(self):
        mapping = {}
        root = self.ui.treeFinalWidget.invisibleRootItem()
        for index in range(root.childCount()):
            parent = root.child(index)
            if parent.checkState(0) >= 1:  # checked or partialy checked
                mapping[parent.text(0)] = {'name': parent.text(1),
                                           'signals': {}}
                for row in range(parent.childCount()):
                    child = parent.child(row)
                    if child.checkState(0) == QtCore.Qt.Checked:
                        mapping[parent.text(0)]['signals'][child.text(0)] =\
                                                                 child.text(1)
        return mapping

    def data_overview(self):
        samples = 0
        thingy = ""
        self.maxtile = maxTileNumberBr()
        for i in mapping_list:
            det = 0
            detectors = []
            for j in mapping_list[i]:
                detectors.append(j)
                det += 1
            samples += 1
            detectors.sort()
            dimensions = str(self.maxtile[i]['maxx']) + 'x' + \
            str(self.maxtile[i]['maxy'])
            thingy += i + "\n    " + "elements(+detectors):   (" + str(det) + \
                      ")\n      " + (", ".join(detectors)) + "\n    " + \
                      "tiles:      " + dimensions + "\n\n  "
        thingy = "samples:   (" + str(samples) + ")\n\n  " + thingy
        self.ui.plainTextEdit.setPlainText(thingy)

    def reset_tile_graph_color(self):
        for i in self.vb.allChildItems()[2:-1]:
            i.setBrush(brush_tile)

    def clear_the_data(self):
        global mapping_list
        global tile_index
        global pts
        global stitchy
        global xstage
        global ystage
        global image_size
        global max_tiles
        global final_list
        global filter_parameter_list
        global base_image
        clear_msg = "Are you sure you want to clear all the progress?"
        reply = QtGui.QMessageBox.question(self, 'Message',
                     clear_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            mapping_list = {}
            xstage = {}
            ystage = {}
            tile_index = {}
            pts = {}
            stitchy = {}
            image_size = {}
            max_tiles = {}
            final_list = {}
            filter_parameter_list = {}
            base_image = {}
            self.rect = {}
            self.img = {}
            self.data1 = {}
            self.ui.treeDataTiles.clear()
            self.ui.treeFinalWidget.clear()
            self.data_append_flag = 0  # 0 import, 1 for append
            self.metadata_append_flag = 0  # same as above
            self.ui.actionImportDataFolder.setIcon(self.icon)
            self.ui.actionImportDataFolder.setText('import data folder')
            self.ui.actionImportMetadata.setIcon(self.icon1)
            self.ui.overviewComboBox.setModel(QtGui.QStandardItemModel())
            self.parameters = {}
            self.ui.treeParameters.clear()
            self.ui.plainTextEdit.setPlainText('')
            self.vb.clear()
            self.fpt.clear()
            try:
                self.tweeke.vb.clear()
                self.oi.setImage((self.original_image * 0).astype(np.uint8))
                self.fi.setImage((self.original_image * 0).astype(np.uint8))
            except:
                pass
            self.ui.actionImportMetadata.setEnabled(False)
            self.ui.actionExportImages.setEnabled(False)

    def import_the_data(self):
        """method of importing tiles from the directory and
        populating the dictionary with information and
        copying dictionary into QTreeWidget for displaying file hierarchy"""
        self.directory = QtGui.QFileDialog.getExistingDirectory(
                           None,
                           'Select a folder:',
                           '/mnt/bulk-data/etc/extra_large_mapping/AL20-1',
                           QtGui.QFileDialog.ShowDirsOnly)
        self.start_importing_data()
        for sample in self.filters:
            self.filters[sample].sigTreeStateChanged.connect(self.tweek_filter)
            self.filters[sample].sigTreeStateChanged.connect(
                                                      self.updateFilteredImage)

    def getBaseImageName(self):
        for sample in mapping_list:
            a = list(mapping_list[sample].keys())
            b = ['BSE', 'AsB', 'BEI']
            #b = ['Signal A']
            overlap = [x for x in a if x in b]
            if overlap != []:
                base_image[sample] = overlap[0]
            else:
                dlg = BSEMissing(sample)
                if dlg.exec_():
                    base_image[sample] = dlg.returnSample()

    @waiting_effects
    def start_importing_data(self):
        if self.directory != '':
            self.data_dir = self.directory
            # scaning given directory, initiation of data dictionary, and
            # returning counting objects in dictionary
            z = fill_mapping_dict(self.data_dir)
            #check for BSE, AsB, BEI or custom images to use as the base images
            self.getBaseImageName()
            fill_tile_index()
            imageSize()
            if z > 0:
                self.ui.actionImportMetadata.setEnabled(True)
                self.fill_ft_widget(mapping_list)
                self.fill_final_widget(final_list)
                self.data_overview()
                self.ui.tabWidget.setTabEnabled(1, True)
                #self.ui.tabWidget.setTabEnabled(2, True)
                self.sampleListModel = QtGui.QStandardItemModel()
                for r in list(mapping_list.keys()):
                    item = QtGui.QStandardItem(r)
                    item.setEditable(False)
                    if (self.maxtile[r]['maxx'] or self.maxtile[r]['maxx']) < 3:
                        item.setBackground(col_bad)
                    else:
                        item.setBackground(col_not_so_good)
                    self.sampleListModel.appendRow(item)
                    if self.data_append_flag == 0:
                        self.ui.actionImportDataFolder.setText(
                                                    'append the data folder')
                        self.ui.actionImportDataFolder.setIcon(self.icon_a)
                        self.data_append_flag = 1
                        self.parameters[r] = param_branch(r, param_basic(r))
                        self.filters[r] = param_branch(r, filter_basic(r))
                        self.ui.treeParameters.setParameters(
                                            self.parameters[r], showTop=False)
                        self.ui.filtersTreeView.setParameters(
                                            self.filters[r], showTop=False)
                    elif r not in self.parameters:
                        self.parameters[r] = param_branch(r, param_basic(r))
                        self.filters[r] = param_branch(r, filter_basic(r))
                        self.ui.treeParameters.addParameters(
                                            self.parameters[r], showTop=False)
                        self.ui.filtersTreeView.addParameters(
                                            self.filters[r], showTop=False)
                    elif self.parameters[r].param(r).param('mosaic tiles').\
                            param('horizontal tiles').value() <\
                            max_tiles[r]['maxx'] and self.parameters[r].\
                            param(r).param('mosaic tiles').\
                            param('vertical tiles').value() <\
                            max_tiles[r]['maxy']:
                                self.parameters[r].param(r).\
                                         param('mosaic tiles').\
                                         param('horizontal tiles').setValue(
                                                        max_tiles[r]['maxx'])
                                self.parameters[r].param(r).\
                                         param('mosaic tiles').\
                                         param('vertical tiles').setValue(
                                                        max_tiles[r]['maxy'])
                    self.rect[r] = {}
                    self.img[r] = {}
                    self.data1[r] = {}
                    pts[r] = tile_name(r, int(max_tiles[r]['maxx'] / 2 + 1),
                                       int(max_tiles[r]['maxy'] / 2 + 1))
                    stitching_list(r, pts[r])
                    self.populate_rect_dict(r)
                    self.populate_img_dict(r)
                    self.parameters[r].sigTreeStateChanged.connect(
                                                            self.redraw_tiles)
                    self.parameters[r].sigTreeStateChanged.connect(
                                                           self.update_stitch)
                self.ui.overviewComboBox.setModel(self.sampleListModel)
                self.ui.treeFinalWidget.clicked.\
                                            connect(self.toggle_export_buttons)
                self.ui.overviewWidget.setVisible(True)
                self.ui.stitchWidget.setVisible(True)
                # create stitching preview (3x3) instance:
                self.tweeke = NineImg(self.ui.overviewComboBox.currentText())
                filter_parameters()
            else:
                self.dialog = QtGui.QMessageBox(
                    'No Data',
                    "no sufficient tile data found in:\n" + str(self.data_dir),
                    QtGui.QMessageBox.Icon(1),
                    1, 0, 0)    # Ok button
                self.dialog.show()

    @waiting_effects
    def save_parameter_state(self):
        for sample in self.parameters:
            stage_delta_x = self.parameters[sample].param(sample).\
                                           param('stage').param('stage step x')
            stage_delta_x.setDefault(stage_delta_x.value())
            stage_delta_y = self.parameters[sample].param(sample).\
                                           param('stage').param('stage step y')
            stage_delta_y.setDefault(stage_delta_y.value())
            width = self.parameters[sample].param(sample).param('Image').\
                                                                 param('width')
            width.setDefault(width.value())
            height = self.parameters[sample].param(sample).param('Image').\
                                                                param('height')
            height.setDefault(height.value())
            dx = self.parameters[sample].param(sample).param('Image').\
                                                                    param('dx')
            dx.setDefault(dx.value())
            dy = self.parameters[sample].param(sample).param('Image').\
                                                                    param('dy')
            dy.setDefault(dy.value())
            angle = self.parameters[sample].param(sample).param('Image').\
                                                              param('rotation')
            angle.setDefault(angle.value())
            left_cut = self.parameters[sample].param(sample).param('Image').\
                                                  param('cutoff').param('left')
            left_cut.setDefault(left_cut.value())
            right_cut = self.parameters[sample].param(sample).param('Image').\
                                                 param('cutoff').param('right')
            right_cut.setDefault(right_cut.value())
            top_cut = self.parameters[sample].param(sample).param('Image').\
                                                   param('cutoff').param('top')
            top_cut.setDefault(top_cut.value())
            bottom_cut = self.parameters[sample].param(sample).param('Image').\
                                                param('cutoff').param('bottom')
            bottom_cut.setDefault(bottom_cut.value())
            mag = self.parameters[sample].param(sample).param('microscope').\
                                                         param('magnification')
            mag.setDefault(mag.value())
            WD = self.parameters[sample].param(sample).param('microscope').\
                                                                    param('WD')
            WD.setDefault(WD.value())
            HV = self.parameters[sample].param(sample).param('microscope').\
                                                                    param('HV')
            HV.setDefault(HV.value())

    def populate_rect_dict(self, sample):
        root = self.parameters[sample].param(sample)
        stage_delta_x = root.param('stage').param('stage step x').value()
        stage_delta_y = root.param('stage').param('stage step y').value()
        width = root.param('Image').param('width').value()
        height = root.param('Image').param('height').value()
        dx = root.param('Image').param('dx').value()
        dy = root.param('Image').param('dy').value()
        angle = root.param('Image').\
                                                  param('rotation').value()
        left_cut = root.param('Image').\
                                      param('cutoff').param('left').value()
        right_cut = root.param('Image').\
                                      param('cutoff').param('right').value()
        top_cut = root.param('Image').\
                                      param('cutoff').param('top').value()
        bottom_cut = root.param('Image').\
                                      param('cutoff').param('bottom').value()
        for i in tile_index[sample]:

            x1 = cos_(angle) * stage_delta_x *\
                  (tile_index[sample][i]['x'] - 1) +\
                  sin_(angle) * stage_delta_y *\
                  (tile_index[sample][i]['y'] - 1) + dx * left_cut
            y1 = -sin_(angle) * stage_delta_x *\
                  (tile_index[sample][i]['x'] - 1) +\
                  cos_(angle) * stage_delta_y *\
                  (tile_index[sample][i]['y'] - 1) + dy * top_cut
            self.rect[sample][i] = selectableRect(i,
                   x1,
                   y1,
                   (width - left_cut - right_cut) * dx,
                   (height - top_cut - bottom_cut) * dy
                   )
            self.rect[sample][i].setPen(pen_tile)
            self.rect[sample][i].setToolTip(i)
            if sample in pts:
                if i in pts[sample]:
                    self.rect[sample][i].setBrush(brush_selection)
            else:
                self.rect[sample][i].setBrush(pg.mkBrush(None))

    def populate_img_dict(self, sample):
        self.img[sample] = {}
        root = self.parameters[sample].param(sample)
        width = root.param('Image').param('width').value()
        height = root.param('Image').param('height').value()
        left_cut = root.param('Image').param('cutoff').param('left').value()
        right_cut = root.param('Image').param('cutoff').param('right').value()
        top_cut = root.param('Image').param('cutoff').param('top').value()
        bottom_cut = root.param('Image').param('cutoff').param('bottom').value()
        for i in stitchy[sample]:
            try:
                if mapping_list[sample][base_image[sample]][i].\
                                                   rsplit('.', 1)[-1] == 'txt':
                    self.data1[sample][i] = np.loadtxt(
                                 mapping_list[sample][base_image[sample]][i],
                                 delimiter=';').transpose()
                else:
                    self.data1[sample][i] = misc.imread(
                        mapping_list[sample][base_image[sample]][i]).transpose()
                self.img[sample][i] = pg.ImageItem(
                            self.data1[sample][i][left_cut:width - right_cut,
                                      top_cut:height - bottom_cut])
                self.img[sample][i].setRect(self.rect[sample][i].rect())
                self.img[sample][i].setOpacity(0.7)
                self.img[sample][i].setToolTip(i)
            except:
                pass

    def draw_tiles(self):
        if str(self.ui.overviewComboBox.currentText()) != '':
            self.vb.clear()
            sample = self.ui.overviewComboBox.currentText()
            for i in self.rect[sample]:
                self.vb.addItem(self.rect[sample][i])
                self.vb.autoRange()
            # first time it will fail, so it should try and pass...
            # should be cleaned in future
            #try:
                #self.tweeke.vb.clear()
                #for i in self.img[sample]:
                    #self.tweeke.vb.addItem(myapp.img[sample][i])
                #self.tweeke.vb.autoRange()
            #except:
                #pass

    def redraw_stitch(self):
        if str(self.ui.overviewComboBox.currentText()) != '':
            sample = self.ui.overviewComboBox.currentText()
            self.populate_img_dict(sample)

    def change_nineImg_sample(self):
        try:
            sample = self.ui.overviewComboBox.currentText()
            self.tweeke.vb.clear()
            for i in self.img[sample]:
                self.tweeke.vb.addItem(myapp.img[sample][i])
            self.tweeke.vb.autoRange()
        except:
            pass

    def update_stitch(self):
        if str(self.ui.overviewComboBox.currentText()) != '':
            sample = self.ui.overviewComboBox.currentText()
            root = self.parameters[sample].param(sample)
            width = root.param('Image').param('width').value()
            height = root.param('Image').param('height').value()
            left_cut = root.param('Image').param('cutoff').param('left').value()
            right_cut = root.param('Image').\
                                          param('cutoff').param('right').value()
            top_cut = root.param('Image').param('cutoff').param('top').value()
            bottom_cut = root.param('Image').\
                                       param('cutoff').param('bottom').value()
            for i in stitchy[sample]:
                try:
                    self.img[sample][i].setImage(
                           self.data1[sample][i][left_cut:width - right_cut,
                                                top_cut:height - bottom_cut])
                    self.img[sample][i].setRect(self.rect[sample][i].rect())
                except:
                    pass

    @waiting_effects
    def redraw_tiles(self):
        if str(self.ui.overviewComboBox.currentText()) != '':
            self.vb.clear()
            sample = self.ui.overviewComboBox.currentText()
            self.populate_rect_dict(sample)
            self.draw_tiles()
            self.tweeke.vb.clear()
            for i in self.img[sample]:
                self.tweeke.vb.addItem(myapp.img[sample][i])

    def toggle_export_buttons(self):
        if not self.exportFinalTree():
            self.ui.actionExportImages.setEnabled(False)
            #self.ui.actionExportHdf5.setEnabled(False)
        else:
            self.ui.actionExportImages.setEnabled(True)
            #self.ui.actionExportHdf5.setEnabled(True)

    def import_the_jobs(self):
        global xstage
        global ystage
        fd = QtGui.QFileDialog(self)
        self.da_file = fd.getOpenFileName(None,
                                          'Select the bruker jobs file',
                                          self.data_dir,
                                          'Bruker jobs file (*.rtj)')
        self.update_with_jobs()
        self.tweeke.vb.autoRange()

    @waiting_effects
    def update_with_jobs(self):
        from os.path import isfile
        thingy = {}
        for sample_ in mapping_list:  # ??
            thingy[sample_] = 0  # ??
        if isfile(self.da_file):
            if self.metadata_append_flag == 0:
                self.ui.actionImportMetadata.setText('append metadata(*.rtj)')
                self.ui.actionImportMetadata.setIcon(self.icon1_a)
                self.metadata_append_flag = 1
            root = parseXML(self.da_file)
            for i in root.ClassInstance.ChildClassInstances.ClassInstance:
                if i.TRTJobEntry.JobType.text == 'jtMapping':
                    #TBD add condition here for tiling (one signal)
                    #jobs in the future
                    sample = i.TRTJobEntry.RootName.text
                    if i.TRTJobEntry.RootName.text not in xstage:
                        xstage[sample] = {}
                        ystage[sample] = {}
                    for  j in i.TRTJobEntry.ClassInstance:
                        if j.attrib['Type'] == 'TRTJobSEMSettings':
                            for k in j.ClassInstance:
                                if (k.attrib['Type'] == 'TRTSEMData') and\
                                                         (thingy[sample] == 0):
                                    self.parameters[sample].param(sample).\
                                         param('microscope').\
                                         param('HV').setValue(float(k.HV.text))
                                    self.parameters[sample].param(sample).\
                                         param('microscope').\
                                         param('WD').setValue(float(k.WD.text))
                                    self.parameters[sample].param(sample).\
                                         param('microscope').\
                                         param('magnification').\
                                         setValue(float(k.Mag.text))
                                    self.parameters[sample].param(sample).\
                                        param('Image').\
                                        param('dx').setValue(
                                                  float(k.DX.text) / 1000000)
                                    self.parameters[sample].param(sample).\
                                        param('Image').\
                                        param('dy').setValue(
                                                  float(k.DY.text) / 1000000)
                                    thingy[sample] = 1  # ???
                                elif k.attrib['Type'] == 'TRTSEMStageData':
                                    xstage[sample][i.TRTJobEntry.JobName.text]\
                                            = float(k.X.text)
                                    ystage[sample][i.TRTJobEntry.JobName.text]\
                                            = float(k.Y.text)
            for sample in xstage:
                if max_tiles[sample]['maxx'] > 1:
                    deltax = ((max(xstage[sample].values()) -
                           min(xstage[sample].values())) /
                           (max_tiles[sample]['maxx'] - 1)) / 1000000
                else:
                    deltax = 0
                self.parameters[sample].param(sample).param('stage').\
                        param('stage step x').setValue(deltax)
                if max_tiles[sample]['maxy'] > 1:
                    deltay = ((max(ystage[sample].values()) -
                           min(ystage[sample].values())) /
                           (max_tiles[sample]['maxy'] - 1)) / 1000000
                else:
                    deltay = 0
                self.parameters[sample].param(sample).param('stage').\
                        param('stage step y').setValue(deltay)
                self.populate_rect_dict(sample)
                self.populate_img_dict(sample)
                self.save_parameter_state()
                self.sampleListModel.findItems(sample)[0].\
                                                        setBackground(col_good)

    def estimate_final_array(self, sample):
        """function which iterates throught allready calculated
        bounding rectangles of tiles, and by finding min of (left,top)
        and max of (right,bottom), returns those values where first two
        can be used as offset populating numpy array
        """
        min_left, min_top = float('inf'), float('inf')
        max_right, max_bottom = float('-inf'), float('-inf')
        for i in self.rect[sample]:
            stuff = self.rect[sample][i]
            if stuff.rect().left() < min_left:
                min_left = stuff.rect().left()
            if stuff.rect().top() < min_top:
                min_top = stuff.rect().top()
            if stuff.rect().right() > max_right:
                max_right = stuff.rect().right()
            if stuff.rect().bottom() > max_bottom:
                max_bottom = stuff.rect().bottom()
        root = self.parameters[sample].param(sample)
        dx = root.param('Image').param('dx').value()
        dy = root.param('Image').param('dy').value()
        left = min_left / dx
        top = min_top / dy
        width = (max_right - min_left) / dx
        height = (max_bottom - min_top) / dy
        return round(left), round(top), round(width), round(height)


class NineImg():
    """canvas, the pyqtgraph plot where 3x3 images are placed and updated
    with basic parameters changed with UI"""
    def __init__(self, sample):
        v = myapp.ui.graphicsView
        self.vb = pg.ViewBox()
        self.vb.setAspectLocked()
        self.vb.invertY()
        v.setCentralItem(self.vb)
        for i in myapp.img[sample]:
            self.vb.addItem(myapp.img[sample][i])
        self.vb.autoRange()
        #### below have to be moved into main class, before the instation of
        #### this class to connect all samples not just selected one at begining
        #myapp.parameters[sample].sigTreeStateChanged.\
                                                  #connect(myapp.update_stitch)


exitFlag = 1


class ExportHdf5Window(QtGui.QDialog, Ui_ExportHdf5):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.browseButton.pressed.connect(self.open_the_hdf5)
        self.startButton.pressed.connect(self.start_sequence)
        self.abortButton.pressed.connect(self.abort_sequence)

    def open_the_hdf5(self):
        pass

    def start_sequence(self):
        pass

    def abort_sequence(self):
        pass


class ExportImageWindow(QtGui.QDialog, Ui_FinalImage):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.browseButton.pressed.connect(self.get_the_dir)
        self.startButton.pressed.connect(self.start_sequence)
        self.abortButton.pressed.connect(self.abort_sequence)
        self.directory = ''

    def get_the_dir(self):
        self.directory = QtGui.QFileDialog.getExistingDirectory(
                           None,
                           'Select a folder:',
                           '/mnt/bulk-data/etc/extra_large_mapping/AL20-1',
                           QtGui.QFileDialog.ShowDirsOnly)
        self.statusText.setText(self.directory)

    def stitch_the_dimention(self, sample, plane):
        #left offset, top offset, width, hight:
        lo, to, w, h = myapp.estimate_final_array(sample)
        mapping = np.zeros((h + 1, w + 1), dtype='uint8')
        root = myapp.parameters[sample].param(sample)
        width = root.param('Image').param('width').value()
        height = root.param('Image').param('height').value()
        dx = root.param('Image').param('dx').value()
        dy = root.param('Image').param('dy').value()
        left_cut = root.param('Image').param('cutoff').param('left').value()
        right_cut = root.param('Image').param('cutoff').param('right').value()
        top_cut = root.param('Image').param('cutoff').param('top').value()
        bottom_cut = root.param('Image').param('cutoff').param('bottom').value()
        val1 = 0  # initial progress bar value
        step1 = 1 / len(tile_index[sample]) * 100  # progress bar step
        self.progressBar_1.setValue(0)  # we like progress... not bars... :P
        for i in mapping_list[sample][plane]:
            fn = mapping_list[sample][plane][i]
            left = round(myapp.rect[sample][i].rect().left() / dx) - lo
            top = round(myapp.rect[sample][i].rect().top() / dy) - to
            right = left + width - left_cut - right_cut
            bottom = top + height - top_cut - bottom_cut
            if fn.rsplit('.', 1)[-1] == 'txt':
                data = np.loadtxt(fn, delimiter=';')
            else:
                data = misc.imread(fn, flatten=1)
                #for those nasty scaled bruker pngs...
                if plane != base_image[sample]:
                    scaledown = len(np.unique(data))
                    data = data * scaledown / 255
            # in case of signal beeing more than 8 bit increase the canvas
            # bit depth:
            if data.max() > 255 and mapping.dtype == 'uint8':
                mapping = mapping.astype(np.float32, copy=False)
            # copy the tile into canvas at the calculated place
            mapping[top:bottom, left:right] =\
                  data[top_cut:height - bottom_cut, left_cut:width - right_cut]
            self.statusText.setText(fn)
            val1 += step1
            self.progressBar_1.setValue(int(val1))
        if final_list[sample][plane] != 'None':
            a_filter = final_list[sample][plane]
            self.statusText.setText('applying ' + a_filter + ' filter')
            fp = []
            for i in filter_parameter_list[sample][plane][final_list[sample][plane]]:
                fp.append(i['value'])
            mapping[:] = filterImage(mapping, a_filter, *fp)
        if mapping.dtype == 'float32':
            mapping = mapping.astype(np.uint16, copy=False)

        return mapping

    def start_sequence(self):
        global abort
        self.startButton.setEnabled(False)
        self.closeButton.setEnabled(False)
        self.abortButton.setEnabled(True)
        self.imageFormat.setEnabled(False)
        self.browseButton.setEnabled(False)
        abort = 0
        self.progressBar_3.setValue(0)
        finito_list = myapp.exportFinalTree()
        step3 = 1 / len(finito_list) * 100
        val3 = 0
        im_format = self.imageFormat.currentText().strip('\*')

        for sample in finito_list:
            step2 = 1 / len(finito_list[sample]['signals']) * 100
            val2 = 0
            self.progressBar_2.setValue(0)
            for plane in finito_list[sample]['signals']:
                thingy = self.stitch_the_dimention(sample, plane)
                root = myapp.parameters[sample].param(sample).param('Image')
                name_wo_suffix = '/'.join([self.directory,
                          '_'.join([finito_list[sample]['name'],
                                    finito_list[sample]['signals'][plane]])])
                if im_format == '.tif':
                    tf.imsave(''.join([name_wo_suffix, im_format]), thingy)
                else:
                    misc.imsave(''.join([name_wo_suffix, im_format]), thingy)
                world = open(''.join([name_wo_suffix,
                                      ''.join([im_format, 'w'])]),
                             "w")
                world.write(str(root.param('dx').value()))
                world.write('\n0\n0\n')
                world.write(str(-root.param('dy').value()))
                world.write('\n1\n1')
                world.close()
                val2 += step2
                self.progressBar_2.setValue(int(val2))
                if abort == 1:
                    break
            val3 += step3
            self.progressBar_3.setValue(int(val3))
        self.progressBar_1.setValue(100)
        self.progressBar_2.setValue(100)
        self.progressBar_3.setValue(100)
        self.statusText.setText('done!')
        self.unfreeze_buttons()

    def abort_sequence(self):
        global exitFlag
        exitFlag = 0

    def unfreeze_buttons(self):
        self.startButton.setEnabled(True)
        self.closeButton.setEnabled(True)
        self.abortButton.setEnabled(False)
        self.imageFormat.setEnabled(True)
        self.browseButton.setEnabled(True)


class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args, **self.kwargs)
        return


if __name__ == "__main__":
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())
    app = QtGui.QApplication(sys.argv)
    myapp = StartQT4()
    myapp.show()
    sys.exit(app.exec_())
