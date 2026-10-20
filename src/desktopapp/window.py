"""Six explicit workflows, background workers and a complete diagnostic log."""
from datetime import datetime
import json
from pathlib import Path
import sys
import uuid
from PySide6 import QtCore, QtGui, QtWidgets as W
from . import VERSION
from . import jobs
from .paths import ROOT, data_root, load_settings, write_json


STYLE = '''
QWidget {font-family:"Segoe UI","PingFang SC","Microsoft YaHei";font-size:13px;color:#dbe3ee;background:#101823;}
QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox,QPlainTextEdit {background:#172433;border:1px solid #33475b;border-radius:6px;padding:7px;selection-background-color:#285e81;}
QPushButton {background:#243b50;border:1px solid #3d596e;border-radius:6px;padding:8px 13px;}
QPushButton:hover {background:#31516b;} QPushButton:disabled {color:#718094;background:#192431;}
QPushButton[primary="true"] {background:#137d81;border:1px solid #28adb1;color:white;}
QListWidget {background:#101c2a;border:0;padding:10px;} QListWidget::item {padding:16px 12px;border-radius:7px;}
QListWidget::item:selected {background:#224559;color:#8ce7dd;}
QGroupBox {border:1px solid #304155;border-radius:8px;margin-top:15px;padding:16px 11px 10px;}
QGroupBox::title {subcontrol-origin:margin;left:12px;padding:0 5px;color:#a9bdd0;}
QLabel[hint="true"] {color:#9aaec2;} QProgressBar {border:0;background:#203043;height:5px;} QProgressBar::chunk {background:#26b8a9;}
QCheckBox {spacing:8px;padding:5px 0;} QScrollArea {border:0;}
'''


