import sys

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDir
from PyQt5.QtGui import QPixmap, QPalette, QImage, QPainter, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QGridLayout, QScrollArea, QPushButton, QDialog, \
    QLineEdit, QFileDialog, QMessageBox, QDialogButtonBox, QListWidget, QListWidgetItem, QTextEdit, QHBoxLayout
from models import Place, session, Item


# 场景组件：1.渲染场景的名字，图片，包含物品个数
#          2.对鼠标点击作出反应，弹出该场景的详细内容
class PlaceWidget(QWidget):
    def __init__(self, place, parent):
        super().__init__()
        self.parent = parent
        self.place = place
        # 场景图片
        label_image = QLabel(self)
        pixmap = QPixmap(place.image).scaled(200, 200)
        label_image.setPixmap(pixmap)
        # 场景名字
        label_name = QLabel(self)
        label_name.setText(place.name)
        # 包含物品个数
        self.label_count = QLabel(self)
        self.label_count.setText("{}个物品".format(len(place.items)))

        # 将上面三个内容垂直布局
        vbox = QVBoxLayout()
        vbox.addWidget(label_image)
        vbox.addWidget(label_name)
        vbox.addWidget(self.label_count)
        self.setLayout(vbox)

    # 对鼠标点击事件作出反应，弹出详细信息对话框
    def mousePressEvent(self, event):
        dialog = AddItemDialog(self, self.place)
        dialog.exec_()
        self.parent.flush_count()

    # 刷新物品数目
    def flush(self):
        self.label_count.setText("{}个物品".format(len(self.place.items)))


# 场景列表：包含所有的场景
class PlaceListWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.set_grid()

    # 将所有场景进行网格布局
    def set_grid(self):
        grid = QGridLayout()
        places = session.query(Place)
        # 每行放置2个，计算需要的行数，最后需要有一个"添加"按钮
        # 所以总数是场景个数+1
        row_count = (places.count() + 1) // 2 + 1
        # 实例化所有场景组件
        self.widgets = [PlaceWidget(place, self) for place in places]
        # 将"添加场景"按钮加到场景列表中
        self.widgets.append(AddPlaceWidget(self))
        # 每个场景组件的具体位置
        positions = [(i, j) for i in range(row_count) for j in range(2)]
        positions = positions[:places.count() + 1]
        # 将所有场景组件加到网格布局中
        for position, widget in zip(positions, self.widgets):
            grid.addWidget(widget, *position)
        # 设置布局
        self.setLayout(grid)

    # 刷新场景列表（添加/删除场景后）
    def flush(self):
        self.layout().setEnabled(False)
        QWidget().setLayout(self.layout())
        self.set_grid()
        self.repaint()

    # 刷新所有场景组件中的物品计数（用于添加/移动/删除物品）
    def flush_count(self):
        for widget in self.widgets:
            widget.flush()


# 添加新场景组件
# 其实就是一个按钮，会对鼠标点击作出反应，弹出对话框
# 下面内容和PlaceWidget类似，不再赘述
class AddPlaceWidget(QWidget):
    def __init__(self, widget_list):
        super().__init__()
        self.widget_list = widget_list
        add_button = QPushButton('新增', self)
        add_button.setFixedSize(200, 200)
        label_name = QLabel(self)
        label_name.setText('')
        label_count = QLabel(self)
        label_count.setText('')

        vbox = QVBoxLayout()
        vbox.addWidget(add_button)
        vbox.addWidget(label_name)
        vbox.addWidget(label_count)
        self.setLayout(vbox)

        # 将鼠标点击事件关联到add_place方法
        add_button.clicked.connect(self.add_place)

    # 添加场景
    def add_place(self):
        # 弹出对话框添加场景
        dialog = AddPlaceDialog(self)
        result = dialog.exec_()
        # 将结果保存到数据库并刷新场景列表
        if result:
            place = Place(name=dialog.name, image=dialog.image)
            session.add(place)
            session.commit()
            self.widget_list.flush()

    # 接口兼容
    def flush(self):
        pass


