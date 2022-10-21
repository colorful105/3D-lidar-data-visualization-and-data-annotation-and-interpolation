import numpy as np
import sys
from PyQt5.QtWidgets import *
import vispy.scene
from vispy import scene
from vispy.scene import visuals
from vispy import color
import open3d

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        global canvas, view, grid
        self.flag = 1
        canvas = vispy.scene.SceneCanvas()
        view = canvas.central_widget.add_view()
        grid = visuals.GridLines(parent=view.scene)

        view.add(grid)
        view.camera = 'turntable'

        button = QPushButton('Open File')
        button.clicked.connect(self.openfile)
        vbox = QVBoxLayout()
        vbox.addWidget(canvas.native)
        vbox.addWidget(button)
        self.setLayout(vbox)
        self.setWindowTitle('project')
        self.setGeometry(1000, 207, 800, 600)
        view.camera.center = (0, 0, 0)
        self.show()
        self.meshes = []
        xyztext = "X: 0.000000 Y: 0.000000 Z: 0.000000"
        self.text = visuals.Text(xyztext, color='white', anchor_x='left', parent=view, pos=(20, 30))
        canvas.events.key_press.connect(self.on_button_press)
        canvas.events.mouse_move.connect(self.on_mouse_move)
        canvas.events.mouse_press.connect(self.on_mouse_press)
        canvas.events.mouse_move.disconnect(self.on_mouse_press)
    def openfile(self):
        self.file=QFileDialog.getOpenFileName(self, 'Open file', './')
        self.object = self.EditVisual()
        view.camera.distance = abs(self.data).max() * 2.5
        self.meshes.append([self.data])
        self.update()

    def on_button_press(self, event):

        if event.key == 'f': # camera scene fix
            view.camera.interactive = not view.camera.interactive

            if view.camera.interactive == 0:
                canvas.events.mouse_move.connect(self.on_mouse_press)
            else:
                canvas.events.mouse_move.disconnect(self.on_mouse_press)
    def EditVisual(self):
        global ids, kwargs, colors
        pcd = open3d.io.read_point_cloud(self.file[0])
        self.size = 0.1
        self.data = np.asarray(pcd.points)
        cmap = color.get_colormap('viridis')
        colors = np.concatenate(list(map(cmap.map, np.linspace(0, 1, len(self.data)))))
        self.sphere = visuals.Markers(scaling=True, parent=view.scene)
        self.sphere.transform = scene.transforms.STTransform(scale=(1, 1, 1))
        kwargs = dict(symbol='o', size=self.size, edge_width = 0, edge_color=None)
        ids = np.arange(1, len(self.data) + 1, dtype=np.uint32).view(np.uint8)
        ids = ids.reshape(-1, 4)
        ids = np.divide(ids, 255, dtype=np.float32)
        self.sphere.set_data(self.data, face_color=colors, **kwargs)

        return self.sphere

    def detect_idx(self):
        click_radius = self.size/2
        self.sphere.update_gl_state(blend=False)
        self.sphere.antialias = 0
        self.sphere.set_data(self.data, face_color=ids, **kwargs)
        self.img = canvas.render((pos_press[0] - click_radius,
                             pos_press[1] - click_radius,
                             click_radius * 2 + 1,
                             click_radius * 2 + 1),
                            bgcolor=(0, 0, 0, 0))
        self.sphere.update_gl_state(blend=True)
        self.sphere.set_data(self.data, face_color=colors, **kwargs)
        idxs = self.img.ravel().view(np.uint32)
        idx = idxs[len(idxs) // 2]

        if idx == 0:
            idxs, counts = np.unique(idxs, return_counts=True)
            idxs = idxs[np.argsort(counts)]
            idx = idxs[-1] or (len(idxs) > 1 and idxs[-2])
        if idx > 0:
            self.on_click(idx - 1, self.sphere)
            print('data coordinates :', self.data[idx])

    def on_mouse_press(self, event):
        global pos_press
        pos_press = canvas.transforms.canvas_transform.map(event.pos)
        if event.button == 1:
            self.detect_idx()

    def on_click(self, idx, markers):
        colors[idx] = (1, 1, 1, 1)

        markers.set_data(self.data, face_color=colors, symbol='o', size=self.size, edge_width=0, edge_color=None)
    def on_mouse_move(self, event):
        global x, y, z
        tr = canvas.scene.node_transform(view.scene)
        scene_coords = tr.map(event.pos)
        scene_coords /= scene_coords[-1]
        x, y, z, w = scene_coords
        self.text.text = f"X: {x:0.06f} Y: {y:0.06f} Z: {z:0.06f}"
        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    app.exec_()
