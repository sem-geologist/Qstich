# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'export_to_hdf5.ui'
#
# Created: Sat Apr 11 17:26:44 2015
#      by: PyQt4 UI code generator 4.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ExportHdf5(object):
    def setupUi(self, ExportHdf5):
        ExportHdf5.setObjectName(_fromUtf8("ExportHdf5"))
        ExportHdf5.resize(665, 151)
        self.horizontalLayout = QtGui.QHBoxLayout(ExportHdf5)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.statusText = QtGui.QLabel(ExportHdf5)
        self.statusText.setObjectName(_fromUtf8("statusText"))
        self.gridLayout.addWidget(self.statusText, 4, 1, 1, 1)
        self.label_4 = QtGui.QLabel(ExportHdf5)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)
        self.progressBar_3 = QtGui.QProgressBar(ExportHdf5)
        self.progressBar_3.setProperty("value", 0)
        self.progressBar_3.setObjectName(_fromUtf8("progressBar_3"))
        self.gridLayout.addWidget(self.progressBar_3, 2, 1, 1, 1)
        self.label = QtGui.QLabel(ExportHdf5)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.label_2 = QtGui.QLabel(ExportHdf5)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.progressBar_2 = QtGui.QProgressBar(ExportHdf5)
        self.progressBar_2.setProperty("value", 0)
        self.progressBar_2.setObjectName(_fromUtf8("progressBar_2"))
        self.gridLayout.addWidget(self.progressBar_2, 1, 1, 1, 1)
        self.progressBar_1 = QtGui.QProgressBar(ExportHdf5)
        self.progressBar_1.setProperty("value", 0)
        self.progressBar_1.setObjectName(_fromUtf8("progressBar_1"))
        self.gridLayout.addWidget(self.progressBar_1, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(ExportHdf5)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.line = QtGui.QFrame(ExportHdf5)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout.addWidget(self.line, 3, 1, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.browseButton = QtGui.QPushButton(ExportHdf5)
        self.browseButton.setObjectName(_fromUtf8("browseButton"))
        self.verticalLayout.addWidget(self.browseButton)
        self.startButton = QtGui.QPushButton(ExportHdf5)
        self.startButton.setObjectName(_fromUtf8("startButton"))
        self.verticalLayout.addWidget(self.startButton)
        self.abortButton = QtGui.QPushButton(ExportHdf5)
        self.abortButton.setEnabled(False)
        self.abortButton.setText(_fromUtf8("Abort"))
        self.abortButton.setObjectName(_fromUtf8("abortButton"))
        self.verticalLayout.addWidget(self.abortButton)
        self.closeButton = QtGui.QPushButton(ExportHdf5)
        self.closeButton.setEnabled(True)
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.verticalLayout.addWidget(self.closeButton)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(ExportHdf5)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(_fromUtf8("pressed()")), ExportHdf5.reject)
        QtCore.QMetaObject.connectSlotsByName(ExportHdf5)

    def retranslateUi(self, ExportHdf5):
        ExportHdf5.setWindowTitle(_translate("ExportHdf5", "export to hdf5", None))
        self.statusText.setText(_translate("ExportHdf5", "...", None))
        self.label_4.setText(_translate("ExportHdf5", "status:", None))
        self.label.setText(_translate("ExportHdf5", "Total", None))
        self.label_2.setText(_translate("ExportHdf5", "progress of \n"
" the one plane", None))
        self.label_3.setText(_translate("ExportHdf5", "progress of\n"
" the sample", None))
        self.browseButton.setText(_translate("ExportHdf5", "open/ create\n"
" hdf5 file", None))
        self.startButton.setText(_translate("ExportHdf5", "Start", None))
        self.closeButton.setText(_translate("ExportHdf5", "Close", None))

