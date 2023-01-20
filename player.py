from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QLineEdit, QCheckBox
import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAbstractVideoSurface, QVideoFrame, QAbstractVideoBuffer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette, QPixmap, QImage
from PyQt5.QtCore import Qt, QUrl
import cv2
from qtrangeslider import QRangeSlider
import pandas as pd
import numpy as np
import os
import draw_box as db
from tkinter import Tk

class SnapshotVideoSurface(QAbstractVideoSurface):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_frame = QImage()
        self._start_frame = QImage()

    @property
    def current_frame(self):
        return self._current_frame
    
    @property
    def start_frame(self):
        return self._start_frame

    def supportedPixelFormats(self, handleType=QAbstractVideoBuffer.NoHandle):
        formats = [QVideoFrame.PixelFormat()]
        if handleType == QAbstractVideoBuffer.NoHandle:
            for f in [
                QVideoFrame.Format_RGB32,
                QVideoFrame.Format_ARGB32,
                QVideoFrame.Format_ARGB32_Premultiplied,
                QVideoFrame.Format_RGB565,
                QVideoFrame.Format_RGB555,
            ]:
                formats.append(f)
        return formats

    def present(self, frame):
        self._current_frame = frame.image()
        return True

    def keep_frame(self):
        self._start_frame = self._current_frame

