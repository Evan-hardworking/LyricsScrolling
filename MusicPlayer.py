# I wrote this programme to build LyricVideos so there aren't enough functions set.

import bisect,os,datetime
from PySide6.QtGui import QFont, QAction, QPalette, QColor
from PySide6.QtCore import (
    Signal,
    QObject,
    Property,
    Qt,
    QUrl,
    QSettings,
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QFontDialog,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QSlider,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# settings.setValue("mySetting", "myValue")
# myValue = settings.value("mySetting")

class CustomObject(QObject):
    value_changed = Signal()

    def __init__(self):
        super().__init__()
        self._number = 0

    def get_number(self):
        return self._number

    def set_number(self, number):
        self._number = number
        self.value_changed.emit()

    number = Property(int, get_number, set_number)


class CustomObjectF(QObject):
    value_changed = Signal()

    def __init__(self):
        super().__init__()
        self._number = 0

    def get_number(self):
        return self._number

    def set_number(self, number):
        self._number = number
        self.value_changed.emit()

    number = Property(float, get_number, set_number)


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.settings = QSettings(
            os.path.join(self.script_dir, "settings.ini"), QSettings.IniFormat
        )

        if self.settings.value("FileLoaded") == None:
            self.settings.setValue("FileLoaded", False)
        self.init_ui()
        self.resize(1000, 600)

    def init_ui(self):
        self.muted = True
        self.Height = 20
        self.FontSize = 20
        self.RowSpacing = 50  # If it's changed, self.moveValue(=56) should be recalculated.
        self.moveValue = 56
        self.ChangedBefore = 0
        self.Start = 0
        self.EndLineValue = 0
        self.lrc_lines = []
        self.Widget = QWidget()
        self.object = CustomObject()
        self.enl_object = CustomObjectF()
        self.player = QMediaPlayer()
        self.FontColor = QColor(60, 60, 60)  # Set default Foreground and Background color
        self.BAckgroundColor = QColor(255, 255, 255)
        self.container = QVBoxLayout()
        self.container.setContentsMargins(0, 0, 0, 50)
        self.DurationBar = QSlider()
        self.DurationBar.setOrientation(Qt.Horizontal)
        self.hlv_btns = QHBoxLayout()
        self.btnAudio = QPushButton("加载音频\nLoadAudio")
        self.btnLrc = QPushButton("加载歌词\nLoadLyrics")
        self.labelTimer = QLabel("00:00.00")
        self.labelTimer.setFixedWidth(70)
        self.labelTimer.setAlignment(Qt.AlignCenter)
        self.btnPlay = QPushButton("播放\nPlay")
        self.btnPause = QPushButton("暂停\nPause")
        self.btnStop = QPushButton("停止\nStop")
        self.VolumeBar = QSlider()
        self.VolumeBar.setOrientation(Qt.Horizontal)
        self.VolumeBar.setValue(100)
        self.hlv_btns.addStretch()
        self.hlv_btns.addWidget(self.btnAudio)
        self.hlv_btns.addWidget(self.btnLrc)
        self.hlv_btns.addWidget(self.labelTimer)
        self.hlv_btns.addWidget(self.btnPlay)
        self.hlv_btns.addWidget(self.btnPause)
        self.hlv_btns.addWidget(self.btnStop)
        self.hlv_btns.addWidget(self.VolumeBar)
        self.hlv_btns.addStretch()
        self.container.addWidget(self.DurationBar)
        self.container.addLayout(self.hlv_btns)

        if self.settings.value("Font") == None:
            self.Font = QFont("Tw Cen MT")  # default font
        else:
            self.Font = self.settings.value("Font")
        if self.settings.value("FileLoaded"):
            self.lrc_file = self.settings.value("LrcFile")
            self.audiopath = self.settings.value("AudioFile")

            self.lrcSet()
            self.audioSet()
        else:
            self.AudioPathSelect()
            self.LrcPathSelect()

        self.lrcScroll = QScrollArea()
        self.lrcScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)    # Hide the scrollbar
        # self.lrcScroll.verticalScrollBar().setStyleSheet("background-color:blue")
        self.lrcScroll.setFrameStyle(QFrame.NoFrame)
        self.lrcScroll.setWidgetResizable(True)
        self.lrcScroll.setWidget(QWidget())
        self.lrcScroll.widget().setLayout(self.LrcDisplay())
        LineLabel = QLabel()
        LineLabel.setFixedHeight(100)
        self.container.addWidget(LineLabel)
        self.container.addWidget(self.lrcScroll)
        self.setLayout(self.container)
        self.moveAnimation()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(self.VolumeBar.value())
        self.checkValue = CustomObject()
        self.MenuActions()
        self.bind()

    def MenuActions(self):
        self.lrcScroll.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.MenuChangeFont = QAction("选择字体SetFont")
        self.MenuChangeFontColor = QAction("选择字体颜色SetFontColor")
        self.MenuChangeColor = QAction("设置背景颜色SetBackgroundColor")
        self.lrcScroll.addActions(
            [self.MenuChangeFont, self.MenuChangeFontColor, self.MenuChangeColor]
        )

    def startMove(self):
        self.moveAnimation()
        self.anim.start()

    def startEnl(self):
        self.enlargeAnimation()
        self.enl_anim.start()

    def moveAnimation(self):
        self.anim = QPropertyAnimation(self.object, b"number")
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.anim.setStartValue(self.Start * self.moveValue - 112)
        self.anim.setEndValue(self.EndLineValue - 112)
        self.object.value_changed.connect(self.SCrollMove)

    def enlargeAnimation(self):
        self.enl_anim = QPropertyAnimation(self.enl_object, b"number")
        self.enl_anim.setDuration(200)
        self.enl_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.enl_anim.setStartValue(0.0)
        self.enl_anim.setEndValue(120.0)
        self.enl_object.value_changed.connect(self.FontaAni)

    def FontaAni(self):
        self.FontValue = 15 + round(self.enl_object.number / 20, 3)
        self.CurrentLabel.setStyleSheet("font-size: %spt" % str(self.FontValue))
        palette = QPalette()
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        self.CurrentLabel.setPalette(palette)

    def SCrollMove(self):
        self.Value = self.object.number
        self.lrcScroll.verticalScrollBar().setValue(self.Value)

    def bind(self):
        self.VolumeBar.sliderMoved.connect(self.volume_slider_changed)
        self.DurationBar.sliderMoved.connect(self.play_slider_changed)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.btnAudio.clicked.connect(self.AudioPathSelect)
        self.btnLrc.clicked.connect(self.LrcPathSelect)
        self.btnPlay.clicked.connect(self.PlayAudio)
        self.btnPause.clicked.connect(self.PauseAudio)
        self.btnStop.clicked.connect(self.StopAudio)
        self.player.mediaStatusChanged.connect(self.AudioLoaded)
        self.MenuChangeFont.triggered.connect(self.changeFont)
        self.MenuChangeFontColor.triggered.connect(self.ChangeFontColor)
        self.MenuChangeColor.triggered.connect(self.ChangeColor)

    def position_changed(self, position):
        if self.DurationBar.maximum() != self.player.duration():
            self.DurationBar.setMaximum(self.player.duration())

        self.DurationBar.setValue(position)
        if position == 0:
            self.labelTimer.setText("00:00.00")
        else:
            milliseconds = position
            seconds = milliseconds / 1000
            time = datetime.timedelta(seconds=seconds)
            ba = str(time)
            formatted_time = str(time).split(".")[0] + "." + str(time)[:3]
            formatted_time = ba.split(":", 1)[1][:8]
            lbText = formatted_time
            self.labelTimer.setText(lbText)

            self.CurrentLineIndex = bisect.bisect_left(
                self.lrcTime, self.TransTime(lbText) + 0.3, key=self.TransTime
            )
            if self.indexIsChanged(self.CurrentLineIndex):
                self.EndLineValue = self.CurrentLineIndex * 56
                self.startMove()
                self.fontchange()

                self.Start = self.CurrentLineIndex

    def fontchange(self):
        if self.CurrentLineIndex >= 2:
            self.LastLabel = self.LcrVBox.itemAt(self.CurrentLineIndex - 2).widget()
            self.CurrentLabel = self.LcrVBox.itemAt(self.CurrentLineIndex - 1).widget()
            self.LastLabel.setStyleSheet("font-size: %spx" % str(self.FontSize))
            self.LastLabel.setPalette(self.palette)
            self.startEnl()

    def ChangeFontColor(self):
        self.FontColor = QColorDialog.getColor()

        self.palette.setColor(QPalette.WindowText, self.FontColor)
        for i in range(self.LcrVBox.count()):
            widget = self.LcrVBox.itemAt(i).widget()
            widget.setPalette(self.palette)

    def ChangeColor(self):
        self.backGroungPalette = QPalette()
        self.BAckgroundColor = QColorDialog.getColor()
        self.backGroungPalette.setColor(QPalette.ColorRole.Window, self.BAckgroundColor)
        self.lrcScroll.setPalette(self.backGroungPalette)

    def TransTime(self, Str):
        time = int(Str.split(":")[0]) * 60 + float(Str.split(":")[1])
        return time

    def duration_changed(self, duration):
        self.DurationBar.setRange(0, duration)

    def volume_slider_changed(self, position):
        self.audio_output.setVolume(float(position / self.VolumeBar.maximum()))

    def play_slider_changed(self, position):
        self.player.setPosition(position)

    def PlayAudio(self):
        self.player.play()

    def PauseAudio(self):
        self.player.pause()

    def StopAudio(self):
        self.player.stop()
        self.play_slider_changed(0)

    def AudioPathSelect(self):
        self.audiopath = ""
        self.audiopath, _ = QFileDialog().getOpenFileName(
            self, "获取音频", ".", "音频(*.mp3 *.wav *.flac);;所有文件 (*)"
        )
        if self.audiopath != "":
            self.settings.setValue("FileLoaded", True)
            self.settings.setValue("AudioFile", self.audiopath)
            self.audioSet()

    def audioSet(self):
        self.player.setSource(QUrl.fromLocalFile(self.audiopath))

    def AudioLoaded(self):
        if self.player.mediaStatus() == QMediaPlayer.LoadedMedia:
            self.btnPlay.setEnabled(True)

    def LrcPathSelect(self):
        self.lrc_file = ""
        self.lrc_file, _ = QFileDialog.getOpenFileName(
            self, "获取lrc文件", ".", "歌词(*.lrc);;所有文件 (*)"
        )
        if self.lrc_file != "":
            self.settings.setValue("LrcFile", self.lrc_file)
            self.lrcSet()

    def lrcSet(self):
        self.lrc_linesDict = self.load_lrc(self.lrc_file)
        self.lrcTime = []
        self.lrcLine = []
        for i in self.lrc_linesDict:
            lrcTime, lrcLine = i.split("]")
            self.lrcTime.append(lrcTime[-8:])
            self.lrcLine.append(lrcLine)
        return self.lrcLine

    def LrcDisplay(self):
        lrcLayout = QVBoxLayout()
        lrcLayout.setContentsMargins(100, 0, 100, 0)

        self.palette = QPalette()
        self.palette.setColor(QPalette.WindowText, self.FontColor)

        for index, i in enumerate(self.lrcTime):
            DisplayLine = QLabel(self.lrcLine[index], self.Widget)
            DisplayLine.setFont(self.Font)
            DisplayLine.setObjectName(i)
            DisplayLine.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # DisplayLine.setAlignment(Qt.AlignCenter)  # Set AlignCenter
            DisplayLine.setFixedHeight(self.RowSpacing)
            DisplayLine.setStyleSheet("font-size: %spx" % self.FontSize)
            DisplayLine.setPalette(self.palette)

            lrcLayout.addWidget(DisplayLine)
        self.LcrVBox = lrcLayout
        return self.LcrVBox

    def indexIsChanged(self, New):
        if New != self.Start:
            return True
        else:
            return False

    def load_lrc(self, lrc_file):
        with open(lrc_file, "r") as f:
            lrc_text = f.read()
        lrc_lines = lrc_text.split("\n")
        return lrc_lines

    def changeFont(self):
        ok, font = QFontDialog.getFont()
        if ok:
            self.Font = font
            self.settings.setValue("Font", self.Font)
            for i in range(self.LcrVBox.count()):
                widget = self.LcrVBox.itemAt(i).widget()
                widget.setFont(self.Font)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.player.isPlaying():
                self.player.pause()
            else:
                self.player.play()


if __name__ == "__main__":
    app = QApplication([])
    window1 = MyWindow()
    window1.show()
    app.exec()
