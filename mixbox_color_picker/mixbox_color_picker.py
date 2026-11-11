from krita import *
from PyQt5.QtWidgets import *

from . import mixbox


def pick_color(color_tuple):
    v = Krita.instance().activeWindow().activeView()
    if v is not None:
        v.setForeGroundColor(ManagedColor.fromQColor(QColor(*color_tuple), v.canvas()))


# Krita 和 PyQt 有很多小驼峰，但 python 一般用 snake_case
# 纠结。。。总之能用 snake case 的还是用 snake case 吧
def get_foreground_color_tuple():
    v = Krita.instance().activeWindow().activeView()
    if v is not None:
        col = v.foregroundColor().colorForCanvas(v.canvas())
        return (col.red(), col.green(), col.blue())
    return (255, 0, 255)


class MyDocker(DockWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mixbox Color Picker")
        widget_main = QWidget(self)
        self.setWidget(widget_main)

        # 界面布局，一个选色渐变条 + 一左一右俩 button
        self.gradient_slider = GradientSlider(widget_main)

        button_group = QWidget(widget_main)
        button_group.setLayout(QHBoxLayout())

        button_set_color1 = QPushButton("Set Color 1", button_group)
        button_set_color1.clicked.connect(self.gradient_slider.set_color1)
        button_set_color2 = QPushButton("Set Color 2", button_group)
        button_set_color2.clicked.connect(self.gradient_slider.set_color2)

        button_group.layout().addWidget(button_set_color1)
        button_group.layout().addWidget(button_set_color2)
        button_group.layout().setContentsMargins(0, 0, 0, 0)

        widget_main.setLayout(QVBoxLayout())
        widget_main.layout().addWidget(self.gradient_slider)
        widget_main.layout().addWidget(button_group)

    def canvasChanged(self, canvas):
        pass


# 注册自定义窗口 MyDocker，必须写在 class 声明之后
Krita.instance().addDockWidgetFactory(
    DockWidgetFactory("mixbox_color_picker", DockWidgetFactoryBase.DockRight, MyDocker)
)


class GradientSlider(QWidget):

    def __init__(self, parent):
        super(GradientSlider, self).__init__(parent)
        self.t = 0
        self.color1 = (255, 255, 0)
        self.color2 = (0, 0, 255)
        self.update_cached_colors()

    def set_color1(self):
        self.color1 = get_foreground_color_tuple()
        self.update_cached_colors()
        self.update()

    def set_color2(self):
        self.color2 = get_foreground_color_tuple()
        self.update_cached_colors()
        self.update()

    # 缓存颜色值，避免重绘时重复调用 mixbox.lerp
    def update_cached_colors(self):
        self.cached_colors = [mixbox.lerp(self.color1, self.color2, i / 255.0) for i in range(256)]

    def get_color_from_cache(self, t):
        return self.cached_colors[round(t * 255)]

    def sizeHint(self):
        return QtCore.QSize(5000, 5000)

    def pick_mixed_color(self):
        rgb_mix = mixbox.lerp(self.color1, self.color2, self.t)
        pick_color(rgb_mix)

    # 鼠标事件，左键点击和左键移动的逻辑完全一样
    def mousePressEvent(self, event):
        self.handle_mouse(event)

    def mouseMoveEvent(self, event):
        self.handle_mouse(event)

    def handle_mouse(self, event):
        # 更新插值位置 t，调用选色，调用 update 重画
        if event.buttons() == QtCore.Qt.LeftButton:
            self.t = event.pos().x() / self.width()
            self.t = max(0, min(1, self.t))
            self.pick_mixed_color()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        ww = max(self.width(), 1.0)  # 因为要做除法，给个保底安全点
        hh = self.height()

        painter.setPen(QtCore.Qt.NoPen)
        # 左闭右开啊别忘了
        for x in range(ww + 1):
            t = float(x) / float(ww)
            color_tuple = self.get_color_from_cache(t)
            # 反色渲染当前指针位置
            if abs(self.t - t) <= 1.5 / ww:
                r, g, b = color_tuple
                color_tuple = (255 - r, 255 - g, 255 - b)
            # 再加一条更窄的白线
            if abs(self.t - t) <= 0.5 / ww:
                color_tuple = (255, 255, 255)
            painter.setBrush(QBrush(QColor(*color_tuple)))
            painter.drawRect(int(x), 0, 1, int(hh))