# 添加新场景对话框
# 用于添加新场景
class AddPlaceDialog(QDialog):
    def __init__(self, parent):
        super(AddPlaceDialog, self).__init__(parent)
        self.parent = parent

        # 选择照片
        self.button = QPushButton('选择照片')
        self.button.clicked.connect(self.open)
        # 显示照片
        self.image_label = QLabel()
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setFixedSize(200, 200)

        # 场景名称
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText('为区域命名，如书房，客厅...')

        # 确定/取消按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok |
                                           QDialogButtonBox.Cancel)

        # 确定后的行为（执行submit方法）
        self.button_box.accepted.connect(self.submit)
        # 取消后的行为（返回）
        self.button_box.rejected.connect(self.reject)

        # 将上面几个组件垂直布局
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(self.button)
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.line_edit)
        vbox.addWidget(self.button_box)

        self.image = None
        self.name = None

    # 添加照片的具体方法
    def open(self):
        # 弹出选择对话框
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                  QDir.currentPath())
        # 判断用户选择的照片是否合法并作出提示
        if fileName:
            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self, "",
                                        "无法加载图片:%s." % fileName)
                return
            else:
                self.image = fileName

            # 设置显示照片预览
            self.image_label.setPixmap(QPixmap.fromImage(image).scaled(200, 200))
            self.scaleFactor = 1.0

    # 提交对话框
    def submit(self):
        self.name = self.line_edit.text().strip()
        if not self.name or not self.image:
            QMessageBox.information(self, "",
                                    "必须指定图片和名称！")
            return
        else:
            self.accept()


# 用于显示一个场景中的所有物品位置
# 可以对鼠标点击作出反应，在点击处添加物品
class ImageLabel(QLabel):
    def __init__(self, parent, place):
        super().__init__(parent)
        self.parent = parent
        # 设置显示区域大小
        self.setFixedSize(400, 400)
        self.setPixmap(QPixmap(place.image).scaled(400, 400))
        self.item_buttons = []
        # 绘制所有已经存在的物品
        self.drawItems()

    # 鼠标点击事件：弹出添加物品的对话框
    def mouseReleaseEvent(self, event):
        dialog = EditItem(self.parent, event=event)
        result = dialog.exec_()
        # 更新场景信息（如物品数量）
        session.add(self.parent.place)
        session.commit()

    # 重新绘制所有物品
    def flush(self):
        self.drawItems()

    # 绘制物品
    def drawItems(self):
        for item in self.parent.items:
            self.add_button(item)

    # 添加新的物品，每个物品用一个按钮表示，点击该按钮
    # 会弹出物品的详细信息
    def add_button(self, item):
        button = self.create_button(item)
        button.setVisible(True)
        self.item_buttons.append(button)

    def create_button(self, item):
        button = QPushButton('', self)
        # 设置物品按钮的颜色大小
        button.setStyleSheet("background-color: yellow")
        button.setGeometry(item.x, item.y, 10, 10)
        # 按钮提示信息显示物品名字
        button.setToolTip(item.name)
        # 按钮和物品进行关联，简化编程实现
        button.item = item
        item.button = button
        # 对物品点击进行响应
        button.clicked.connect(self.make_edit_item(button))
        return button

    # 对物品点击的响应是创建一个新的对话框
    # 在该对话框中可以编辑信息/移动/删除
    def make_edit_item(self, button):
        def edit_item():
            dialog = EditItem(self.parent, button.item)
            result = dialog.exec_()

        return edit_item


