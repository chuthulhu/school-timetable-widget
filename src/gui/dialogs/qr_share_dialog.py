from PyQt5 import QtWidgets, QtCore, QtGui
import json
import base64
import qrcode
import io
from PIL import Image

class QRShareDialog(QtWidgets.QDialog):
    """시간표 QR코드 공유 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.settings_manager = parent.settings_manager
        self.setWindowTitle("시간표 QR코드 공유")
        self.setMinimumSize(400, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QtWidgets.QVBoxLayout()
        
        # 안내 텍스트
        info_label = QtWidgets.QLabel("QR코드를 스캔하여 시간표를 다른 기기와 공유할 수 있습니다.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # QR코드 표시 영역
        self.qr_label = QtWidgets.QLabel()
        self.qr_label.setAlignment(QtCore.Qt.AlignCenter)
        self.qr_label.setMinimumSize(300, 300)
        self.qr_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        layout.addWidget(self.qr_label)
        
        # 공유 옵션
        options_group = QtWidgets.QGroupBox("공유 옵션")
        options_layout = QtWidgets.QVBoxLayout()
        
        self.share_timetable = QtWidgets.QCheckBox("시간표 데이터")
        self.share_timetable.setChecked(True)
        options_layout.addWidget(self.share_timetable)
        
        self.share_time_settings = QtWidgets.QCheckBox("교시 시간 설정")
        self.share_time_settings.setChecked(True)
        options_layout.addWidget(self.share_time_settings)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 버튼 영역
        buttons_layout = QtWidgets.QHBoxLayout()
        
        generate_btn = QtWidgets.QPushButton("QR코드 생성")
        generate_btn.clicked.connect(self.generate_qr_code)
        buttons_layout.addWidget(generate_btn)
        
        save_btn = QtWidgets.QPushButton("QR코드 저장")
        save_btn.clicked.connect(self.save_qr_code)
        buttons_layout.addWidget(save_btn)
        
        close_btn = QtWidgets.QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # 초기 QR코드 생성
        QtCore.QTimer.singleShot(100, self.generate_qr_code)
    
    def generate_qr_code(self):
        """선택된 옵션에 따라 QR코드 생성"""
        try:
            # 공유할 데이터 준비
            share_data = {}
            
            if self.share_timetable.isChecked():
                share_data["timetable"] = self.settings_manager.timetable_data
            
            if self.share_time_settings.isChecked():
                # 교시별 시간 데이터는 문자열로 변환
                time_settings = {}
                for period, time_range in self.settings_manager.time_ranges.items():
                    time_settings[str(period)] = {
                        "start": time_range["start"].toString("HH:mm"),
                        "end": time_range["end"].toString("HH:mm")
                    }
                share_data["time_settings"] = time_settings
            
            # 데이터가 없으면 오류 표시
            if not share_data:
                QtWidgets.QMessageBox.warning(self, "오류", "공유할 데이터를 선택하세요.")
                return
            
            # 데이터를 JSON 문자열로 변환하고 Base64 인코딩
            data_str = json.dumps(share_data, ensure_ascii=False)
            data_b64 = base64.b64encode(data_str.encode('utf-8')).decode('ascii')
            
            # QR코드 생성
            qr = qrcode.QRCode(
                version=None,  # 자동 크기 조정
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(data_b64)
            qr.make(fit=True)
            
            # PIL 이미지로 생성
            img = qr.make_image(fill_color="black", back_color="white")
            
            # PIL 이미지를 QPixmap으로 변환
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(img_bytes.getvalue())
            
            # 레이블에 표시
            if pixmap.width() > self.qr_label.width() or pixmap.height() > self.qr_label.height():
                pixmap = pixmap.scaled(
                    self.qr_label.width(), 
                    self.qr_label.height(),
                    QtCore.Qt.KeepAspectRatio, 
                    QtCore.Qt.SmoothTransformation
                )
            
            self.qr_label.setPixmap(pixmap)
            
            # QR 코드 이미지 저장
            self.qr_image = img
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"QR코드 생성 실패: {str(e)}")
    
    def save_qr_code(self):
        """생성된 QR코드를 파일로 저장"""
        if not hasattr(self, 'qr_image'):
            QtWidgets.QMessageBox.warning(self, "알림", "먼저 QR코드를 생성해야 합니다.")
            return
        
        # 파일 저장 대화상자
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "QR코드 저장", "", "PNG 이미지 (*.png)"
        )
        
        if file_path:
            try:
                if not file_path.lower().endswith('.png'):
                    file_path += '.png'
                self.qr_image.save(file_path)
                QtWidgets.QMessageBox.information(self, "저장 완료", f"QR코드를 저장했습니다.\n{file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "저장 실패", f"QR코드 저장 중 오류가 발생했습니다.\n{str(e)}")
    
    def resizeEvent(self, event):
        """크기 변경 시 QR코드 다시 표시"""
        super().resizeEvent(event)
        if hasattr(self, 'qr_image'):
            self.generate_qr_code()
