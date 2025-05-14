from PyQt5 import QtWidgets, QtCore, QtGui
import os
import datetime

class BackupRestoreDialog(QtWidgets.QDialog):
    """시간표 및 설정 백업/복원 관리 대화상자"""
    
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.settings_manager = parent.settings_manager
        self.setWindowTitle("시간표 백업 및 복원")
        self.setMinimumSize(500, 400)
        
        self.setup_ui()
        self.load_backups()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QtWidgets.QVBoxLayout()
        
        # 안내 레이블
        info_label = QtWidgets.QLabel("시간표 데이터와 설정을 백업하거나 복원할 수 있습니다.")
        layout.addWidget(info_label)
        
        # 백업 목록 테이블
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["백업 이름", "생성일", "설명"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # 백업 버튼
        backup_layout = QtWidgets.QHBoxLayout()
        
        backup_name_label = QtWidgets.QLabel("백업 이름:")
        backup_layout.addWidget(backup_name_label)
        
        self.backup_name_edit = QtWidgets.QLineEdit()
        today = datetime.datetime.now().strftime("%Y%m%d")
        self.backup_name_edit.setText(f"Timetable_{today}")
        backup_layout.addWidget(self.backup_name_edit, 1)
        
        backup_btn = QtWidgets.QPushButton("백업 생성")
        backup_btn.clicked.connect(self.create_backup)
        backup_layout.addWidget(backup_btn)
        
        layout.addLayout(backup_layout)
        
        # 작업 버튼 영역
        btn_layout = QtWidgets.QHBoxLayout()
        
        restore_btn = QtWidgets.QPushButton("선택 백업 복원")
        restore_btn.clicked.connect(self.restore_selected)
        btn_layout.addWidget(restore_btn)
        
        delete_btn = QtWidgets.QPushButton("선택 백업 삭제")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)
        
        refresh_btn = QtWidgets.QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_backups)
        btn_layout.addWidget(refresh_btn)
        
        close_btn = QtWidgets.QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_backups(self):
        """백업 목록 불러오기"""
        backups = self.settings_manager.get_available_backups()
        
        # 테이블 초기화
        self.table.setRowCount(0)
        
        # 백업 목록 표시
        for i, backup in enumerate(backups):
            self.table.insertRow(i)
            
            # 백업 이름
            name_item = QtWidgets.QTableWidgetItem(backup["name"])
            self.table.setItem(i, 0, name_item)
            
            # 생성일
            created = backup.get("created")
            if created:
                created_str = created.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_str = "알 수 없음"
            created_item = QtWidgets.QTableWidgetItem(created_str)
            self.table.setItem(i, 1, created_item)
            
            # 설명
            desc_item = QtWidgets.QTableWidgetItem(backup.get("description", ""))
            self.table.setItem(i, 2, desc_item)
        
        # 칼럼 크기 조정
        self.table.resizeColumnsToContents()
        
        # 첫 번째 행 선택
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
    
    def create_backup(self):
        """새 백업 생성"""
        backup_name = self.backup_name_edit.text().strip()
        if not backup_name:
            QtWidgets.QMessageBox.warning(self, "알림", "백업 이름을 입력하세요.")
            return
        
        # 특수문자 제거
        import re
        backup_name = re.sub(r'[\\/*?:"<>|]', "_", backup_name)
        
        # 백업 생성
        success, message = self.settings_manager.create_backup(backup_name)
        
        if success:
            QtWidgets.QMessageBox.information(self, "백업 완료", f"백업이 생성되었습니다.\n{message}")
            self.load_backups()  # 목록 새로고침
        else:
            QtWidgets.QMessageBox.critical(self, "백업 실패", f"백업을 생성하지 못했습니다.\n{message}")
    
    def restore_selected(self):
        """선택된 백업 복원"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QtWidgets.QMessageBox.warning(self, "알림", "복원할 백업을 선택하세요.")
            return
        
        # 선택된 행의 백업 이름 가져오기
        row = selected_rows[0].row()
        backup_name = self.table.item(row, 0).text()
        
        # 복원 확인 대화상자
        reply = QtWidgets.QMessageBox.question(
            self, "백업 복원", 
            f"{backup_name} 백업을 복원하시겠습니까?\n\n현재 설정과 시간표가 모두 대체됩니다.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # 백업 복원
            success, message = self.settings_manager.restore_backup(backup_name)
            
            if success:
                QtWidgets.QMessageBox.information(self, "복원 완료", f"백업이 복원되었습니다.\n\n변경사항을 적용하려면 앱을 재시작하세요.")
                
                # 부모 위젯에 시간표 및 스타일 갱신 요청
                if hasattr(self.parent, "update_timetable_display"):
                    self.parent.update_timetable_display()
                if hasattr(self.parent, "update_styles"):
                    self.parent.update_styles()
                if hasattr(self.parent, "update_current_period"):
                    self.parent.update_current_period()
            else:
                QtWidgets.QMessageBox.critical(self, "복원 실패", f"백업을 복원하지 못했습니다.\n{message}")
    
    def delete_selected(self):
        """선택된 백업 삭제"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QtWidgets.QMessageBox.warning(self, "알림", "삭제할 백업을 선택하세요.")
            return
        
        # 선택된 행의 백업 이름 가져오기
        row = selected_rows[0].row()
        backup_name = self.table.item(row, 0).text()
        
        # 삭제 확인 대화상자
        reply = QtWidgets.QMessageBox.question(
            self, "백업 삭제", 
            f"{backup_name} 백업을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # 백업 폴더 경로 가져오기
            from utils.paths import get_data_directory
            backup_path = os.path.join(get_data_directory(), "backups", backup_name)
            
            try:
                # 폴더와 내용 삭제
                import shutil
                shutil.rmtree(backup_path)
                QtWidgets.QMessageBox.information(self, "삭제 완료", f"{backup_name} 백업이 삭제되었습니다.")
                self.load_backups()  # 목록 새로고침
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "삭제 실패", f"백업을 삭제하지 못했습니다.\n{str(e)}")