# 添加物品/物品编辑对话框
class EditItem(QDialog):
    # 如果item为None则为添加新的物品
    # item不为None则是编辑已经存在的物品
    def __init__(self, parent, item=None, event=None):
        super().__init__(parent)

        self.parent = parent
        self.item = item
        self.event = event
        # 物品名称和详细信息
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText('输入物品名称')
        self.textedit = QTextEdit(self)

        # 显示信息
        if self.item is None:
            self.line_edit.setText('')
            self.textedit.setText('')
        else:
            self.line_edit.setText(self.item.name)
            self.textedit.setText(self.item.description)

        self.delete_button = QPushButton("删除", self)
        self.move_button = QPushButton("移动", self)

        # 删除和移动按钮水平布局
        hbox = QHBoxLayout()
        hbox.addWidget(self.delete_button)
        hbox.addWidget(self.move_button)

        # 关联具体的方法
        self.delete_button.clicked.connect(self.delete)
        self.move_button.clicked.connect(self.move)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok |
                                           QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.submit)
        self.button_box.rejected.connect(self.reject)

        # 将上面的组件进行垂直布局
        vbox = QVBoxLayout()
        vbox.addWidget(self.line_edit)
        vbox.addWidget(self.textedit)
        vbox.addLayout(hbox)
        vbox.addWidget(self.button_box)
        self.setLayout(vbox)

        # 如果是添加物品则金庸删除和移动按钮
        if item is None:
            self.delete_button.setEnabled(False)
            self.move_button.setEnabled(False)

    # 删除操作
    def delete(self):
        if not self.item:
            return
        self.item.button.setVisible(False)
        self.parent.items.remove(self.item)
        # 刷新显示
        self.parent.flush()
        # 更新数据库
        session.delete(self.item)
        session.commit()
        self.accept()

    # 移动操作
    def move(self):
        self.item.button.setVisible(False)
        a = self.item
        # 在对话中选择移动的目的地和位置
        dialog = MovePlaceListDialog(self, self.item)
        result = dialog.exec_()

        # 移动成功则对当前显示进行刷新
        if result:
            print(a == self.item)
            self.item.button.setVisible(False)

            if self.parent.place == self.item.place:
                self.parent.flush()
                self.parent.image_label.flush()
            else:
                self.parent.items.remove(self.item)
                self.parent.flush()
            self.accept()
        else:
            self.item.button.setVisible(True)

    def submit(self):
        if not self.line_edit.text():
            QMessageBox.information(self, "",
                                    "必须指定名称！")
            return
        else:
            if self.item is None:
                self.item = Item(name='', description='',
                                 x=self.event.x(), y=self.event.y(),
                                 place=self.parent.place)
            self.item.name = self.line_edit.text()
            self.item.description = self.textedit.toPlainText()
            session.add(self.item)
            session.commit()
            print(self.item, self.parent.items)
            if self.item not in self.parent.items:
                self.parent.items.append(self.item)
                self.parent.image_label.add_button(self.item)
            self.parent.flush()
            self.accept()


# 移动到的场景
class MovePlaceWidget(PlaceWidget):
    def __init__(self, place, item, parent):
        super().__init__(place, parent)
        self.parent = parent
        self.place = place
        self.item = item

    def mousePressEvent(self, event):
        dialog = MoveItemDialog(self, self.place, self.item)
        result = dialog.exec_()
        if result:
            self.parent.accept()
        self.flush()


# 移动到的具体位置
class MoveItemDialog(QDialog):
    def __init__(self, parent, place, item):
        super().__init__(parent)
        self.parent = parent
        self.item = item
        self.place = place
        self.items = list(place.items)
        self.text_label = QLabel(self)
        self.text_label.setText("请点击要将item移动到的位置")
        self.image_label = ImageLabel(self, place)
        self.image_label.mouseReleaseEvent = self.mouseReleaseEvent_new

        vbox = QVBoxLayout()
        vbox.addWidget(self.text_label)
        vbox.addWidget(self.image_label)
        self.setLayout(vbox)

    def mouseReleaseEvent_new(self, event):
        self.item.place = self.place
        # self.item.button.hide()
        self.item.x = event.x()
        self.item.y = event.y()
        # self.image_label.add_button(self.item)
        session.add(self.item)
        session.commit()
        QMessageBox.information(self, "",
                                "移动成功！")
        self.accept()

    def flush(self):
        pass


# 所有可移动到的场景列表
class MovePlaceListDialog(QDialog):
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item

        label = QLabel("请选择要移动到的地方")
        grid = self.get_grid()
        widget = QWidget(self)
        widget.setLayout(grid)
        scrollArea = QScrollArea(self)
        scrollArea.setWidget(widget)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(scrollArea)
        self.setLayout(vbox)

    def get_grid(self):
        grid = QGridLayout()
        places = session.query(Place)
        row_count = (places.count()) // 2 + 1
        widgets = [MovePlaceWidget(place, self.item, self) for place in places]
        positions = [(i, j) for i in range(row_count) for j in range(2)]
        positions = positions[:places.count()]
        for position, widget in zip(positions, widgets):
            grid.addWidget(widget, *position)
        return grid

    def flush_count(self):
        for widget in self.widgets:
            widget.flush()


