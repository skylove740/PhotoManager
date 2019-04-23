import sys, os
from pathlib import Path
from PIL import Image
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from Contants import *

# Load QT Designer UI Interface
class Form(QtWidgets.QDialog):
    setResultTextSignal = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.myui = uic.loadUi("photoUI.ui", self)
        self.setResultTextSignal.connect(self.setResultText)
        self.baseListView.doubleClicked.connect(self.baseItemSelected)
        self.cmpListView.doubleClicked.connect(self.cmpItemSelected)
        self.myui.show()


   ############### Slots ##############


    def baseLoadBtnClicked(self):
        baseDir = QtWidgets.QFileDialog.getExistingDirectory(self,"Select base file path","./")
        self.basePath.setText(baseDir)
        self.baseListView.setModel(self.addAllFilesToList(baseDir))
        self.setResultTextSignal.emit(NOTIFY_LOAD_SUCCESS)

    def cmpLoadBtnClicked(self):
        cmpDir = QtWidgets.QFileDialog.getExistingDirectory(self,"Select compare file path","./")
        self.comparePath.setText(cmpDir)
        self.cmpListView.setModel(self.addAllFilesToList(cmpDir))
        self.setResultTextSignal.emit(NOTIFY_LOAD_SUCCESS)

    def cmpBtnClicked(self):
        # TBD : 너무 느림... 빠르게 하는 방법 강구 필요.
        # TBD : Thread로 돌려야할듯.
        self.sameListCmp = {}
        self.sameListBase = {}
        basePath = self.basePath.text().strip()
        cmpPath = self.comparePath.text().strip()
        if basePath != '' and cmpPath != '':
            # 현재 list에 있는 모든 값을 rowIndex:value dictionary로 가져옴
            baseFileList = {i:str(self.baseListView.model().item(i).text()) for i in range(self.baseListView.model().rowCount())}
            cmpFileList = {i:str(self.cmpListView.model().item(i).text()) for i in range(self.cmpListView.model().rowCount())}
            for bi in baseFileList.keys():
                try:
                    self.caculateProgress(int(bi)+1)
                    baseImg = Image.open(basePath + '/' + baseFileList[bi].strip())
                    for ci in cmpFileList.keys():
                        if basePath != cmpPath:
                            try:
                                cmpImg = Image.open(cmpPath+'/'+cmpFileList[ci].strip())
                                if baseImg == cmpImg:
                                    print("same ",basePath+'/'+baseFileList[bi].strip(), cmpPath+'/'+cmpFileList[ci].strip())
                                    self.sameListCmp[ci] = cmpPath+'/'+cmpFileList[ci].strip()
                                    self.sameListBase[bi] = basePath+'/'+baseFileList[bi].strip()
                            except Exception as e:
                                #print('*** Caught exception: %s: %s' % (e.__class__, e))
                                continue
                except Exception as e:
                    #print('*** Caught exception: %s: %s' % (e.__class__, e))
                    continue
            for i in self.sameListCmp.keys():
                # 같은 파일들 이름은 붉은 글씨로 표기함
                self.cmpListView.model().setData(self.cmpListView.model().index(i,0), QBrush(Qt.red), QPalette.Base)
                # 같은 파일들은 선택해줌
                self.cmpListView.setSelection(self.cmpListView.rectForIndex(self.cmpListView.model().index(i,0)), QItemSelectionModel.Select)
            for i in self.sameListBase.keys():
                self.baseListView.model().setData(self.baseListView.model().index(i,0), QBrush(Qt.red), QPalette.Base)
            self.setResultTextSignal.emit(NOTIFY_COMPARE_SUCCESS)
        else:
            self.setResultTextSignal.emit(NOTIFY_SET_PATH)

    def cmpSelecAllBtnClicked(self):
        currentText = self.CmpSelecAllBtn.text().strip()
        if currentText == SELECT_ALL_BTN_STATE[0]:
            self.CmpSelecAllBtn.setText(SELECT_ALL_BTN_STATE[1])
            self.cmpListView.selectAll()
        else:
            self.CmpSelecAllBtn.setText(SELECT_ALL_BTN_STATE[0])
            self.cmpListView.clearSelection()

    def baseSelecAllBtnClicked(self):
        currentText = self.BaseSelecAllBtn.text().strip()
        if currentText == SELECT_ALL_BTN_STATE[0]:
            self.BaseSelecAllBtn.setText(SELECT_ALL_BTN_STATE[1])
            self.baseListView.selectAll()
        else:
            self.BaseSelecAllBtn.setText(SELECT_ALL_BTN_STATE[0])
            self.baseListView.clearSelection()

    def removeSelecFilesBtnClicked(self):
        selectedList = self.cmpListView.selectedIndexes()        
        while len(selectedList) > 0:
            removeFilePath = self.comparePath.text().strip() + selectedList[0].data().strip()
            self.cmpListView.model().removeRow(selectedList[0].row())
            os.remove(removeFilePath)
            selectedList = self.cmpListView.selectedIndexes()

    def setResultText(self, str):
        self.resultText.setText(str)

    def baseItemSelected(self):
        # QListView에서는 selectedIndexes()로 현재 선택된 list들을 가져올 수 있다.
        # 그결과 list의 row()로 row 번호, data()로 list 값을 가져올 수 있다.
        imgPath = str(self.basePath.text().strip() + self.baseListView.selectedIndexes()[-1].data().strip()).strip()
        #img = Image.open(imgPath)
        # 이미지를 Label에 출력하려면 QPixmap을 사용해야한다.
        imgLabel = QPixmap(imgPath)
        imgLabel = imgLabel.scaledToHeight(self.baseImgView.height())
        self.baseImgView.setPixmap(imgLabel)

    def cmpItemSelected(self):
        imgPath = str(self.comparePath.text().strip() + self.cmpListView.selectedIndexes()[-1].data().strip()).strip()
        imgLabel = QPixmap(imgPath)
        imgLabel = imgLabel.scaledToHeight(self.cmpImgView.height())
        self.cmpImgView.setPixmap(imgLabel)

    def addAllFilesToList(self, path):
        if os.path.exists(path):
            model = QStandardItemModel()
            fileList = []
            self.loadAllFiles(path, fileList, 1, '')
            for fName in fileList:
                item = QStandardItem(fName)
                item.setEditable(False)
                model.appendRow(item)
            return model
        return None


   ############### Functions ##############


    def loadAllFiles(self, path, files, emptyVol, parent):
        try:
            if os.path.exists(path):
                fileList = os.listdir(path)
                for f in fileList:
                    filePath = path+"/"+f
                    if os.path.isdir(filePath):
                        # 현재 file이 directory인 경우 list에 추가하고 재귀호출을 한다.
                        # 이 때, 현재 파일이 directory 하위임을 표시하기 위해 emptyVol에 1을 더해주고 현재 폴더 이름을 전달한다.
                        # emptyVol은 들여쓰기 단계를 표기하기 위해 존재한다.
                        files.append(str(emptyVol*" ")+"/"+f)
                        self.loadAllFiles(filePath, files, emptyVol+1, parent+'/'+f)
                    elif os.path.isfile(filePath):
                        files.append(str(emptyVol*" ")+" /"+parent+'/'+f)
                    else:
                        continue
        except Exception as e:
            print('*** Caught exception: %s: %s' % (e.__class__, e))
            self.setResultTextSignal.emit('%s: %s' % (e.__class__, e))

    def caculateProgress(self, index):
        totalCount = self.baseListView.model().rowCount()
        progress = int((int(index) / totalCount) * 100)
        self.progressBar.setValue(progress)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = Form()
    sys.exit(app.exec())