from PyQt5 import QtWidgets, QtCore, QtGui
import json
import base64
import os
import io
import tempfile
import sys
import numpy as np  # numpy 추가

class ImportDialog(QtWidgets.QDialog):
    """시간표 가져오기 대화상자"""
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.settings_manager = parent.settings_manager
        self.setWindowTitle("시간표 가져오기")
        self.setMinimumSize(500, 400)
        
        # 카메라 및 QR 관련 변수 초기화
        self.camera = None
        self.timer = QtCore.QTimer()
        self.imported_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QtWidgets.QVBoxLayout()
        
        # 탭 위젯
        self.tabs = QtWidgets.QTabWidget()
        
        # QR 코드 탭
        qr_tab = QtWidgets.QWidget()
        qr_layout = QtWidgets.QVBoxLayout()
        
        qr_info = QtWidgets.QLabel("카메라로 QR코드를 스캔하거나 QR코드 이미지를 불러올 수 있습니다.")
        qr_info.setWordWrap(True)
        qr_layout.addWidget(qr_info)
        
        # 카메라 뷰
        self.camera_view = QtWidgets.QLabel("카메라를 활성화하려면 '카메라 시작' 버튼을 누르세요.")
        self.camera_view.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_view.setMinimumSize(320, 240)
        self.camera_view.setStyleSheet("background-color: #222; color: white; border: 1px solid #444;")
        qr_layout.addWidget(self.camera_view)
        
        # 카메라 제어 버튼
        camera_btn_layout = QtWidgets.QHBoxLayout()
        
        self.camera_start_btn = QtWidgets.QPushButton("카메라 시작")
        self.camera_start_btn.clicked.connect(self.start_camera)
        camera_btn_layout.addWidget(self.camera_start_btn)
        
        self.camera_stop_btn = QtWidgets.QPushButton("카메라 중지")
        self.camera_stop_btn.clicked.connect(self.stop_camera)
        self.camera_stop_btn.setEnabled(False)
        camera_btn_layout.addWidget(self.camera_stop_btn)
        
        load_qr_btn = QtWidgets.QPushButton("QR코드 파일 열기")
        load_qr_btn.clicked.connect(self.open_qr_image)
        camera_btn_layout.addWidget(load_qr_btn)
        
        qr_layout.addLayout(camera_btn_layout)
        qr_tab.setLayout(qr_layout)
        
        # 파일 탭
        file_tab = QtWidgets.QWidget()
        file_layout = QtWidgets.QVBoxLayout()
        
        file_info = QtWidgets.QLabel("JSON 파일에서 시간표와 설정을 가져올 수 있습니다.")
        file_info.setWordWrap(True)
        file_layout.addWidget(file_info)
        
        # 파일 선택 버튼
        file_btn_layout = QtWidgets.QHBoxLayout()
        load_file_btn = QtWidgets.QPushButton("JSON 파일 열기")
        load_file_btn.clicked.connect(self.open_json_file)
        file_btn_layout.addWidget(load_file_btn)
        file_layout.addLayout(file_btn_layout)
        
        file_layout.addStretch(1)
        file_tab.setLayout(file_layout)
        
        # 탭 추가
        self.tabs.addTab(qr_tab, "QR코드 스캔")
        self.tabs.addTab(file_tab, "파일에서 가져오기")
        
        layout.addWidget(self.tabs)
        
        # 가져오기 결과 표시 영역
        result_group = QtWidgets.QGroupBox("가져오기 결과")
        result_layout = QtWidgets.QVBoxLayout()
        
        self.result_text = QtWidgets.QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 버튼 영역
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.import_btn = QtWidgets.QPushButton("시간표에 적용")
        self.import_btn.clicked.connect(self.apply_imported_data)
        self.import_btn.setEnabled(False)
        buttons_layout.addWidget(self.import_btn)
        
        close_btn = QtWidgets.QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
    def start_camera(self):
        """카메라 시작"""
        # OpenCV 모듈 로딩 확인
        try:
            import cv2
            from pyzbar.pyzbar import decode
            
            # 카메라 초기화
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QtWidgets.QMessageBox.warning(self, "오류", "카메라를 열 수 없습니다.")
                return
            
            # 타이머 연결 (프레임 캡처용)
            self.timer.timeout.connect(lambda: self.update_frame(cv2, decode))
            self.timer.start(100)  # 100ms = 10fps
            
            # 버튼 상태 변경
            self.camera_start_btn.setEnabled(False)
            self.camera_stop_btn.setEnabled(True)
            
        except ImportError:
            QtWidgets.QMessageBox.warning(
                self, 
                "모듈 오류", 
                "카메라 기능을 사용하려면 OpenCV와 pyzbar 모듈이 필요합니다.\n"
                "pip install opencv-python pyzbar 명령으로 설치하세요."
            )
    
    def stop_camera(self):
        """카메라 중지"""
        # 타이머 중지
        if self.timer.isActive():
            self.timer.stop()
        
        # 카메라 해제
        if hasattr(self, 'camera') and self.camera:
            self.camera.release()
            self.camera = None
        
        # 버튼 상태 변경
        self.camera_start_btn.setEnabled(True)
        self.camera_stop_btn.setEnabled(False)
        
        # 카메라 뷰 초기 상태로 복원
        self.camera_view.setText("카메라를 활성화하려면 '카메라 시작' 버튼을 누르세요.")
        
    def update_frame(self, cv2, decode_func):
        """카메라 프레임 업데이트 및 QR 코드 스캔"""
        if not self.camera:
            return
            
        ret, frame = self.camera.read()
        if not ret:
            return
            
        # 이미지 처리
        try:
            # 그레이스케일로 변환 (QR 코드 인식을 위해)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # QR 코드 인식 시도
            decoded_objects = decode_func(gray)
            
            # QR 코드 발견
            for obj in decoded_objects:
                # QR 코드 위치 표시
                pts = obj.polygon
                if len(pts) > 4:
                    hull = cv2.convexHull(np.array([pt for pt in pts]))  # np 사용
                    cv2.polylines(frame, [hull], True, (0, 255, 0), 3)
                else:
                    for j in range(4):
                        cv2.line(frame, pts[j], pts[(j+1) % 4], (0, 255, 0), 3)
                
                # QR 코드 데이터 처리
                self.process_qr_data(obj.data)
                
                # 타이머 정지 (QR 코드를 인식했으므로 더 이상 스캔할 필요 없음)
                self.timer.stop()
            
            # 이미지를 Qt 포맷으로 변환
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
            
            # 적절한 크기로 조정
            qt_image = qt_image.scaled(self.camera_view.width(), self.camera_view.height(), 
                                      QtCore.Qt.KeepAspectRatio)
            
            # 화면에 표시
            self.camera_view.setPixmap(QtGui.QPixmap.fromImage(qt_image))
            
        except Exception as e:
            print(f"프레임 처리 중 오류: {str(e)}")
    
    def process_qr_data(self, data):
        """QR 코드에서 추출한 데이터 처리"""
        try:
            # Base64 디코딩
            data_str = base64.b64decode(data).decode('utf-8')
            
            # JSON 파싱
            imported_data = json.loads(data_str)
            
            # 결과 저장
            self.imported_data = imported_data
            
            # 결과 표시
            self.display_imported_data()
            
        except Exception as e:
            self.result_text.setText(f"QR 코드 데이터 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def open_qr_image(self):
        """QR 코드 이미지 파일 열기"""
        try:
            from pyzbar.pyzbar import decode
            from PIL import Image
            
            # 파일 선택 대화상자
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "QR 코드 이미지 열기", "", "이미지 파일 (*.png *.jpg *.jpeg *.bmp)"
            )
            
            if not file_path:
                return
                
            # 이미지 로드 및 QR코드 디코딩
            image = Image.open(file_path)
            decoded_objects = decode(image)
            
            # QR 코드를 찾았는지 확인
            if decoded_objects:
                # 첫 번째 QR 코드 데이터 사용
                self.process_qr_data(decoded_objects[0].data)
            else:
                self.result_text.setText("선택한 이미지에서 QR 코드를 찾을 수 없습니다.")
                
        except ImportError:
            QtWidgets.QMessageBox.warning(
                self, 
                "모듈 오류", 
                "QR 코드 이미지 처리를 위해 pyzbar와 PIL 모듈이 필요합니다.\n"
                "pip install pyzbar pillow 명령으로 설치하세요."
            )
        except Exception as e:
            self.result_text.setText(f"QR 코드 이미지 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def open_json_file(self):
        """JSON 파일 열기"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "JSON 파일 열기", "", "JSON 파일 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.imported_data = json.load(f)
                
            # 결과 표시
            self.display_imported_data()
            
        except Exception as e:
            self.result_text.setText(f"JSON 파일 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def display_imported_data(self):
        """가져온 데이터 내용 표시"""
        if not self.imported_data:
            self.result_text.setText("가져온 데이터가 없습니다.")
            self.import_btn.setEnabled(False)
            return
        
        result = "가져온 데이터:\n\n"
        
        # 시간표 데이터
        if "timetable" in self.imported_data:
            timetable = self.imported_data["timetable"]
            result += "■ 시간표 데이터\n"
            for day in ["월", "화", "수", "목", "금"]:
                if day in timetable:
                    result += f"  {day}요일: "
                    periods = []
                    for period, subject in timetable[day].items():
                        if subject:  # 내용이 있는 경우만 표시
                            periods.append(f"{period}교시({subject})")
                    result += ", ".join(periods) + "\n"
            result += "\n"
        
        # 시간 설정
        if "time_settings" in self.imported_data:
            time_settings = self.imported_data["time_settings"]
            result += "■ 교시별 시간 설정\n"
            for period, times in sorted(time_settings.items(), key=lambda x: int(x[0])):
                result += f"  {period}교시: {times['start']} ~ {times['end']}\n"
        
        self.result_text.setText(result)
        self.import_btn.setEnabled(True)
    
    def apply_imported_data(self):
        """가져온 데이터를 현재 설정에 적용"""
        if not self.imported_data:
            return
            
        # 적용할 데이터 선택 대화상자
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("가져오기 옵션")
        layout = QtWidgets.QVBoxLayout()
        
        # 시간표 데이터 옵션
        timetable_check = QtWidgets.QCheckBox("시간표 데이터")
        timetable_check.setEnabled("timetable" in self.imported_data)
        timetable_check.setChecked(timetable_check.isEnabled())
        layout.addWidget(timetable_check)
        
        # 시간 설정 옵션
        time_settings_check = QtWidgets.QCheckBox("교시별 시간 설정")
        time_settings_check.setEnabled("time_settings" in self.imported_data)
        time_settings_check.setChecked(time_settings_check.isEnabled())
        layout.addWidget(time_settings_check)
        
        # 경고 메시지
        warning_label = QtWidgets.QLabel("경고: 선택한 데이터는 현재 설정을 덮어씁니다.")
        warning_label.setStyleSheet("color: red;")
        layout.addWidget(warning_label)
        
        # 버튼
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        # 대화상자 실행
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        
        # 선택된 데이터 적용
        applied = False
        
        # 시간표 데이터 적용
        if timetable_check.isChecked() and "timetable" in self.imported_data:
            self.settings_manager.update_timetable_data(self.imported_data["timetable"])
            applied = True
        
        # 시간 설정 적용
        if time_settings_check.isChecked() and "time_settings" in self.imported_data:
            time_settings = self.imported_data["time_settings"]
            
            # QTime 객체로 변환
            for period, times in time_settings.items():
                period = int(period)
                start_hour, start_min = map(int, times["start"].split(':'))
                end_hour, end_min = map(int, times["end"].split(':'))
                
                self.settings_manager.time_ranges[period] = {
                    "start": QtCore.QTime(start_hour, start_min),
                    "end": QtCore.QTime(end_hour, end_min)
                }
            
            # 설정 저장
            self.settings_manager.save_time_settings()
            applied = True
        
        # 부모 위젯에 변경사항 반영
        if applied:
            if hasattr(self.parent, "update_timetable_display"):
                self.parent.update_timetable_display()
            if hasattr(self.parent, "update_current_period"):
                self.parent.update_current_period()
                
            QtWidgets.QMessageBox.information(
                self, 
                "가져오기 완료", 
                "선택한 데이터가 성공적으로 적용되었습니다."
            )
            
    def closeEvent(self, event):
        """대화상자 닫힐 때 호출"""
        # 카메라 정리
        self.stop_camera()
        super().closeEvent(event)