# 添加新的物品
class AddItemDialog(QDialog):
    def __init__(self, parent, place, item=None):
        super().__init__(parent)
        self.place = place
        self.items = list(place.items)
        self.image_label = ImageLabel(self, place)
        # 在当前场景搜索
        self.search_line = QLineEdit(self)
        self.search_line.setPlaceholderText('搜索')
        self.search_line.textChanged.connect(self.search)
        self.listwidget = QListWidget(self)
        self.populate_list(self.listwidget, None)
        self.listwidget.itemClicked.connect(self.on_listwidget_clicked)
        self.listwidget.itemDoubleClicked.connect(
            self.on_listwidget_doubleClicked
        )

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.search_line)
        vbox.addWidget(self.listwidget)
        self.setLayout(vbox)

        if item:
            for item0 in self.items:
                if item0.id == item.id:
                    item0.button.setStyleSheet("background-color: green")
                    break
            for i in range(self.listwidget.count()):
                if self.listwidget.item(i).item.id == item.id:
                    self.listwidget.setCurrentRow(i)
                    break

    # 每当搜索框中内容改变时候就刷新物品列表
    # 搜索框为空则显示全部
    def search(self):
        text = self.search_line.text().strip()
        if not text:
            self.flush()
        else:
            results = []
            for item in self.items:
                if text in item.name:
                    results.append(item)
            self.flush(results)

    # 刷新列表
    def flush(self, items=None):
        self.listwidget.clear()
        self.populate_list(self.listwidget, items)
        self.repaint()

    # 填充列表
    def populate_list(self, listwidget, items):
        if items is None:
            items = self.items
        for item in items:
            list_item = QListWidgetItem(item.name)
            list_item.item = item
            listwidget.addItem(list_item)

    # 列表中的项目被点击时在场景图片中以绿色标记出物品
    def on_listwidget_clicked(self, listitem):
        for button in self.image_label.item_buttons:
            button.setStyleSheet("background-color: yellow")
        print(listitem.item.button)
        button = QPushButton("", self.image_label)

        listitem.item.button.setStyleSheet("background-color: green")

    # 双击则弹出详细信息对话框
    def on_listwidget_doubleClicked(self, listitem):
        dialog = EditItem(self, listitem.item)
        result = dialog.exec_()


# 搜索框，全局搜索物品
class SearchWidget(QWidget):
    def __init__(self, placelist):
        super().__init__()
        self.placelist = placelist
        self.items = list(session.query(Item))

        self.search_line = QLineEdit(self)
        self.search_line.setPlaceholderText('搜索')
        self.search_line.textChanged.connect(self.search)
        self.listwidget = QListWidget(self)
        self.listwidget.itemClicked.connect(self.on_listwidget_clicked)
        self.listwidget.itemDoubleClicked.connect(
            self.on_listwidget_doubleClicked
        )

        vbox = QVBoxLayout()
        vbox.addWidget(self.search_line)
        vbox.addWidget(self.listwidget)
        self.setLayout(vbox)

    def search(self):
        text = self.search_line.text().strip()
        results = []
        if not text:
            pass
        else:
            for item in self.items:
                if text in item.name:
                    results.append(item)
        self.flush(results)

    def flush(self, items):
        self.listwidget.clear()
        self.populate_list(self.listwidget, items)
        self.repaint()

    def populate_list(self, listwidget, items):
        for item in items:
            list_item = QListWidgetItem(item.name + "({})".format(item.place.name))
            list_item.item = item
            listwidget.addItem(list_item)

    def on_listwidget_clicked(self, listitem):
        dialog = AddItemDialog(self, listitem.item.place, listitem.item)
        dialog.exec_()
        self.placelist.flush_count()

    def on_listwidget_doubleClicked(self, listitem):
        dialog = EditItem(self, listitem.item)
        result = dialog.exec_()


# 初始界面
class Main(QWidget):
    def __init__(self):
        super().__init__()
        placelist = PlaceListWidget()
        searchwidget = SearchWidget(placelist)

        # scrollArea0.setBackgroundRole(QPalette.Dark)

        scrollArea = QScrollArea()
        # scrollArea.setBackgroundRole(QPalette.Dark)
        scrollArea.setWidget(placelist)

        vbox = QVBoxLayout()
        vbox.addWidget(searchwidget)
        vbox.addWidget(scrollArea)
        self.setLayout(vbox)


if __name__ == '__main__':
    app = QApplication([])
    main = Main()
    main.show()

    sys.exit(app.exec_())
