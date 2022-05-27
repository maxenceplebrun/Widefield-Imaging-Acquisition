import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import RectangleSelector
from matplotlib.animation import FuncAnimation
import time
import matplotlib.pyplot as plt
import random
import numpy as np
import importlib.util   
from threading import *
import sys
import __main__
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.blocks import Stimulation, Block, Experiment
from src.controls import DAQ, Instrument, Camera
from src.signal_generator import make_signal, random_square

#from src.controls import DAQ, Instrument, Camera
#import pyqtgraph as pg  

#pg.setConfigOption('background', 'w')
#pg.setConfigOption('foreground', 'k')

class PlotWindow(QDialog):
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def get_data(self, time_values, pulses, jitter, width=0.2):
        y_values = random_square(time_values, pulses, width, jitter)
        return y_values

    def plot(self, x, y):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y)
        self.canvas.draw()

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Widefield Imaging Aquisition'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def closeEvent(self, *args, **kwargs):
        self.video_running = False
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.plot_x_values = []
        self.plot_y_values = []
        self.elapsed_time = 0
        
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignTop)

        self.experiment_settings_label = QLabel('Experiment Settings')
        self.experiment_settings_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.experiment_settings_label, 0,0)

        self.experiment_settings_main_window = QVBoxLayout()
        self.experiment_name_window = QHBoxLayout()
        self.experiment_name = QLabel('Experiment Name')
        self.experiment_name_window.addWidget(self.experiment_name)
        self.experiment_name_cell = QLineEdit()
        self.experiment_name_window.addWidget(self.experiment_name_cell)
        self.experiment_settings_main_window.addLayout(self.experiment_name_window)

        self.mouse_id_window = QHBoxLayout()
        self.mouse_id_label = QLabel('Mouse ID')
        self.mouse_id_window.addWidget(self.mouse_id_label)
        self.mouse_id_cell = QLineEdit()
        self.mouse_id_window.addWidget(self.mouse_id_cell)
        self.experiment_settings_main_window.addLayout(self.mouse_id_window)

        self.directory_window = QHBoxLayout()
        self.directory_save_files_checkbox = QCheckBox()
        self.directory_save_files_checkbox.setText("Save")
        self.directory_save_files_checkbox.stateChanged.connect(self.enable_directory)
        self.directory_window.addWidget(self.directory_save_files_checkbox)
        self.directory_choose_button = QPushButton("Select Directory")
        self.directory_choose_button.setIcon(QIcon("gui/icons/folder-plus.png"))
        self.directory_choose_button.setDisabled(True)
        self.directory_choose_button.clicked.connect(self.choose_directory)
        self.directory_window.addWidget(self.directory_choose_button)
        self.directory_cell = QLineEdit("")
        self.directory_cell.setReadOnly(True)
        self.directory_window.addWidget(self.directory_cell)
        self.experiment_settings_main_window.addLayout(self.directory_window)

        self.experiment_settings_main_window.addStretch()

        self.grid_layout.addLayout(self.experiment_settings_main_window, 1, 0)

        self.image_settings_label = QLabel('Image Settings')
        self.image_settings_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.image_settings_label, 0,1)

        self.image_settings_main_window = QVBoxLayout()

        self.framerate_window = QHBoxLayout()
        self.framerate_label = QLabel('Framerate')
        self.framerate_window.addWidget(self.framerate_label)
        self.framerate_cell = QLineEdit('30')
        self.framerate_window.addWidget(self.framerate_cell)
        self.image_settings_main_window.addLayout(self.framerate_window)

        self.exposure_window = QHBoxLayout()
        self.exposure_label = QLabel('Exposure')
        self.exposure_window.addWidget(self.exposure_label)
        self.exposure_cell = QLineEdit('10')
        self.exposure_window.addWidget(self.exposure_cell)
        self.image_settings_main_window.addLayout(self.exposure_window)

        self.image_settings_second_window = QHBoxLayout()
        self.speckle_button = QCheckBox('Infrared')
        self.image_settings_second_window.addWidget(self.speckle_button)
        self.red_button = QCheckBox('Red')
        self.image_settings_second_window.addWidget(self.red_button)
        self.green_button = QCheckBox('Green')
        self.image_settings_second_window.addWidget(self.green_button)
        self.fluorescence_button = QCheckBox('Blue')
        self.image_settings_second_window.addWidget(self.fluorescence_button)
        self.image_settings_main_window.addLayout(self.image_settings_second_window)
        
        self.roi_buttons = QStackedLayout()

        self.roi_layout1 = QHBoxLayout()
        self.reset_roi_button = QPushButton()
        self.reset_roi_button.setText("Reset ROI")
        self.reset_roi_button.setIcon(QIcon("gui/icons/zoom-out-area.png"))
        self.reset_roi_button.setEnabled(False)
        self.reset_roi_button.clicked.connect(self.reset_roi)
        self.roi_layout1.addWidget(self.reset_roi_button)

        self.set_roi_button = QPushButton()
        self.set_roi_button.setText("Set ROI")
        self.set_roi_button.setIcon(QIcon("gui/icons/zoom-in-area.png"))
        self.set_roi_button.clicked.connect(self.set_roi)
        self.roi_layout1.addWidget(self.set_roi_button)
        self.roi_layout1_container = QWidget()
        self.roi_layout1_container.setLayout(self.roi_layout1)
        
        self.roi_layout2 = QHBoxLayout()
        self.cancel_roi_button = QPushButton()
        self.cancel_roi_button.setText("Cancel")
        self.cancel_roi_button.setIcon(QIcon("gui/icons/zoom-cancel.png"))
        self.cancel_roi_button.clicked.connect(self.cancel_roi)
        self.roi_layout2.addWidget(self.cancel_roi_button)


        self.save_roi_button = QPushButton()
        self.save_roi_button.setText("Save ROI")
        self.save_roi_button.setIcon(QIcon("gui/icons/zoom-check.png"))
        self.save_roi_button.clicked.connect(self.save_roi)
        self.roi_layout2.addWidget(self.save_roi_button)
        self.roi_layout2_container = QWidget()
        self.roi_layout2_container.setLayout(self.roi_layout2)

        self.roi_buttons.addWidget(self.roi_layout1_container)
        self.roi_buttons.addWidget(self.roi_layout2_container)

        self.image_settings_main_window.addLayout(self.roi_buttons)

        self.activate_live_preview_button = QPushButton()
        self.activate_live_preview_button.setText("Start Live Preview")
        self.activate_live_preview_button.setIcon(QIcon("gui/icons/video"))
        self.activate_live_preview_button.clicked.connect(self.open_live_preview_thread)

        self.deactivate_live_preview_button = QPushButton()
        self.deactivate_live_preview_button.setText("Stop Live Preview")
        self.deactivate_live_preview_button.setIcon(QIcon("gui/icons/video-off"))
        self.deactivate_live_preview_button.clicked.connect(self.stop_live)

        self.live_preview_buttons = QStackedLayout()


        self.live_preview_buttons.addWidget(self.activate_live_preview_button)
        self.live_preview_buttons.addWidget(self.deactivate_live_preview_button)
        self.image_settings_main_window.addLayout(self.live_preview_buttons)
        self.image_settings_main_window.addStretch()
        


        self.grid_layout.addLayout(self.image_settings_main_window, 1, 1)

        self.live_preview_label = QLabel('Live Preview')
        self.live_preview_label.setFont(QFont("IBM Plex Sans", 17))
        self.numpy = np.random.rand(1024, 1024)
        self.image_view = PlotWindow()
        self.plot_image = plt.imshow(self.numpy, interpolation="nearest")
        self.plot_image.axes.get_xaxis().set_visible(False)
        self.plot_image.axes.axes.get_yaxis().set_visible(False)

        self.grid_layout.addWidget(self.live_preview_label, 0, 2)
        self.grid_layout.addWidget(self.image_view, 1, 2)

        self.stimulation_tree_label = QLabel('Stimulation Tree')
        self.stimulation_tree_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.stimulation_tree_label, 2, 0)

        self.stimulation_tree_window = QVBoxLayout()
        self.stimulation_tree = QTreeWidget()
        self.stimulation_tree.setHeaderLabels(["Name", "Iterations", "Delay", "Jitter", "Type", "Pulses", "Duration", "Jitter", "Width", "Frequency", "Duty", "Canal 1", "Canal 2"])
        for i in range(9):
            #self.stimulation_tree.header().hideSection(i+1)
            pass
        self.stimulation_tree.currentItemChanged.connect(self.actualize_tree)
        self.stimulation_tree_window.addWidget(self.stimulation_tree)


        self.stimulation_tree_switch_window = QStackedLayout()
        self.stimulation_tree_second_window = QHBoxLayout()
        self.stim_buttons_container = QWidget()
        self.delete_branch_button = QPushButton('Delete')
        self.delete_branch_button.setIcon(QIcon("gui/icons/trash.png"))
        self.delete_branch_button.clicked.connect(self.delete_branch)
        self.stimulation_tree_second_window.addWidget(self.delete_branch_button)
        self.add_brother_branch_button = QPushButton('Add Sibling')
        self.add_brother_branch_button.clicked.connect(self.add_brother)
        self.add_brother_branch_button.setIcon(QIcon("gui/icons/arrow-bar-down.png"))
        self.stimulation_tree_second_window.addWidget(self.add_brother_branch_button)
        self.add_child_branch_button = QPushButton('Add Child')
        self.add_child_branch_button.clicked.connect(self.add_child)
        self.add_child_branch_button.setIcon(QIcon("gui/icons/arrow-bar-right.png"))
        self.stimulation_tree_second_window.addWidget(self.add_child_branch_button)
        self.stim_buttons_container.setLayout(self.stimulation_tree_second_window)
        self.stimulation_tree_switch_window.addWidget(self.stim_buttons_container)
        
        self.new_branch_button = QPushButton("New Stimulation")
        self.new_branch_button.setIcon(QIcon("gui/icons/square-plus.png"))
        self.stimulation_tree_third_window = QHBoxLayout()
        self.stimulation_tree_third_window.addWidget(self.new_branch_button)
        self.stim_buttons_container2 = QWidget()
        self.stim_buttons_container2.setLayout(self.stimulation_tree_third_window)
        self.stimulation_tree_switch_window.addWidget(self.stim_buttons_container2)
        self.new_branch_button.clicked.connect(self.first_stimulation)
        self.grid_layout.addLayout(self.stimulation_tree_switch_window, 4, 0)


        
        
        #self.stimulation_tree_window.addLayout(self.stimulation_tree_switch_window)
        self.stimulation_tree_switch_window.setCurrentIndex(1)
        self.grid_layout.addLayout(self.stimulation_tree_window, 3, 0)

        self.signal_adjust_label = QLabel('Signal Adjust')
        self.signal_adjust_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.signal_adjust_label, 2, 1)


        self.signal_adjust_superposed = QStackedLayout()
        self.stimulation_edit_layout = QVBoxLayout()
        self.stimulation_edit_layout.setContentsMargins(0, 0, 0, 0)

        self.stimulation_name_label = QLabel("Stimulation Name")
        self.stimulation_name_cell = QLineEdit()
        self.stimulation_name_cell.textEdited.connect(self.name_to_tree)
        self.stimulation_name_window = QHBoxLayout()
        self.stimulation_name_window.addWidget(self.stimulation_name_label)
        self.stimulation_name_window.addWidget(self.stimulation_name_cell)
        self.stimulation_edit_layout.addLayout(self.stimulation_name_window)

        self.stimulation_type_label = QLabel("Stimulation Type")
        self.stimulation_type_cell = QComboBox()
        self.stimulation_type_cell.addItem("random-square")
        self.stimulation_type_cell.addItem("square")
        self.stimulation_type_cell.addItem("Third")
        self.stimulation_type_cell.currentIndexChanged.connect(self.type_to_tree)
        self.stimulation_type_window = QHBoxLayout()
        self.stimulation_type_window.addWidget(self.stimulation_type_label)
        self.stimulation_type_window.addWidget(self.stimulation_type_cell)
        self.stimulation_edit_layout.addLayout(self.stimulation_type_window)
        self.different_signals_window = QStackedLayout()

        

        self.first_signal_duration_window = QHBoxLayout()
        self.first_signal_type_duration_label = QLabel("Duration (s)")
        self.first_signal_duration_window.addWidget(self.first_signal_type_duration_label)
        self.first_signal_type_duration_cell = QLineEdit()
        self.first_signal_type_duration_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_duration_window.addWidget(self.first_signal_type_duration_cell)

        self.canal_window = QHBoxLayout()
        self.first_signal_first_canal_check = QCheckBox()
        self.first_signal_first_canal_check.stateChanged.connect(self.canals_to_tree)
        self.first_signal_first_canal_check.setText("Canal 1")
        self.canal_window.addWidget(self.first_signal_first_canal_check)
        self.first_signal_second_canal_check = QCheckBox()
        self.first_signal_second_canal_check.stateChanged.connect(self.canals_to_tree)
        self.first_signal_second_canal_check.setText("Canal 2")
        self.canal_window.addWidget(self.first_signal_second_canal_check)
        self.stimulation_edit_layout.addLayout(self.canal_window)

        self.first_signal_type_window = QVBoxLayout()
        self.first_signal_type_window.setAlignment(Qt.AlignLeft)
        self.first_signal_type_window.setAlignment(Qt.AlignTop)
        self.first_signal_type_window.setContentsMargins(0, 0, 0, 0)
        self.first_signal_type_container = QWidget()
        self.first_signal_type_container.setLayout(self.first_signal_type_window)
        self.stimulation_edit_layout.addLayout(self.first_signal_duration_window)
        #self.stimulation_edit_layout.addLayout(self.first_signal_duration_window)
        self.stimulation_edit_layout.addLayout(self.different_signals_window)


        

        self.first_signal_pulses_window = QHBoxLayout()
        self.first_signal_type_pulses_label = QLabel("Pulses")
        self.first_signal_pulses_window.addWidget(self.first_signal_type_pulses_label)
        self.first_signal_type_pulses_cell = QLineEdit()
        self.first_signal_type_pulses_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_pulses_window.addWidget(self.first_signal_type_pulses_cell)
        

        self.first_signal_jitter_window = QHBoxLayout()
        self.first_signal_type_jitter_label = QLabel("Jitter (s)")
        self.first_signal_jitter_window.addWidget(self.first_signal_type_jitter_label)
        self.first_signal_type_jitter_cell = QLineEdit()
        self.first_signal_type_jitter_cell.setText("0")
        self.first_signal_type_jitter_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_jitter_window.addWidget(self.first_signal_type_jitter_cell)

        self.first_signal_width_window = QHBoxLayout()
        self.first_signal_type_width_label = QLabel("Width (s)")
        self.first_signal_width_window.addWidget(self.first_signal_type_width_label)
        self.first_signal_type_width_cell = QLineEdit()
        self.first_signal_type_width_cell.setText("0")
        self.first_signal_type_width_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_width_window.addWidget(self.first_signal_type_width_cell)

        self.first_signal_type_window.addLayout(self.first_signal_duration_window)
        self.first_signal_type_window.addLayout(self.first_signal_pulses_window)
        self.first_signal_type_window.addLayout(self.first_signal_width_window)
        self.first_signal_type_window.addLayout(self.first_signal_jitter_window)
