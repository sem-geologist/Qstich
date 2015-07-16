# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'finalize.ui'
#
# Created: Fri Apr 10 01:36:55 2015
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

class Ui_FinalImage(object):
    def setupUi(self, FinalImage):
        FinalImage.setObjectName(_fromUtf8("FinalImage"))
        FinalImage.resize(623, 154)
        self.horizontalLayout = QtGui.QHBoxLayout(FinalImage)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.statusText = QtGui.QLabel(FinalImage)
        self.statusText.setObjectName(_fromUtf8("statusText"))
        self.gridLayout.addWidget(self.statusText, 4, 1, 1, 1)
        self.label_4 = QtGui.QLabel(FinalImage)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)
        self.progressBar_3 = QtGui.QProgressBar(FinalImage)
        self.progressBar_3.setProperty("value", 0)
        self.progressBar_3.setObjectName(_fromUtf8("progressBar_3"))
        self.gridLayout.addWidget(self.progressBar_3, 2, 1, 1, 1)
        self.label = QtGui.QLabel(FinalImage)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.label_2 = QtGui.QLabel(FinalImage)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.progressBar_2 = QtGui.QProgressBar(FinalImage)
        self.progressBar_2.setProperty("value", 0)
        self.progressBar_2.setObjectName(_fromUtf8("progressBar_2"))
        self.gridLayout.addWidget(self.progressBar_2, 1, 1, 1, 1)
        self.progressBar_1 = QtGui.QProgressBar(FinalImage)
        self.progressBar_1.setProperty("value", 0)
        self.progressBar_1.setObjectName(_fromUtf8("progressBar_1"))
        self.gridLayout.addWidget(self.progressBar_1, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(FinalImage)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.line = QtGui.QFrame(FinalImage)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout.addWidget(self.line, 3, 1, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.browseButton = QtGui.QPushButton(FinalImage)
        self.browseButton.setObjectName(_fromUtf8("browseButton"))
        self.verticalLayout.addWidget(self.browseButton)
        self.imageFormat = QtGui.QComboBox(FinalImage)
        self.imageFormat.setObjectName(_fromUtf8("imageFormat"))
        self.imageFormat.addItem(_fromUtf8(""))
        self.imageFormat.addItem(_fromUtf8(""))
        self.verticalLayout.addWidget(self.imageFormat)
        self.startButton = QtGui.QPushButton(FinalImage)
        self.startButton.setObjectName(_fromUtf8("startButton"))
        self.verticalLayout.addWidget(self.startButton)
        self.abortButton = QtGui.QPushButton(FinalImage)
        self.abortButton.setEnabled(False)
        self.abortButton.setText(_fromUtf8("Abort"))
        self.abortButton.setObjectName(_fromUtf8("abortButton"))
        self.verticalLayout.addWidget(self.abortButton)
        self.closeButton = QtGui.QPushButton(FinalImage)
        self.closeButton.setEnabled(True)
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.verticalLayout.addWidget(self.closeButton)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(FinalImage)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(_fromUtf8("pressed()")), FinalImage.reject)
        QtCore.QMetaObject.connectSlotsByName(FinalImage)

    def retranslateUi(self, FinalImage):
        FinalImage.setWindowTitle(_translate("FinalImage", "Export to images", None))
        self.statusText.setText(_translate("FinalImage", "...", None))
        self.label_4.setText(_translate("FinalImage", "status:", None))
        self.label.setText(_translate("FinalImage", "Total", None))
        self.label_2.setText(_translate("FinalImage", "progress of \n"
" the one plane", None))
        self.label_3.setText(_translate("FinalImage", "progress of\n"
" the sample", None))
        self.browseButton.setText(_translate("FinalImage", "Save to folder...", None))
        self.imageFormat.setItemText(0, _translate("FinalImage", "*.tif", None))
        self.imageFormat.setItemText(1, _translate("FinalImage", "*.png", None))
        self.startButton.setText(_translate("FinalImage", "Start", None))
        self.closeButton.setText(_translate("FinalImage", "Close", None))