class Window(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyQt5 Media Player")
        self.setGeometry(350, 100, 700, 500)
        self.setWindowIcon(QIcon('player.png'))

        p =self.palette()
        p.setColor(QPalette.Window, Qt.white)
        self.setPalette(p)

        self.init_ui()

        self.show()


    def init_ui(self):

        self.start_time = 0
        self.current_time = 0
        self.offset = (0,0)

        #create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)


        #create videowidget object
        self.videowidget = QVideoWidget()


        #create open button
        openBtn = QPushButton('Open Video')
        openBtn.clicked.connect(self.open_video)
        self.video_selected = False


        #create open button
        dfOpenBtn = QPushButton('Open Dataframe')
        dfOpenBtn.clicked.connect(self.open_df)
        self.df_selected = False


        #create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        #create button for start slicing
        self.startBtn = QPushButton('Start Slice')
        self.startBtn.setEnabled(False)
        self.startBtn.clicked.connect(self.start_slice)

        #create textbox 
        self.textBox = QLineEdit(placeholderText="Input format: ID - trial type")
        self.textBox.setEnabled(False)

        #create checkbox for choosing which frame to capture
        self.startBox = QCheckBox('Start')
        self.endBox = QCheckBox('End')
        self.startBox.setChecked(False)
        self.endBox.setChecked(False)


        #create button for generating slicing
        self.genBtn = QPushButton("Generate")
        self.genBtn.setEnabled(False)
        self.genBtn.clicked.connect(self.generate)


        #create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        #add ticks every minute
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(60000)

        #create a skip forward button
        self.skipForwardBtn = QPushButton()
        self.skipForwardBtn.setEnabled(False)
        self.skipForwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.skipForwardBtn.clicked.connect(self.skip_forward)

        #create a skip backward button
        self.skipBackwardBtn = QPushButton()
        self.skipBackwardBtn.setEnabled(False)
        self.skipBackwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.skipBackwardBtn.clicked.connect(self.skip_backward)


        #create slider 2 for slicing
        self.slider2 = QRangeSlider(Qt.Horizontal)
        self.slider2.setValue((0,0))
        self.slider2.setTickPosition(QSlider.TicksBelow)
        self.slider2.setTickInterval(60000)
        self.slider2.sliderMoved.connect(self.update_label)

        #create a seek forward button
        self.seekForwardBtn = QPushButton()
        self.seekForwardBtn.setEnabled(False)
        self.seekForwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.seekForwardBtn.clicked.connect(self.seek_forward)

        #create a seek backward button
        self.seekBackwardBtn = QPushButton()
        self.seekBackwardBtn.setEnabled(False)
        self.seekBackwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.seekBackwardBtn.clicked.connect(self.seek_backward)

        #create labels to indicate time
        self.first_handle = QLabel('First handle: ' + str(self.slider2.value()[0]))
        self.second_handle = QLabel('Second handle: ' + str(self.slider2.value()[1]))
        self.video_duration_label = QLabel('Video duration: ')

        #create label
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)


        #create hbox layout
        hboxLayout = QHBoxLayout()
        hboxLayout.setContentsMargins(0,0,0,0)
        hboxLayout.addWidget(openBtn)
        hboxLayout.addWidget(dfOpenBtn)
        hboxLayout.addWidget(self.playBtn)
        hboxLayout.addWidget(self.startBtn)
        hboxLayout.addWidget(self.textBox)
        hboxLayout.addWidget(self.startBox)
        hboxLayout.addWidget(self.endBox)
        hboxLayout.addWidget(self.genBtn)


        #create hbox layout
        hboxLayout2 = QHBoxLayout()
        hboxLayout2.setContentsMargins(0,0,0,0)
        hboxLayout2.addWidget(self.slider)
        hboxLayout2.addWidget(self.skipBackwardBtn)
        hboxLayout2.addWidget(self.skipForwardBtn)

        #create hbox layout for slider 2
        hboxLayout3 = QHBoxLayout()
        hboxLayout3.setContentsMargins(0,0,0,0)
        hboxLayout3.addWidget(self.slider2)
        hboxLayout3.addWidget(self.seekBackwardBtn)
        hboxLayout3.addWidget(self.seekForwardBtn)

        #create hbox layout for labels
        hboxLayout4 = QHBoxLayout()
        hboxLayout4.setContentsMargins(0,0,0,0)
        hboxLayout4.addWidget(self.first_handle)
        hboxLayout4.addWidget(self.second_handle)
        hboxLayout4.addWidget(self.video_duration_label)

        #create vbox layout
        vboxLayout = QVBoxLayout(spacing = 0)
        vboxLayout.addWidget(self.videowidget,540)
        vboxLayout.addLayout(hboxLayout)
        vboxLayout.addLayout(hboxLayout2)
        #vboxLayout.addWidget(self.slider2)
        vboxLayout.addLayout(hboxLayout3)
        vboxLayout.addLayout(hboxLayout4)


        self.setLayout(vboxLayout)
        self.snapshotVideoSurface = SnapshotVideoSurface(self)
        self.mediaPlayer.setVideoOutput([self.videowidget.videoSurface(), self.snapshotVideoSurface])


        #media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

        self.fixation = QLabel("", self)
        self.fixation.resize(20, 20)
        self.fixation.setPixmap(QPixmap("circle.png"))
        self.fixation.move(200, 200)
    
    def keyPressEvent(self, event):
        print(event.text())
        if event.key() == Qt.Key_W:
            self.offset = (self.offset[0], self.offset[1]-0.1)
            print(self.offset)
            self.fixation.move(self.fixation.x(), self.fixation.y() + self.offset[1])
            print("up")
        if event.key() == Qt.Key_S:
            self.offset = (self.offset[0], self.offset[1]+0.1)
            print(self.offset)
            self.fixation.move(self.fixation.x(), self.fixation.y() + self.offset[1])
            print("down")
        if event.key() == Qt.Key_D:
            self.offset = (self.offset[0]+0.1, self.offset[1])
            print(self.offset)
            self.fixation.move(self.fixation.x() + self.offset[0], self.fixation.y())
            print("right")
        if event.key() == Qt.Key_A:
            self.offset = (self.offset[0]-0.1, self.offset[1])
            print(self.offset)
            self.fixation.move(self.fixation.x() + self.offset[0], self.fixation.y())
            print("left")
        if event.key() == Qt.Key_Enter:
            print("Enter")

    def update_label(self):
        self.first_handle.setText('First handle: ' + str(self.slider2.value()[0]))
        self.second_handle.setText('Second handle: ' + str(self.slider2.value()[1]))


    def skip_forward(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() + 100)


    def skip_backward(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() - 100)


    def seek_forward(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() + 10000)


    def seek_backward(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() - 10000)


    def start_slice(self):
        self.slider2.setValue((self.slider2.sliderPosition()[1], self.slider2.sliderPosition()[1]))


    def open_video(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")

        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.video_selected = True
            if self.video_selected and self.df_selected:
                self.playBtn.setEnabled(True)
                self.textBox.setEnabled(True)
                self.genBtn.setEnabled(True)
                self.skipForwardBtn.setEnabled(True)
                self.skipBackwardBtn.setEnabled(True)
                self.seekForwardBtn.setEnabled(True)
                self.seekBackwardBtn.setEnabled(True)
                self.startBtn.setEnabled(True)


        #calculate the duration of the video
        data = cv2.VideoCapture(filename)
        frames = data.get(cv2.CAP_PROP_FRAME_COUNT)
        fps= int(data.get(cv2.CAP_PROP_FPS))
        self.video_duration = int(frames/fps) * 1000

        #update the slider depending on the video length
        self.slider.setRange(0, self.video_duration)
        self.slider2.setRange(0, self.video_duration)

        #update the label
        self.video_duration_label.setText('Video duration: ' + str(self.video_duration) + ' ms')

    
    def open_df(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Dataframe")

        if filename != '':
            dataframe = (QUrl.fromLocalFile(filename))
            self.df_selected = True
            self.df = pd.read_csv(filename)
            self.start_time = self.df.at[0, "time_stamp"]
            self.current_time = self.df.at[0, "time_stamp"]

            if self.video_selected and self.df_selected:
                self.playBtn.setEnabled(True)
                self.textBox.setEnabled(True)
                self.genBtn.setEnabled(True)
                self.skipForwardBtn.setEnabled(True)
                self.skipBackwardBtn.setEnabled(True)
                self.seekForwardBtn.setEnabled(True)
                self.seekBackwardBtn.setEnabled(True)
                self.startBtn.setEnabled(True)


    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()

        else:
            self.mediaPlayer.play()


    def mediastate_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )

        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )


    def position_changed(self, position):
        if self.video_selected and self.df_selected:
            self.slider.setValue(position)
            self.slider2.setValue([self.slider2.sliderPosition()[0], position])
            self.current_time = self.slider.sliderPosition() + self.start_time
            #update the position of fixation
            index = self.df['time_stamp'].sub(self.current_time).abs().idxmin()
            if np.isnan(self.df.at[index, "x_cord"]):
                index = index + 1
            print(self.offset)
            self.fixation.move(int(self.df.at[index, "x_cord"]/1920 * self.videowidget.width() + self.videowidget.x() + self.fixation.size().width()//2 + self.offset[0]), 
        int(self.df.at[index, "y_cord"]/1080 *  self.videowidget.height() + self.videowidget.y() + self.fixation.size().height()//2 + self.offset[1]))
            #update the label
            self.first_handle.setText('First handle: ' + str(self.slider2.value()[0]))
            self.second_handle.setText('Second handle: ' + str(self.slider2.value()[1]))


    def duration_changed(self, duration):
        self.slider.setRange(0, duration)


    def set_position(self, position):
        self.mediaPlayer.setPosition(position)


    def generate(self):
        textboxValue = self.textBox.text()
        print(self.slider2.sliderPosition()[0])

        #check that the first 3 values are an integer
        try:
            val = int(textboxValue[0:3])
        except ValueError:
            print("Input format: ID - trial type")
            return

        #check that the fourth letter is -
        if textboxValue[3] != "-":
            print("Input format: ID - trial type")

        #check that the last word is the trial type
        if textboxValue[4:len(textboxValue)] != "AI" and textboxValue[4:len(textboxValue)] != "Driver" \
            and textboxValue[4:len(textboxValue)] != "Navigator":
            print(textboxValue[4:len(textboxValue)])
            print("Input format: ID - trial type (AI, Driver, Navigator)")
            return

        #if both of the check boxes are not checked, return
        if self.startBox.isChecked() == False and self.endBox.isChecked() == False:
            print("Please check one of the checkboxes")
            return

        #if both of the check boxes are checked, return
        elif self.startBox.isChecked() == True and self.endBox.isChecked() == True:
            print("Please check only one of the checkboxes")
            return

        #if only one of the check boxes is checked then take a screenshot
        else:
            #keep the current position of the video
            temp_pos = self.mediaPlayer.position()

            #if the start box is checked, take a screenshot of the start of the slice
            if self.startBox.isChecked():
                self.mediaPlayer.pause()
                #set the media player position to the start of the slice
                self.mediaPlayer.setPosition(int(self.slider2.sliderPosition()[0])) 
        
        print(self.slider2.sliderPosition()[0])
        start_index = self.df['time_stamp'].sub(self.slider2.sliderPosition()[0] + self.start_time).abs().idxmin()
        if self.df.at[start_index, "time_stamp"] < self.slider2.sliderPosition()[0] + self.start_time:
            start_index = start_index + 1
        end_index = self.df['time_stamp'].sub(self.slider2.sliderPosition()[1] + self.start_time).abs().idxmin()
        if self.df.at[end_index, "time_stamp"] < self.slider2.sliderPosition()[1] + self.start_time:
            end_index = end_index + 1
        print(self.slider2.sliderPosition()[0])

        # #pop up window that asks to select the AOI
        root = Tk()
        root.update()

        image = self.snapshotVideoSurface.current_frame
        #save the image
        if not image.isNull():
            image = image.scaled(1910, 1080)
            image.save( os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + textboxValue + "-" + \
                 str(int(self.slider2.sliderPosition()[0])) + '-' + str(int(temp_pos)) + '.jpg', 'jpg')
        else:
            print("Null image")

        print(self.slider2.sliderPosition()[0])

        #pop up window that asks to select the AOI
        app = db.DrawBox(root, os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" +textboxValue + "-" + \
            str(int(self.slider2.sliderPosition()[0])) + '-' + str(int(temp_pos)) + '.jpg')
        root.mainloop()

        #write a csv file
        csv_dest = os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + textboxValue + '-' + \
             str(int(self.slider2.sliderPosition()[0])) + '-' + str(int(temp_pos)) + '.csv'
        with open(csv_dest, 'a') as f:
            #writing the four courners of the AOI box
            f.write(str(app.left) + ',' + str(app.top) + ',' + str(app.right) + ',' + str(app.bottom) + '\n')
            #writing the pandas dataframe
            self.df.iloc[start_index:end_index, 1:10].to_csv(f)
        
        if self.startBox.isChecked():
            #set the media player position back to the original position
            self.mediaPlayer.setPosition(int(temp_pos))
            self.slider.setValue(int(temp_pos))



    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())





app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())