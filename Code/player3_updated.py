from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QLineEdit, QCheckBox, QInputDialog
import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAbstractVideoSurface, QVideoFrame, QAbstractVideoBuffer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette, QPixmap, QImage
from PyQt5.QtCore import Qt, QUrl, QBuffer
import cv2
from qtrangeslider import QRangeSlider
import pandas as pd
import numpy as np
import os
import draw_box as db
import emip_toolkit as et
import io
from tkinter import Tk
from PIL import Image
import time
import threading


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

        p = self.palette()
        p.setColor(QPalette.Window, Qt.white)
        self.setPalette(p)

        self.init_ui()

        self.show()

    def init_ui(self):

        self.start_time = 0
        self.current_time = 0
        self.offset = (0, 0)

        # create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # create videowidget object
        self.videowidget = QVideoWidget()

        # create open video button
        openBtn = QPushButton('Open Video')
        openBtn.clicked.connect(self.open_video)
        self.video_selected = False

        # create open dataframe button
        dfOpenBtn = QPushButton('Open Dataframe')
        dfOpenBtn.clicked.connect(self.open_df)
        self.df_selected = False

        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        # create button for start slicing
        self.startBtn = QPushButton('Start Slice')
        self.startBtn.setEnabled(False)
        self.startBtn.clicked.connect(self.start_slice)

        # create textbox for time inputs
        self.textBox = QLineEdit(placeholderText="Input format: ID")
        self.textBox.setEnabled(False)
        self.textBox2 = QLineEdit(placeholderText="Input format: Start time-End time")
        self.textBox2.setEnabled(False)

        # create textbox for choosing which frame to capture
        self.frameBox = QLineEdit(placeholderText="Input format: Frame name")
        self.textBox2.setEnabled(False)

        # create button for generating slicing
        self.genBtn = QPushButton("Generate")
        self.genBtn.setEnabled(False)
        self.genBtn.clicked.connect(self.generate)

        # create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        # add ticks every minute
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(60000)

        # create a skip forward button
        self.skipForwardBtn = QPushButton()
        self.skipForwardBtn.setEnabled(False)
        self.skipForwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.skipForwardBtn.clicked.connect(self.skip_forward)

        # create a skip backward button
        self.skipBackwardBtn = QPushButton()
        self.skipBackwardBtn.setEnabled(False)
        self.skipBackwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.skipBackwardBtn.clicked.connect(self.skip_backward)

        # create slider 2 for slicing
        self.slider2 = QRangeSlider(Qt.Horizontal)
        self.slider2.setValue((0, 0))
        self.slider2.setTickPosition(QSlider.TicksBelow)
        self.slider2.setTickInterval(60000)
        self.slider2.sliderMoved.connect(self.update_label)

        # create a seek forward button
        self.seekForwardBtn = QPushButton()
        self.seekForwardBtn.setEnabled(False)
        self.seekForwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.seekForwardBtn.clicked.connect(self.seek_forward)

        # create a seek backward button
        self.seekBackwardBtn = QPushButton()
        self.seekBackwardBtn.setEnabled(False)
        self.seekBackwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.seekBackwardBtn.clicked.connect(self.seek_backward)

        # create labels to indicate time
        self.first_handle = QLabel('First handle: ' + str(self.slider2.value()[0]))
        self.second_handle = QLabel('Second handle: ' + str(self.slider2.value()[1]))
        self.video_duration_label = QLabel('Video duration: ')

        # create label
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # create exit button
        self.exitBtn = QPushButton('Exit')
        self.seekBackwardBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.exitBtn.clicked.connect(self.exit)

        # create exit boolean
        self.exit_condition = False

        # create hbox layout
        hboxLayout = QHBoxLayout()
        hboxLayout.setContentsMargins(0, 0, 0, 0)
        hboxLayout.addWidget(openBtn)
        hboxLayout.addWidget(dfOpenBtn)
        hboxLayout.addWidget(self.playBtn)
        hboxLayout.addWidget(self.startBtn)
        hboxLayout.addWidget(self.textBox)
        hboxLayout.addWidget(self.textBox2)
        hboxLayout.addWidget(self.frameBox)

        # create hbox layout
        hboxLayout2 = QHBoxLayout()
        hboxLayout2.setContentsMargins(0, 0, 0, 0)
        hboxLayout2.addWidget(self.slider)
        hboxLayout2.addWidget(self.skipBackwardBtn)
        hboxLayout2.addWidget(self.skipForwardBtn)

        # create hbox layout for slider 2
        hboxLayout3 = QHBoxLayout()
        hboxLayout3.setContentsMargins(0, 0, 0, 0)
        hboxLayout3.addWidget(self.slider2)
        hboxLayout3.addWidget(self.seekBackwardBtn)
        hboxLayout3.addWidget(self.seekForwardBtn)

        # create hbox layout for labels
        hboxLayout4 = QHBoxLayout()
        hboxLayout4.setContentsMargins(0, 0, 0, 0)
        hboxLayout4.addWidget(self.exitBtn)
        hboxLayout4.addWidget(self.first_handle)
        hboxLayout.addSpacing(15)
        hboxLayout4.addWidget(self.second_handle)
        hboxLayout.addSpacing(15)
        hboxLayout4.addWidget(self.video_duration_label)
        hboxLayout.addSpacing(15)
        hboxLayout4.addWidget(self.genBtn)

        # create vbox layout
        vboxLayout = QVBoxLayout(spacing=0)
        vboxLayout.addWidget(self.videowidget, 540)
        vboxLayout.addLayout(hboxLayout)
        vboxLayout.addLayout(hboxLayout2)
        # vboxLayout.addWidget(self.slider2)
        vboxLayout.addLayout(hboxLayout3)
        vboxLayout.addLayout(hboxLayout4)

        self.setLayout(vboxLayout)
        self.snapshotVideoSurface = SnapshotVideoSurface(self)
        self.mediaPlayer.setVideoOutput([self.videowidget.videoSurface(), self.snapshotVideoSurface])

        # media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
        # self.mediaPlayer.metaDataChanged.connect(self.meta_data_changed)

        self.fixation = QLabel("", self)
        self.fixation.resize(20, 20)
        self.fixation.setPixmap(QPixmap("circle.png"))
        self.fixation.move(200, 200)
        # whether fixation can be moved by mouseMoveEvent
        self.drag = False
        # creating lock for fixation
        self.fixation_lock = threading.Lock()

        self.resolution_ratio = 1920/1080
        self.resolution_width = 1920
        self.resolution_height = 1080
        self.x_offset = self.videowidget.x()
        self.y_offset = self.videowidget.y()
    
    def resizeEvent(self, event):
        if self.video_selected and self.df_selected:
            self.scale_resolution()
            self.move_fixation_auto(self.current_time)

    def mouseMoveEvent(self, event):
        # if video is paused and fixation pressed for the first time
        if self.drag is True:
            self.fixation_lock.acquire()
            current_offset = ((event.x() - 10) - self.fixation.x(),
                              (event.y() - 10) - self.fixation.y())
            self.offset = (self.offset[0] + current_offset[0],
                           self.offset[1] + current_offset[1])
            self.fixation.move(self.fixation.x() + current_offset[0],
                               self.fixation.y() + current_offset[1])
            self.fixation_lock.release()

    def mousePressEvent(self, event):
        if self.video_selected and self.df_selected:
            if self.mediaPlayer.state() == QMediaPlayer.PausedState:
                if self.drag is False:
                    if event.button() == Qt.LeftButton:
                        # check if mouse press was on fixation
                        x_error = event.pos().x() - self.fixation.x()
                        y_error = event.pos().y() - self.fixation.y()
                        if (0 <= x_error <= 20) and (0 <= y_error <= 20):
                            self.drag = True

    def mouseReleaseEvent(self, event):
        self.drag = False

    def keyPressEvent(self, event):

        current_offset = (0, 0)

        if event.key() == Qt.Key_W:
            current_offset = (0, -1)
        elif event.key() == Qt.Key_S:
            current_offset = (0, 1)
        elif event.key() == Qt.Key_D:
            current_offset = (1, 0)
        elif event.key() == Qt.Key_A:
            current_offset = (-1, 0)
        elif event.key() == Qt.Key_Enter:
            print("Enter")

        self.fixation_lock.acquire()

        self.fixation.move(self.fixation.x() + current_offset[0],
                           self.fixation.y() + current_offset[1])

        self.offset = (self.offset[0] + current_offset[0],
                       self.offset[1] + current_offset[1])

        self.fixation_lock.release()

        print(self.offset)

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
                self.textBox2.setEnabled(True)
                self.frameBox.setEnabled(True)
                self.genBtn.setEnabled(True)
                self.skipForwardBtn.setEnabled(True)
                self.skipBackwardBtn.setEnabled(True)
                self.seekForwardBtn.setEnabled(True)
                self.seekBackwardBtn.setEnabled(True)
                self.startBtn.setEnabled(True)

        # calculate the duration of the video
        data = cv2.VideoCapture(filename)
        frames = data.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = int(data.get(cv2.CAP_PROP_FPS))
        self.video_duration = int(frames / fps) * 1000

        # update the slider depending on the video length
        self.slider.setRange(0, self.video_duration)
        self.slider2.setRange(0, self.video_duration)

        # update the label
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
                self.textBox2.setEnabled(True)
                self.frameBox.setEnabled(True)
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
            self.scale_resolution()
            # start second thread to update fixation while playing
            self.t1 = threading.Thread(target=self.update_fixation)
            self.t1.start()

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

            # change fixation when slider moved
            self.move_fixation_auto(self.current_time)

            # update the label
            self.first_handle.setText('First handle: ' + str(self.slider2.value()[0]))
            self.second_handle.setText('Second handle: ' + str(self.slider2.value()[1]))

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def generate(self):
        part_id = self.textBox.text()

        # check that the first 3 values are an integer
        try:
            val = int(part_id[0:3])
        except ValueError:
            print("Input format: ID")
            return

        start_time, end_time = 0, 0

        start_time = self.slider2.sliderPosition()[0] + self.start_time
        end_time = self.slider2.sliderPosition()[1] + self.start_time

        type = None

        if self.frameBox.text() != '':
            type = self.frameBox.text()
        else:
            print("Choose the trial type")
            return

        # from the eye events dataframe, only take out the fixations during the given time span
        fixations = self.df[(self.df["eye_event"] == "fixation") & (self.df["time_stamp"] >= start_time) & \
                            (self.df["time_stamp"] <= end_time)]
        fixations = fixations.iloc[:, 1:7]

        # write a csv file
        path = os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/Dataframes/"
        print(path)

        try:
            os.makedirs(path)
            print(f"{path} made")
        except OSError as error:
            print("already made")

        csv_dest = path + part_id + "-" + type + "-" + \
                   str(int(self.slider2.sliderPosition()[0])) + '-' + str(
            int(self.slider2.sliderPosition()[1])) + '.csv'
        print(csv_dest)
        with open(csv_dest, 'a') as f:
            # writing the four courners of the AOI box
            f.write(str(self.offset[0]) + ',' + str(self.offset[1]) + '\n')
            # writing the pandas dataframe
            fixations.to_csv(f)

        self.skipped_df = pd.DataFrame(
            columns=["participant_ID", "trial", "time_stamp", "aoi_x", "aoi_y", "aoi_width", "aoi_height", "image",
                     "aoi_image"])
        self.skipped_df.astype(float)
        self.fixated_df = pd.DataFrame(
            columns=["participant_ID", "trial", "time_stamp", "duration", "x_cord", "y_cord", "aoi_x", "aoi_y",
                     "aoi_width", "aoi_height", "image", "aoi_image"])

        fixations = fixations.reset_index(drop=True)

        self.mediaPlayer.pause()
        current_time = fixations.loc[0, "time_stamp"] - self.start_time
        self.mediaPlayer.setPosition(current_time)

        image = self.snapshotVideoSurface.current_frame
        # pop up window that asks to select the AOI
        root = Tk()
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        image.save(buffer, "PNG")
        pil_im = Image.open(io.BytesIO(buffer.data()))
        app = db.DrawBox(root, pil_im)
        root.mainloop()

        for index, row in fixations.iterrows():
            self.mediaPlayer.pause()
            current_time = row["time_stamp"] - self.start_time
            # set the media player position to the start of the slice
            self.mediaPlayer.setPosition(current_time)

            root.mainloop()

            # take a screenshot
            image = self.snapshotVideoSurface.current_frame

            # save the image
            if not image.isNull():
                image = image.scaled(1910, 1080)
                image.save(
                    os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/" + part_id + "-" + \
                    str(current_time) + '.jpg', 'jpg')
            else:
                print("Null image")

            image = os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/" + part_id + "-" + \
                    str(current_time) + '.jpg'
            aoi = et.vscode_find_aoi(image, int(app.left), int(app.top), int(app.right), int(app.bottom))
            #print(aoi)
            aoi_image = et.vscode_draw_aoi(aoi, image, os.path.normpath(
                os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/")
            aoi_image.save(
                os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/aoi-" + part_id + "-" + \
                str(current_time) + '.jpg')
            aoi_image = os.path.normpath( 
                os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/aoi-" + part_id + "-" + \
                        str(current_time) + '.jpg'

            df = pd.DataFrame([[part_id, type, current_time]], columns=["participant_ID", "trial", "time_stamp"])
            df2 = pd.DataFrame([[aoi_image]], columns=["aoi_image"])
            result = et.hit_test(row, aoi, self.offset, part_id, type, current_time)
            #print(result)

            # if the fixation is not over a certain token, continue
            if result.empty:
                os.remove((os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/" + part_id + "-" + \
                          str(current_time) + '.jpg')
                os.remove(
                    os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/aoi-" + part_id + "-" + \
                    str(current_time) + '.jpg')
                continue

            # check if a fixation is an AI suggestion or not
            #if result.iloc[0, 0] == "AI" and 

            # if not empty, join the result dataframe with part-ID and trial type
            result = pd.concat([result, df2], axis=1)

            # if a fixation is in skipped dataframe
            for df_index, row in self.skipped_df.iterrows():
                if ((self.skipped_df.loc[df_index, "aoi_x"] == result.loc[0, "aoi_x"]) | (
                        self.skipped_df.loc[df_index, "aoi_y"] == result.loc[0, "aoi_y"])) \
                        & (self.skipped_df.loc[df_index, "aoi_width"] == result.loc[0, "aoi_width"]) & (
                        self.skipped_df.loc[df_index, "aoi_height"] == result.loc[0, "aoi_height"]):
                    self.skipped_df.drop([df_index], axis=0, inplace=True)

            # add fixation to the fixation dataframe
            self.fixated_df = pd.concat([self.fixated_df, result], ignore_index="true")

            # add all tokens except for the fixation
            for aoi_index, aoi_row in aoi.iterrows():
                # if the token is the fixation, then continue
                if (aoi.loc[aoi_index, "aoi_x"] == result.loc[0, "aoi_x"]) & (
                        aoi.loc[aoi_index, "aoi_y"] == result.loc[0, "aoi_y"]) & \
                        (aoi.loc[aoi_index, "aoi_width"] == result.loc[0, "aoi_width"]) & (
                        aoi.loc[aoi_index, "aoi_height"] == result.loc[0, "aoi_height"]):
                    continue
                else:
                    skipped = False
                    # if the token is already in skipped dataframe then continue
                    for df_index, row in self.skipped_df.iterrows():
                        if ((self.skipped_df.loc[df_index, "aoi_x"] == aoi.loc[aoi_index, "aoi_x"]) | (
                                self.skipped_df.loc[df_index, "aoi_y"] == aoi.loc[aoi_index, "aoi_y"])) \
                                & (self.skipped_df.loc[df_index, "aoi_width"] == aoi.loc[aoi_index, "aoi_width"]) & (
                                self.skipped_df.loc[df_index, "aoi_height"] == aoi.loc[aoi_index, "aoi_height"]):
                            skipped = True
                            break
                    # if not in skipped dataframe then add the token
                    if skipped == False:
                        skipped_token = aoi.loc[aoi_index:aoi_index,
                                        ["aoi_x", "aoi_y", "aoi_width", "aoi_height", "image"]]
                        skipped_token.index = [0]
                        df = pd.DataFrame([[part_id, type, current_time]],
                                          columns=["participant_ID", "trial", "time_stamp"])
                        df2 = pd.DataFrame([[aoi_image]], columns=["aoi_image"])
                        skipped_token = pd.concat([df, skipped_token, df2], axis=1)
                        self.skipped_df = pd.concat([self.skipped_df, skipped_token], ignore_index="true")

        # go through each fixation and check if it is AI suggestion or not
        self.fixated_df = et.check_AI_suggestions(self.fixated_df)

        self.fixated_df.to_csv(os.path.normpath(
            os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/Dataframes/fixation-" + part_id + "-" + \
                               type + "-" + str(int(self.slider2.sliderPosition()[0])) + '-' + str(
            int(self.slider2.sliderPosition()[1])) + "df.csv")
        self.skipped_df.to_csv(os.path.normpath(
            os.getcwd() + os.sep + os.pardir) + "/Data/" + part_id + "/Dataframes/skipped-" + part_id + "-" + \
                               type + "-" + str(int(self.slider2.sliderPosition()[0])) + '-' + str(
            int(self.slider2.sliderPosition()[1])) + "df.csv")

        print("Done")

    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    def update_fixation(self):
        # update the position of fixation whenever video is playing
        while self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            # update every 20ms
            if self.mediaPlayer.position() % 20 == 0:
                self.current_time = self.mediaPlayer.position() + self.start_time
                self.move_fixation_auto(self.current_time)

            if self.exit_condition is True:
                break

    def move_fixation_auto(self, time):
        index = self.df['time_stamp'].sub(time).abs().idxmin()
        if np.isnan(self.df.at[index, "x_cord"]):
            index = index + 1
        # lock around fixation change
        self.fixation_lock.acquire()
        self.fixation.move(
            int((self.df.at[index, "x_cord"] / 1920 * self.resolution_width
                 + self.x_offset + self.fixation.size().width() // 2) + self.offset[0]),
            int((self.df.at[index, "y_cord"] / 1080 * self.resolution_height
                 + self.y_offset + self.fixation.size().height() // 2) + self.offset[1]))
        self.fixation_lock.release()

    # need because video player dimensions are not the same as the video itself
    def scale_resolution(self):
        width = self.videowidget.width()
        height = self.videowidget.height()
        # maximum width/height in relation to the other
        max_width = height*self.resolution_ratio
        max_height = width/self.resolution_ratio
        # if extra blank space is on width
        if width > max_width:
            self.resolution_width = max_width
            self.resolution_height = height
            self.x_offset = (width - max_width) * .5 + self.videowidget.x()
            self.y_offset = (self.videowidget.y())
        # if extra blank space is on height
        elif height > max_height:
            self.resolution_width = width
            self.resolution_height = width/self.resolution_ratio
            self.x_offset = self.videowidget.x()
            self.y_offset = (height - max_height) * .5 + self.videowidget.y()

    def exit(self):
        # breaks update_fixation thread
        self.exit_condition = True
        time.sleep(1)
        sys.exit(app.exec_())


app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())