#-------------------

        self.second_signal_type_window = QVBoxLayout()
        self.second_signal_type_container = QWidget()
        self.second_signal_type_window.setAlignment(Qt.AlignLeft)
        self.second_signal_type_window.setAlignment(Qt.AlignTop)
        self.second_signal_type_window.setContentsMargins(0, 0, 0, 0)
        self.second_signal_type_container.setLayout(self.second_signal_type_window)
        self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.second_signal_frequency_window = QHBoxLayout()
        self.second_signal_type_frequency_label = QLabel("Frequency (Hz)")
        self.second_signal_frequency_window.addWidget(self.second_signal_type_frequency_label)
        self.second_signal_type_frequency_cell = QLineEdit()
        self.second_signal_type_frequency_cell.textEdited.connect(self.signal_to_tree)
        self.second_signal_frequency_window.addWidget(self.second_signal_type_frequency_cell)

        self.second_signal_duty_window = QHBoxLayout()
        self.second_signal_type_duty_label = QLabel("Duty (%)")
        self.second_signal_duty_window.addWidget(self.second_signal_type_duty_label)
        self.second_signal_type_duty_cell = QLineEdit()
        self.second_signal_type_duty_cell.textEdited.connect(self.signal_to_tree)
        self.second_signal_duty_window.addWidget(self.second_signal_type_duty_cell)

        self.second_signal_type_window.addLayout(self.second_signal_frequency_window)
        self.second_signal_type_window.addLayout(self.second_signal_duty_window)