class Window(W.QMainWindow):
    def __init__(self, *, demo=False):
        super().__init__()
        self.setWindowTitle('A7C II Tools · Desktop Preview')
        self.resize(1130, 850)
        self.setMinimumSize(960, 730)
        self.settings = load_settings()
        self.fields, self.buttons = {}, []
        self.current_job = None
        self.log_offset = 0
        self.process = None
        self.demo = demo
        self.camera_operation = False
        self.setStyleSheet(STYLE)
        central = W.QWidget()
        self.setCentralWidget(central)
        layout = W.QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        self.nav = W.QListWidget()
        self.nav.setFixedWidth(205)
        self.nav.addItems(['连接与驱动', '完整恢复', 'FL2 / FL3', '自定义创意外观', '竖屏显示', '电子快门声音'])
        layout.addWidget(self.nav)
        right = W.QVBoxLayout()
        right.setContentsMargins(22, 18, 22, 16)
        layout.addLayout(right, 1)
        heading = W.QHBoxLayout()
        title = W.QLabel('A7C II Tools')
        title.setStyleSheet('font-size:25px;font-weight:650;')
        heading.addWidget(title)
        heading.addStretch()
        heading.addWidget(W.QLabel('固件版本'))
        self.firmware = W.QComboBox()
        self.firmware.addItems(['2.01'])
        heading.addWidget(self.firmware)
        heading.addWidget(W.QLabel('实际电量'))
        self.battery = W.QSpinBox()
        self.battery.setRange(0, 100)
        self.battery.setSuffix(' %')
        heading.addWidget(self.battery)
        right.addLayout(heading)
        self.description = W.QLabel('Windows / macOS · 六个独立操作入口 · ' + VERSION)
        self.description.setProperty('hint', True)
        right.addWidget(self.description)
        self.pages = W.QStackedWidget()
        right.addWidget(self.pages, 1)
        self.connection_page()
        self.recovery_page()
        self.fl23_page()
        self.look_page()
        self.vertical_page()
        self.sound_page()
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)
        self.progress = W.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        right.addWidget(self.progress)
        self.status = W.QLabel('就绪。选择左侧功能；启动软件不会访问相机。')
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(180)
        self.log.setPlaceholderText('完整运行日志与原始报错会显示在这里。')
        right.addWidget(self.log)
        bottom = W.QHBoxLayout()
        open_log = W.QPushButton('打开任务目录')
        open_log.clicked.connect(self.open_job)
        bottom.addWidget(open_log)
        export = W.QPushButton('导出诊断包')
        export.clicked.connect(self.export_logs)
        bottom.addWidget(export)
        bottom.addStretch()
        self.stop = W.QPushButton('停止离线任务')
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self.cancel_offline)
        bottom.addWidget(self.stop)
        right.addLayout(bottom)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tail_log)
        self.timer.start(250)

    def page(self, title, detail):
        wrapper = W.QScrollArea()
        wrapper.setWidgetResizable(True)
        body = W.QWidget()
        layout = W.QVBoxLayout(body)
        layout.setContentsMargins(0, 8, 8, 8)
        label = W.QLabel(title)
        label.setStyleSheet('font-size:20px;font-weight:600;')
        layout.addWidget(label)
        hint = W.QLabel(detail)
        hint.setWordWrap(True)
        hint.setProperty('hint', True)
        layout.addWidget(hint)
        wrapper.setWidget(body)
        self.pages.addWidget(wrapper)
        return layout

    def box(self, layout, title):
        group = W.QGroupBox(title)
        form = W.QFormLayout(group)
        form.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
        layout.addWidget(group)
        return form

    def field(self, form, key, label, *, kind=None, filter='All files (*)', value=''):
        line = W.QLineEdit(str(self.settings.get(key, value)))
        line.setObjectName(key)
        self.fields[key] = line
        if kind:
            row = W.QHBoxLayout()
            row.addWidget(line, 1)
            button = W.QPushButton('选择…')
            button.clicked.connect(lambda: self.browse(line, kind, filter))
            row.addWidget(button)
            form.addRow(label, row)
        else:
            form.addRow(label, line)
        return line

    def browse(self, field, kind, filter):
        if kind == 'folder':
            path = W.QFileDialog.getExistingDirectory(self, '选择目录', field.text())
        elif kind == 'save':
            path = W.QFileDialog.getSaveFileName(self, '保存文件', field.text(), filter)[0]
        else:
            path = W.QFileDialog.getOpenFileName(self, '选择文件', field.text(), filter)[0]
        if path:
            field.setText(path)

    def button(self, layout, text, action, arguments=lambda: {}, *, primary=False):
        button = W.QPushButton(text)
        button.setObjectName('action_' + action)
        button.setProperty('primary', primary)
        button.clicked.connect(lambda: self.launch(action, arguments()))
        layout.addWidget(button)
        self.buttons.append(button)
        return button

    def text(self, key):
        return self.fields[key].text().strip()

    def common(self):
        return {'firmware': self.firmware.currentText(), 'battery': self.battery.value()}

    def work(self, label):
        return str(data_root() / 'work' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + label + '-' + uuid.uuid4().hex[:5]))

    def connection_page(self):
        layout = self.page('连接与驱动', '相机开机并选择“海量存储／Mass Storage”，使用可传数据的 USB 线。一次只连接一台相机。')
        form = self.box(layout, 'USB 连接')
        self.driver_identity = W.QComboBox()
        self.driver_identity.addItems(['普通连接 · 054C:0E8A', '服务连接 · 054C:0336'])
        form.addRow('驱动目标', self.driver_identity)
        if sys.platform == 'darwin':
            self.field(form, 'mac_volume', 'macOS 相机存储卷', kind='folder', value='/Volumes/')
        self.button(layout, '检测相机与驱动', 'driver_scan', primary=True)
        self.button(layout, '准备两阶段驱动并测试连接' if sys.platform == 'win32' else '准备 USB 服务连接', 'usb_prepare', primary=True)
        self.button(layout, '安装／保留可用驱动（Windows 管理员确认）' if sys.platform == 'win32'
                    else '检查 USB 访问（macOS 无需 Zadig）', 'driver_install',
                    lambda: {'pid': ['0e8a', '0336'][self.driver_identity.currentIndex()]})
        if sys.platform == 'darwin':
            self.button(layout, '推出选中的相机存储卷', 'mac_unmount', lambda: {'volume': self.text('mac_volume')})
        self.button(layout, '测试服务连接（不写固件）', 'connect')
        if sys.platform == 'win32':
            self.button(layout, '卸载相机驱动，恢复 Windows 默认连接', 'driver_uninstall',
                        lambda: {'pids': ['0e8a', '0336']})
        hint = W.QLabel('连接中断后先查看完整日志。报错不会触发重新刷写或自动重装驱动。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()

    def recovery_page(self):
        layout = self.page('完整恢复', '选择这台机身的首次备份，将程序和项目设置恢复到该备份时间点。后续安装 FL23、外观或声音不要求按顺序卸载。')
        form = self.box(layout, '恢复来源')
        self.field(form, 'restore_backup', '备份目录', kind='folder')
        choose_zip = W.QPushButton('或选择完整备份 ZIP…')
        choose_zip.clicked.connect(lambda: self.browse(self.fields['restore_backup'], 'file', 'Backup (*.zip);;All files (*)'))
        form.addRow('', choose_zip)
        self.field(form, 'restore_work', '恢复任务目录', kind='folder', value=self.work('recovery'))
        self.button(layout, '检查所选备份（离线）', 'backup_inspect', lambda: {'backup': self.text('restore_backup')})
        auto = W.QPushButton('一键还原：查找并使用最初完整备份')
        auto.setObjectName('one_click_restore')
        auto.clicked.connect(self.one_click_restore)
        self.buttons.append(auto)
        layout.addWidget(auto)
        self.button(layout, '恢复所选备份并完整读回', 'restore', lambda: dict(self.common(),
            backup=self.text('restore_backup'), workspace=self.text('restore_work')), primary=True)
        self.recovery_accept = W.QCheckBox('恢复后已完整断电重开，确认取景、拍照和回放正常')
        layout.addWidget(self.recovery_accept)
        self.button(layout, '核对恢复后加载状态', 'restore_verify', lambda: {
            'workspace': self.text('restore_work'), 'accepted': self.recovery_accept.isChecked()})
        note = W.QLabel('相机需要仍可进入服务通信。此入口使用机身备份；不把官方 BODYDATA.DAT 当作备份刷入。')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def fl23_page(self):
        layout = self.page('FL2 / FL3', '备份 → 安装 → 完整读回 → 断电重开 → 核对。使用已合并 PR 的曲线／色彩数据，保留独立恢复入口。')
        form = self.box(layout, '本次 FL23 任务')
        self.field(form, 'fl23_work', '工作目录', kind='folder', value=self.work('fl23'))
        self.field(form, 'fl23_backup', '第二份备份目录', kind='folder', value=str(data_root() / 'backups' / uuid.uuid4().hex[:8]))
        args = lambda: dict(self.common(), workspace=self.text('fl23_work'), backup=self.text('fl23_backup'))
        self.button(layout, '1  备份与准备', 'fl23_prepare', args)
        self.button(layout, '2  安装 FL2 / FL3', 'fl23_install', args, primary=True)
        self.button(layout, '3  重开后核对', 'fl23_verify', args)
        layout.addStretch()

    def look_page(self):
        layout = self.page('自定义创意外观', '选择编译好的 .a7look，指定自订栏位 1–6。恢复单槽保留其他栏位和 FL2／FL3。')
        form = self.box(layout, '导入到相机')
        self.field(form, 'look_file', 'A7Look 文件', kind='file', filter='A7Look (*.a7look)')
        self.field(form, 'look_name', '机内名称')
        self.look_slot = W.QSpinBox()
        self.look_slot.setRange(1, 6)
        form.addRow('自订栏位', self.look_slot)
        self.field(form, 'look_work', '当前外观任务', kind='folder', value=self.work('look'))
        self.field(form, 'look_backup', '备份目录', kind='folder', value=str(data_root() / 'look-backups'))
        fresh = W.QPushButton('新建外观任务（保留旧任务）')
        fresh.clicked.connect(lambda: (self.fields['look_work'].setText(self.work('look')), self.look_accept.setChecked(False)))
        self.buttons.append(fresh)
        layout.addWidget(fresh)
        args = lambda: dict(self.common(), look=self.text('look_file'), name=self.text('look_name'),
            slot=self.look_slot.value(), workspace=self.text('look_work'), backup=self.text('look_backup'))
        row = W.QHBoxLayout()
        layout.addLayout(row)
        self.button(row, '1  备份与准备', 'look_prepare', args)
        self.button(row, '2  写入所选栏位', 'look_install', args, primary=True)
        self.look_accept = W.QCheckBox('已断电重开，确认预览、拍照和回放正常')
        layout.addWidget(self.look_accept)
        self.button(layout, '核对加载状态', 'look_verify', lambda: dict(args(), accepted=self.look_accept.isChecked()))
        self.button(layout, '恢复这个任务写入前的单个栏位', 'look_restore', args)
        tools = W.QHBoxLayout()
        layout.addLayout(tools)
        compiler = W.QPushButton('生成 A7Look…')
        compiler.clicked.connect(self.compiler_dialog)
        tools.addWidget(compiler)
        self.buttons.append(compiler)
        plugin = W.QPushButton('安装 LrC 自动识别插件…')
        plugin.clicked.connect(self.plugin_dialog)
        tools.addWidget(plugin)
        self.buttons.append(plugin)
        layout.addStretch()

    def vertical_page(self):
        layout = self.page('竖屏显示', '竖握相机时，拍摄信息、图标和布局跟随转向，对照 Sony 原生 Vertical Display。当前版本开启本次运行状态。')
        form = self.box(layout, '显示任务')
        self.field(form, 'vertical_work', '任务目录', kind='folder', value=str(data_root() / 'vertical'))
        args = lambda: dict(self.common(), workspace=self.text('vertical_work'))
        self.button(layout, '读取当前显示状态', 'vertical_status', args)
        self.button(layout, '开启竖屏显示', 'vertical_enable', args, primary=True)
        self.button(layout, '关闭竖屏显示', 'vertical_disable', args)
        self.button(layout, '撤销竖屏资源别名', 'vertical_remove', args)
        layout.addWidget(W.QLabel('开启完成后拔 USB、保持开机，分别检查左右竖握。重新加载后可能需要再次开启。'))
        layout.addStretch()

    def sound_page(self):
        layout = self.page('电子快门声音', '独立开关控制电子快门发声分支。自定义音频先转换、临时试听，再保存已确认的同一份声音。')
        form = self.box(layout, '声音工作区')
        self.field(form, 'sound_work', '工作目录', kind='folder', value=str(data_root() / 'sound'))
        self.field(form, 'sound_backup', '第二份备份', kind='folder', value=str(data_root() / 'sound-backup'))
        args = lambda: dict(self.common(), workspace=self.text('sound_work'), backup=self.text('sound_backup'))
        row = W.QHBoxLayout()
        layout.addLayout(row)
        self.button(row, '开启电子快门声', 'sound_on', args)
        self.button(row, '关闭电子快门声', 'sound_off', args)
        media = self.box(layout, '导入音频／视频片段')
        self.field(media, 'sound_source', '声音文件', kind='file', filter='Audio / video (*.wav *.mp3 *.mp4 *.m4a *.flac *.ogg);;All files (*)')
        self.sound_start = W.QDoubleSpinBox()
        self.sound_start.setRange(0, 86400)
        self.sound_start.setDecimals(3)
        media.addRow('起点（秒）', self.sound_start)
        self.sound_duration = W.QDoubleSpinBox()
        self.sound_duration.setRange(.01, 2)
        self.sound_duration.setDecimals(3)
        self.sound_duration.setValue(.15)
        media.addRow('长度（秒）', self.sound_duration)
        row = W.QHBoxLayout()
        layout.addLayout(row)
        self.button(row, '转换所选片段', 'sound_import', lambda: dict(args(), source=self.text('sound_source'),
            start=self.sound_start.value(), duration=self.sound_duration.value(), peak=.4))
        self.button(row, '相机内临时试听', 'sound_audition', args)
        self.button(layout, '确认试听正确', 'sound_confirm', lambda: dict(args(), result='correct'))
        self.button(layout, '已断电恢复原声，记录恢复完成', 'sound_confirm_recovery', args)
        self.button(layout, '保存确认的自定义声音', 'sound_install', args, primary=True)
        self.sound_accept = W.QCheckBox('保存后已断电重开，声音正确且拍摄／回放正常')
        layout.addWidget(self.sound_accept)
        self.button(layout, '重开后核对声音', 'sound_verify', lambda: dict(args(), accepted=self.sound_accept.isChecked()))
        self.button(layout, '恢复原厂音效', 'sound_restore_sound', args)
        layout.addStretch()

    def compiler_dialog(self):
        dialog = W.QDialog(self)
        dialog.setWindowTitle('生成 A7Look')
        dialog.resize(760, 370)
        layout = W.QVBoxLayout(dialog)
        hint = W.QLabel('DCP 使用 Lightroom 实际显影，需在显影配置中设置 Lightroom 桥接命令；CUBE 须明确为 Sony ST / sRGB 输入与 sRGB 输出。生成文件不连接相机。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = self.box(layout, '源文件与输出')
        self.field(form, 'compile_source', 'DCP / CUBE', kind='file', filter='Reference (*.dcp *.cube)')
        self.field(form, 'compile_name', '外观名称')
        self.field(form, 'compile_output', '输出 A7Look', kind='save', filter='A7Look (*.a7look)')
        self.field(form, 'compile_model', '响应文件', kind='file', filter='Response (*.npz)',
                   value=str(ROOT / 'calibration/a7c2-2.01.virtual.npz'))
        self.field(form, 'renderer_config', '显影配置（DCP 使用）', kind='file', filter='JSON (*.json)',
                   value=str(data_root() / 'a7look-compiler.local.json'))
        run = W.QPushButton('开始生成')
        run.clicked.connect(lambda: (dialog.accept(), self.launch('compile_look', {
            'source': self.text('compile_source'), 'name': self.text('compile_name'),
            'output': self.text('compile_output'), 'model': self.text('compile_model'),
            'renderer_config': self.text('renderer_config'), 'input_space': 'sony-st-srgb', 'passes': 3})))
        layout.addWidget(run)
        dialog.exec()

    def plugin_dialog(self):
        executable = ROOT / ('desktop-assets/exiftool/exiftool.exe' if sys.platform == 'win32' else 'desktop-assets/exiftool/exiftool')
        path = str(executable) if executable.exists() else W.QFileDialog.getOpenFileName(self, '选择 ExifTool')[0]
        if path:
            self.launch('plugin_install', {'exiftool': path})

    def one_click_restore(self):
        roots = [str(data_root() / 'backups'), str(data_root() / 'initial-checkpoints')]
        for key in ('fl23_backup', 'look_backup', 'restore_backup'):
            if self.text(key):
                roots.append(self.text(key))
        self.fields['restore_work'].setText(self.work('recovery'))
        self.launch('restore_auto', dict(self.common(), roots=roots, workspace=self.text('restore_work')))

    def launch(self, action, arguments):
        if self.process is not None:
            return
        if action == 'driver_uninstall':
            answer = W.QMessageBox.question(self, '卸载相机驱动',
                '将备份并卸载 Sony 054C:0E8A／0336 的第三方驱动，让 Windows 重新识别相机。\n'
                '完成后可能需要拔插 USB，重新选择海量存储模式。此操作不修改相机固件。\n现在卸载？',
                W.QMessageBox.Yes | W.QMessageBox.Cancel, W.QMessageBox.Cancel)
            if answer != W.QMessageBox.Yes:
                return
        writing = action in {'restore', 'restore_auto', 'fl23_install', 'look_install', 'look_restore',
                              'vertical_enable', 'vertical_disable', 'vertical_remove',
                              'sound_on', 'sound_off', 'sound_audition', 'sound_install', 'sound_restore_sound'}
        if writing and self.battery.value() < 50:
            W.QMessageBox.information(self, '填写实际电量', '请先填写相机实际电量；写入至少需要 50%。')
            return
        if writing:
            target = ('自动选择已连接机身最早可用的完整备份' if action == 'restore_auto' else
                      arguments.get('backup') if action == 'restore' else arguments.get('look') or arguments.get('workspace'))
            answer = W.QMessageBox.question(self, '开始相机写入',
                '目标：' + str(target) + '\n写入和完整读回期间保持相机开机、USB 连接。现在开始？',
                W.QMessageBox.Yes | W.QMessageBox.Cancel, W.QMessageBox.Cancel)
            if answer != W.QMessageBox.Yes:
                return
        for key, field in self.fields.items():
            self.settings[key] = field.text()
        write_json(data_root() / 'desktop.json', self.settings)
        self.current_job = jobs.new_job(action, arguments)
        self.log_offset = 0
        self.log.clear()
        self.camera_operation = action in jobs.CAMERA_ACTIONS or action == 'driver_install'
        for button in self.buttons:
            button.setEnabled(False)
        self.stop.setEnabled(not self.camera_operation)
        self.progress.setRange(0, 0)
        self.status.setText('正在执行：' + action + '。详细日志持续保存。')
        self.process = QtCore.QProcess(self)
        self.process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONUTF8', '1')
        env.insert('PYTHONIOENCODING', 'utf-8')
        self.process.setProcessEnvironment(env)
        command = jobs.worker_command(self.current_job / 'request.private.json')
        self.process.readyReadStandardOutput.connect(self.process_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start(command[0], command[1:])

    def process_output(self):
        text = bytes(self.process.readAllStandardOutput()).decode('utf-8', errors='replace')
        if text:
            with (self.current_job / 'process.log').open('a', encoding='utf-8') as stream:
                stream.write(text)
            self.log.appendPlainText(text.rstrip())

    def tail_log(self):
        if not self.current_job:
            return
        path = self.current_job / 'worker.log'
        if path.exists():
            with path.open('rb') as stream:
                stream.seek(self.log_offset)
                text = stream.read()
                self.log_offset = stream.tell()
            if text:
                self.log.appendPlainText(text.decode('utf-8', errors='replace').rstrip())

    def finished(self, code, exit_status):
        self.tail_log()
        status_path = self.current_job / 'status.private.json'
        status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
        success = code == 0 and status.get('phase') == 'SUCCEEDED'
        if success and status.get('action') == 'restore_auto':
            self.fields['restore_backup'].setText(status['result']['backup'])
            self.fields['restore_work'].setText(status['result']['workspace'])
        if success and status.get('action') == 'look_restore':
            self.fields['look_work'].setText(status['result']['workspace'])
        for key, field in self.fields.items():
            self.settings[key] = field.text()
        write_json(data_root() / 'desktop.json', self.settings)
        self.status.setText('完成。请按日志提示进行下一步。' if success else
                           '操作停止：' + status.get('error', '进程异常退出，退出码 ' + str(code)) + '。请导出诊断包。')
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if success else 0)
        for button in self.buttons:
            button.setEnabled(True)
        self.stop.setEnabled(False)
        self.process.deleteLater()
        self.process = None

    def process_error(self, error):
        if self.process and error == QtCore.QProcess.FailedToStart:
            self.log.appendPlainText(self.process.errorString())
            self.finished(-1, None)

    def open_job(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.current_job or data_root())))

    def export_logs(self):
        if not self.current_job:
            return
        path = W.QFileDialog.getSaveFileName(self, '导出诊断包', 'a7c2-diagnostics.zip', 'ZIP (*.zip)')[0]
        if path:
            try:
                jobs.export_support(self.current_job, path)
            except Exception as exc:
                W.QMessageBox.warning(self, '导出失败', str(exc))

    def cancel_offline(self):
        if self.process and not self.camera_operation:
            self.process.terminate()

    def closeEvent(self, event):
        if self.process:
            W.QMessageBox.information(self, '任务仍在运行', '请等待当前任务结束后关闭。相机写入期间不要结束程序或拔线。')
            event.ignore()
        else:
            event.accept()


def main():
    app = W.QApplication.instance() or W.QApplication(sys.argv)
    if '--smoke-test' in sys.argv and sys.platform == 'win32':
        # Qt's headless test platform does not enumerate Windows system fonts.
        import os
        font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyh.ttc'
        if font.is_file():
            QtGui.QFontDatabase.addApplicationFont(str(font))
    app.setApplicationName('A7C2Tools')
    app.setOrganizationName('QAQLeonard')
    window = Window()
    window.show()
    if '--smoke-test' in sys.argv:
        data_root().mkdir(parents=True, exist_ok=True)
        for index in range(window.pages.count()):
            window.nav.setCurrentRow(index)
            app.processEvents()
            if not window.grab().save(str(data_root() / ('desktop-page-' + str(index + 1) + '.png'))):
                raise OSError('Could not save desktop smoke screenshot')
        window.nav.setCurrentRow(0)
        QtCore.QTimer.singleShot(800, app.quit)
    return app.exec()