#-------------------

        self.third_signal_type_window = QVBoxLayout()
        self.third_signal_type_container = QWidget()
        self.third_signal_type_container.setLayout(self.third_signal_type_window)
        self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.third_signal_type_name = QLabel("signal3")
        self.third_signal_type_window.addWidget(self.third_signal_type_name)

        self.different_signals_window.addWidget(self.first_signal_type_container)
        self.different_signals_window.addWidget(self.second_signal_type_container)
        self.different_signals_window.addWidget(self.third_signal_type_container)



        self.stimulation_edit_container = QWidget()
        self.stimulation_edit_container.setLayout(self.stimulation_edit_layout)
        self.block_edit_layout = QVBoxLayout()
        self.block_edit_layout.setContentsMargins(0, 0, 0, 0)
        self.block_edit_layout.setAlignment(Qt.AlignLeft)
        self.block_edit_layout.setAlignment(Qt.AlignTop)



        self.block_name_label = QLabel("Block Name")
        self.block_name_cell = QLineEdit()
        self.block_name_cell.textEdited.connect(self.name_to_tree)
        self.block_name_window = QHBoxLayout()
        self.block_name_window.addWidget(self.block_name_label)
        self.block_name_window.addWidget(self.block_name_cell)
        self.block_edit_layout.addLayout(self.block_name_window)

        self.block_iterations_window = QHBoxLayout()
        self.block_iterations_label = QLabel("Iterations")
        self.block_iterations_cell = QLineEdit()
        self.block_iterations_cell.textEdited.connect(self.block_to_tree)
        self.block_iterations_window.addWidget(self.block_iterations_label)
        self.block_iterations_window.addWidget(self.block_iterations_cell)
        self.block_edit_layout.addLayout(self.block_iterations_window)

        self.block_delay_window = QHBoxLayout()
        self.block_delay_label = QLabel("Delay")
        self.block_delay_cell = QLineEdit()
        self.block_delay_cell.textEdited.connect(self.block_to_tree)
        self.block_delay_window = QHBoxLayout()
        self.block_delay_window.addWidget(self.block_delay_label)
        self.block_delay_window.addWidget(self.block_delay_cell)
        self.block_edit_layout.addLayout(self.block_delay_window)

        self.block_jitter_window = QHBoxLayout()
        self.block_jitter_label = QLabel("Jitter")
        self.block_jitter_cell = QLineEdit()
        self.block_jitter_cell.textEdited.connect(self.block_to_tree)
        self.block_jitter_window = QHBoxLayout()
        self.block_jitter_window.addWidget(self.block_jitter_label)
        self.block_jitter_window.addWidget(self.block_jitter_cell)
        self.block_edit_layout.addLayout(self.block_jitter_window)

    



        self.block_edit_container = QWidget()
        self.block_edit_container.setLayout(self.block_edit_layout)
        self.signal_adjust_superposed.addWidget(self.stimulation_edit_container)
        self.signal_adjust_superposed.addWidget(self.block_edit_container)
        self.signal_adjust_superposed.addWidget(QLabel())
        self.signal_adjust_superposed.setCurrentIndex(2)
        self.grid_layout.addLayout(self.signal_adjust_superposed, 3, 1)

        

        self.signal_preview_label = QLabel('Signal Preview')
        self.signal_preview_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.signal_preview_label, 2, 2)

        self.buttons_main_window = QHBoxLayout()
        self.stop_button = QPushButton('Stop')
        self.stop_button.setIcon(QIcon("gui/icons/player-stop.png"))
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setEnabled(False)
        self.buttons_main_window.addWidget(self.stop_button)
        self.run_button = QPushButton('Run')
        self.run_button.setIcon(QIcon("gui/icons/player-play.png"))
        self.run_button.clicked.connect(self.run)
        self.run_button.setEnabled(False)
        self.buttons_main_window.addWidget(self.run_button)
        self.plot_window = PlotWindow()
        #self.plot_window.setFixedHeight(350)
        #self.plot_window.setFixedWidth(350)
        self.grid_layout.addWidget(self.plot_window, 3,2)
        self.grid_layout.addLayout(self.buttons_main_window, 4, 2)
        self.generate_daq()
        self.show()


    def run(self):
        self.deactivate_buttons()
        self.generate_daq()
        self.master_block = self.create_blocks()
        self.experiment = Experiment(self.master_block, int(self.framerate_cell.text()), int(self.exposure_cell.text()), self.mouse_id_cell.text(), self.directory_cell.text(), self.daq)
        self.open_start_experiment_thread()
    def generate_daq(self):
        self.lights =  [Instrument('port0/line3', 'ir'), Instrument('port0/line0', 'red'), Instrument('port0/line2', 'green'), Instrument('port0/line1', 'blue')]
        self.stimuli = [Instrument('ao1', 'air-pump')]
        self.camera =  Camera('img0', 'name')
        self.daq = DAQ('dev1',self.lights, self.stimuli, self.camera, int(self.framerate_cell.text()), int(self.exposure_cell.text()), self)


    def create_blocks(self, item=None):
        try: 
            if not item:
                item = self.stimulation_tree.currentItem()
            if item.childCount() > 0:
                children = []
                for index in range(item.childCount()):
                    child = item.child(index)
                    children.append(self.create_blocks(item=child))
                new_block = Block(item.text(0), children, delay=int(item.text(2)), iterations=int(item.text(1)))
                print(children)
                print(new_block.name)
                return new_block

                #create block with above child
            else:
                try:
                    pulses = int(item.text(5))
                    jitter = float(item.text(7))
                    width = float(item.text(8))
                except Exception:
                    pulses, jitter, width = 0, 0, 0
                try:
                    frequency = float(item.text(9))
                    duty = float(item.text(10))/100
                except Exception:
                    frequency, duty = 0, 0
                new_stim = Stimulation(
                    self.daq, int(item.text(6)), width=width, 
                    pulses=pulses, jitter=jitter, frequency=frequency,
                    duty=duty, delay=0, pulse_type=item.text(4), name=item.text(0))
                print(new_stim.name)
                return new_stim
        except Exception as err:
            print(err)
            pass

    def deactivate_buttons(self):
        self.stop_button.setEnabled(True)
        self.run_button.setEnabled(False)

        self.experiment_name_cell.setEnabled(False)
        self.mouse_id_cell.setEnabled(False)
        self.directory_save_files_checkbox.setEnabled(False)
        self.directory_choose_button.setEnabled(False)
        self.set_roi_button.setEnabled(False)
        self.experiment_name.setEnabled(False)
        self.mouse_id_label.setEnabled(False)
        self.framerate_label.setEnabled(False)
        self.framerate_cell.setEnabled(False)
        self.exposure_cell.setEnabled(False)
        self.exposure_label.setEnabled(False)
        self.add_brother_branch_button.setEnabled(False)
        self.add_child_branch_button.setEnabled(False)
        self.delete_branch_button.setEnabled(False)
        self.red_button.setEnabled(False)
        self.speckle_button.setEnabled(False)
        self.green_button.setEnabled(False)
        self.fluorescence_button.setEnabled(False)

        self.stimulation_name_label.setEnabled(False)
        self.stimulation_name_cell.setEnabled(False)
        self.stimulation_type_label.setEnabled(False)
        self.stimulation_type_cell.setEnabled(False)
        self.first_signal_first_canal_check.setEnabled(False)
        self.first_signal_second_canal_check.setEnabled(False)
        self.first_signal_type_duration_label.setEnabled(False)
        self.first_signal_type_duration_cell.setEnabled(False)
        self.first_signal_type_pulses_label.setEnabled(False)
        self.first_signal_type_pulses_cell.setEnabled(False)
        self.first_signal_type_width_label.setEnabled(False)
        self.first_signal_type_width_cell.setEnabled(False)
        self.first_signal_type_jitter_label.setEnabled(False)
        self.first_signal_type_jitter_cell.setEnabled(False)
        self.second_signal_type_frequency_label.setEnabled(False)
        self.second_signal_type_frequency_cell.setEnabled(False)
        self.second_signal_type_duty_label.setEnabled(False)
        self.second_signal_type_duty_cell.setEnabled(False)
        self.block_iterations_label.setEnabled(False)
        self.block_iterations_cell.setEnabled(False)
        self.block_delay_label.setEnabled(False)
        self.block_delay_cell.setEnabled(False)
        self.block_jitter_label.setEnabled(False)
        self.block_jitter_cell.setEnabled(False)
        self.block_name_label.setEnabled(False)
        self.block_name_cell.setEnabled(False)
        self.activate_live_preview_button.setEnabled(False)
        self.deactivate_live_preview_button.setEnabled(False)

    def stop(self):
        self.activate_buttons()
    
    
    def activate_buttons(self):
        self.stop_button.setEnabled(False)
        self.run_button.setEnabled(True)
        self.experiment_name_cell.setEnabled(True)
        self.mouse_id_cell.setEnabled(True)
        self.directory_save_files_checkbox.setEnabled(True)
        if self.directory_save_files_checkbox.isChecked():
            self.directory_choose_button.setEnabled(True)
        self.set_roi_button.setEnabled(True)
        self.experiment_name.setEnabled(True)
        self.mouse_id_label.setEnabled(True)
        self.framerate_label.setEnabled(True)
        self.framerate_cell.setEnabled(True)
        self.exposure_cell.setEnabled(True)
        self.exposure_label.setEnabled(True)
        self.add_brother_branch_button.setEnabled(True)
        self.add_child_branch_button.setEnabled(True)
        self.delete_branch_button.setEnabled(True)
        self.red_button.setEnabled(True)
        self.speckle_button.setEnabled(True)
        self.green_button.setEnabled(True)
        self.fluorescence_button.setEnabled(True)

        self.stimulation_name_label.setEnabled(True)
        self.stimulation_name_cell.setEnabled(True)
        self.stimulation_type_label.setEnabled(True)
        self.stimulation_type_cell.setEnabled(True)
        self.first_signal_first_canal_check.setEnabled(True)
        self.first_signal_second_canal_check.setEnabled(True)
        self.first_signal_type_duration_label.setEnabled(True)
        self.first_signal_type_duration_cell.setEnabled(True)
        self.first_signal_type_pulses_label.setEnabled(True)
        self.first_signal_type_pulses_cell.setEnabled(True)
        self.first_signal_type_width_label.setEnabled(True)
        self.first_signal_type_width_cell.setEnabled(True)
        self.first_signal_type_jitter_label.setEnabled(True)
        self.first_signal_type_jitter_cell.setEnabled(True)
        self.second_signal_type_frequency_label.setEnabled(True)
        self.second_signal_type_frequency_cell.setEnabled(True)
        self.second_signal_type_duty_label.setEnabled(True)
        self.second_signal_type_duty_cell.setEnabled(True)
        self.block_iterations_label.setEnabled(True)
        self.block_iterations_cell.setEnabled(True)
        self.block_delay_label.setEnabled(True)
        self.block_delay_cell.setEnabled(True)
        self.block_jitter_label.setEnabled(True)
        self.block_jitter_cell.setEnabled(True)
        self.block_name_label.setEnabled(True)
        self.block_name_cell.setEnabled(True)
        self.activate_live_preview_button.setEnabled(True)
        self.deactivate_live_preview_button.setEnabled(True)

    def choose_directory(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory_cell.setText(folder)

    def enable_directory(self):
        if self.directory_save_files_checkbox.isChecked():
            self.directory_choose_button.setDisabled(False)
            self.directory_cell.setDisabled(False)
        else:
            self.directory_choose_button.setDisabled(True)
            self.directory_cell.setDisabled(True)

    def delete_branch(self):
        try:
            root = self.stimulation_tree.invisibleRootItem()
            parent = self.stimulation_tree.currentItem().parent()
            if parent.childCount() == 1:
                parent.setIcon(0, QIcon("gui/icons/wave-square.png"))
            parent.removeChild(self.stimulation_tree.currentItem())
        except Exception:
            root.removeChild(self.stimulation_tree.currentItem())
            if root.childCount() == 0:
                self.run_button.setEnabled(False)
        
    
    def add_brother(self):
        if self.stimulation_tree.currentItem():
            stimulation_tree_item = QTreeWidgetItem()
            stimulation_tree_item.setText(0, "No Name")
            stimulation_tree_item.setForeground(0, QBrush(QColor(211,211,211)))
            stimulation_tree_item.setIcon(0, QIcon("gui/icons/wave-square.png"))
            parent = self.stimulation_tree.selectedItems()[0].parent()
            if parent:
                index = parent.indexOfChild(self.stimulation_tree.selectedItems()[0])
                parent.insertChild(index+1, stimulation_tree_item)
            else:
                self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
            self.type_to_tree(first = True)
            self.canals_to_tree(first=True)
        else:
            pass

    def add_child(self):
        if self.stimulation_tree.currentItem():
            self.stimulation_tree.currentItem().setIcon(0, QIcon("gui/icons/package.png"))
            self.stimulation_tree.currentItem().setText(1, "1")
            stimulation_tree_item = QTreeWidgetItem()
            stimulation_tree_item.setIcon(0, QIcon("gui/icons/wave-square.png"))
            stimulation_tree_item.setText(0,"No Name")
            stimulation_tree_item.setForeground(0, QBrush(QColor(211,211,211)))
            self.stimulation_tree.selectedItems()[0].addChild(stimulation_tree_item)
            self.stimulation_tree.selectedItems()[0].setExpanded(True)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
            self.type_to_tree(first = True)
            self.canals_to_tree(first=True)
        else:
            pass

    def first_stimulation(self):
        self.run_button.setEnabled(True)
        stimulation_tree_item = QTreeWidgetItem()
        stimulation_tree_item.setForeground(0, QBrush(QColor(211,211,211)))
        stimulation_tree_item.setIcon(0, QIcon("gui/icons/wave-square.png"))
        stimulation_tree_item.setText(0, "No Name")
        self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
        self.stimulation_tree_switch_window.setCurrentIndex(0)
        self.stimulation_tree.setCurrentItem(stimulation_tree_item)
        self.canals_to_tree(first=True)
        self.type_to_tree(first = True)


    def actualize_tree(self):
        if self.stimulation_tree.currentItem():
            self.stimulation_tree_switch_window.setCurrentIndex(0)
        else:
            self.stimulation_tree_switch_window.setCurrentIndex(1)
        try:
            if self.stimulation_tree.currentItem().childCount() > 0:
                self.signal_adjust_superposed.setCurrentIndex(1)
            else:
                self.signal_adjust_superposed.setCurrentIndex(0)
        except AttributeError:
            self.signal_adjust_superposed.setCurrentIndex(2)
        self.tree_to_name()
        self.tree_to_block()
        self.tree_to_type()
        self.tree_to_signal()
        self.tree_to_canal()
        self.plot()
        self.draw()

    def name_to_tree(self):
        branch = self.stimulation_tree.currentItem()
        branch.setForeground(0, QBrush(QColor(0, 0, 0)))
        if branch.childCount() > 0:
            branch.setText(0, self.block_name_cell.text())
        else:
            branch.setText(0, self.stimulation_name_cell.text())

    def tree_to_name(self):
        try:
            if self.stimulation_tree.currentItem().childCount() > 0:
                if self.stimulation_tree.currentItem().text(0) != "No Name":
                    self.block_name_cell.setText(self.stimulation_tree.currentItem().text(0))
                else:
                    self.block_name_cell.setText("")
            else:
                if self.stimulation_tree.currentItem().text(0) != "No Name":
                    self.stimulation_name_cell.setText(self.stimulation_tree.currentItem().text(0))
                else:
                    self.stimulation_name_cell.setText("")
        except AttributeError:
            pass
    
    def type_to_tree(self, first=False):
        if first is True:
            self.stimulation_type_cell.setCurrentIndex(0)
        self.different_signals_window.setCurrentIndex(self.stimulation_type_cell.currentIndex())
        try:
            self.stimulation_tree.currentItem().setText(4, str(self.stimulation_type_cell.currentText()))
            self.plot()
            self.draw()
        except Exception:
            pass

    def tree_to_type(self):
        dico = {
            "random-square": 0,
            "square": 1,
            "Third": 2
        }
        try:
            self.stimulation_type_cell.setCurrentIndex(dico[self.stimulation_tree.currentItem().text(4)])
        except Exception as err:
            self.stimulation_type_cell.setCurrentIndex(0)

    def signal_to_tree(self):
        self.stimulation_tree.currentItem().setText(5, self.first_signal_type_pulses_cell.text())
        self.stimulation_tree.currentItem().setText(6, self.first_signal_type_duration_cell.text())
        self.stimulation_tree.currentItem().setText(7, self.first_signal_type_jitter_cell.text())
        self.stimulation_tree.currentItem().setText(8, self.first_signal_type_width_cell.text())
        self.stimulation_tree.currentItem().setText(9, self.second_signal_type_frequency_cell.text())
        self.stimulation_tree.currentItem().setText(10, self.second_signal_type_duty_cell.text())
        self.plot()
        self.draw()

    def tree_to_signal(self):
        try:
            self.first_signal_type_pulses_cell.setText(self.stimulation_tree.currentItem().text(5))
            self.first_signal_type_duration_cell.setText(self.stimulation_tree.currentItem().text(6))
            self.first_signal_type_jitter_cell.setText(self.stimulation_tree.currentItem().text(7))
            self.first_signal_type_width_cell.setText(self.stimulation_tree.currentItem().text(8))
        except Exception:
            pass

    def tree_to_block(self):
        try:
            self.block_iterations_cell.setText(self.stimulation_tree.currentItem().text(1))
            self.block_delay_cell.setText(self.stimulation_tree.currentItem().text(2))
            self.block_jitter_cell.setText(self.stimulation_tree.currentItem().text(3))
        except Exception:
            pass

    def block_to_tree(self):
        self.stimulation_tree.currentItem().setText(1, self.block_iterations_cell.text())
        self.stimulation_tree.currentItem().setText(2, self.block_delay_cell.text())
        self.stimulation_tree.currentItem().setText(3, self.block_jitter_cell.text())
        self.plot()
        self.draw()

    def tree_to_canal(self):
        self.canal_running = True
        try:
            self.first_signal_first_canal_check.setChecked(self.boolean(self.stimulation_tree.currentItem().text(11)))
            self.first_signal_second_canal_check.setChecked(self.boolean(self.stimulation_tree.currentItem().text(12)))
        except Exception:
            pass
        self.canal_running = False

    def canals_to_tree(self, first=False):
        if self.canal_running is not True:
            if first is True:
                self.stimulation_tree.currentItem().setText(11, "False")
                self.stimulation_tree.currentItem().setText(12, "False")
            else:
                self.stimulation_tree.currentItem().setText(11, str(self.first_signal_first_canal_check.isChecked()))
                self.stimulation_tree.currentItem().setText(12, str(self.first_signal_second_canal_check.isChecked()))
            self.actualize_tree()

    def boolean(self, string):
        if string == "True":
            return True
        return False



    def plot(self, item = None):
        try: 
            if not item:
                item = self.stimulation_tree.currentItem()
            if item.childCount() > 0:
                for iteration in range(int(item.text(1))):
                    for index in range(item.childCount()):
                        child = item.child(index)
                        self.plot(child)
                        jitter = float(self.block_jitter_cell.text())
                        delay = round(float(self.block_delay_cell.text()) + random.random()*jitter, 3)
                        time_values = np.linspace(0, delay, int(round(delay))*300)
                        data  = np.zeros(len(time_values))
                        time_values += self.elapsed_time
                        self.plot_x_values = np.concatenate((self.plot_x_values, time_values))
                        self.plot_y_values = np.concatenate((self.plot_y_values, data))
                        self.elapsed_time += delay
            else:
                sign_type = item.text(4)
                duration = float(item.text(6))
                try:
                    pulses = int(item.text(5))
                    jitter = float(item.text(7))
                    width = float(item.text(8))
                except Exception:
                    pulses, jitter, width = 0, 0, 0
                try:
                    frequency = float(item.text(9))
                    duty = float(item.text(10))/100
                except Exception:
                    frequency, duty = 0, 0
                time_values = np.linspace(0, duration, int(round(duration))*300)
                data  = make_signal(time_values, sign_type, width, pulses, jitter, frequency, duty)
                if sign_type == "square":
                    data *= 5
                time_values += self.elapsed_time
                self.plot_x_values = np.concatenate((self.plot_x_values, time_values))
                self.plot_y_values = np.concatenate((self.plot_y_values, data))
                self.elapsed_time += duration
        except Exception as err:
            self.plot_x_values = []
            self.plot_y_values = []
            self.elapsed_time = 0

    def draw(self):
        new_x_values = []
        new_y_values = []
        try:
            sampling_indexes = np.linspace(0, len(self.plot_x_values)-1, 3000, dtype=int)
            new_x_values = np.take(self.plot_x_values, sampling_indexes, 0)
            new_y_values = np.take(self.plot_y_values, sampling_indexes, 0)
            self.plot_window.plot(new_x_values, new_y_values)

            self.plot_x_values = []
            self.plot_y_values = []
            self.elapsed_time = 0
        except Exception as err:
            pass

    def open_start_experiment_thread(self):
        self.start_experiment_thread =Thread(target=self.run_stimulation)
        self.start_experiment_thread.start()

    def run_stimulation(self):
        self.experiment.start()

    def open_live_preview_thread(self):
        self.live_preview_thread =Thread(target=self.start_live)
        self.live_preview_thread.start()

    def start_live(self):
        self.live_preview_buttons.setCurrentIndex(1)
        #self.plot_image = plt.imshow(self.numpy, interpolation="nearest")
        #self.plot_image.axes.get_xaxis().set_visible(False)
        #self.plot_image.axes.axes.get_yaxis().set_visible(False)
        plt.ion()
        self.video_running = True
        while self.video_running is True:
            try:
                self.plot_image.set_array(self.camera.frames[-1])
                time.sleep(1)
            except Exception as err:
                print(err)

    def update_preview(self, np_array):
        self.live_preview_buttons.setCurrentIndex(1)
        plt.ion()
        self.plot_image.set_array(np_array)



    def stop_live(self):
        self.live_preview_buttons.setCurrentIndex(0)
        self.video_running = False
    
    def set_roi(self):
        self.save_roi_button.setEnabled(False)
        self.roi_buttons.setCurrentIndex(1)
        def onselect_function(eclick, erelease):
            self.roi_extent = self.rect_selector.extents
            self.save_roi_button.setEnabled(True)

        self.rect_selector = RectangleSelector(self.plot_image.axes, onselect_function,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='pixels',
                                       interactive=True)

    def reset_roi(self):
        plt.xlim(0, 1024)
        plt.ylim(0,1024)
        self.reset_roi_button.setEnabled(False)

    def cancel_roi(self):
        self.roi_buttons.setCurrentIndex(0)
        self.rect_selector.clear()
        self.rect_selector = None

    def save_roi(self):
        self.roi_buttons.setCurrentIndex(0)
        plt.ion()
        plt.xlim(self.roi_extent[0], self.roi_extent[1])
        plt.ylim(self.roi_extent[2], self.roi_extent[3])
        self.rect_selector.clear()
        self.rect_selector = None
        self.reset_roi_button.setEnabled(True)


    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("IBM Plex Sans")
    app.setFont(font)
    ex = App()
    sys.exit(app.exec_())