import sys
import os
import shutil
from datetime import datetime
import fitz  # PyMuPDF
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QFileDialog, QMessageBox)

class PDFRenamerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file_paths = []
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.setWindowTitle('PTNT PDF 분류기')
        self.resize(550, 400)

        layout = QVBoxLayout()
        
        # 파일 목록 리스트박스
        self.listbox = QListWidget()
        self.listbox.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.listbox)

        # 버튼 레이아웃
        btn_layout = QHBoxLayout()
        
        self.btn_open = QPushButton('파일 오픈 (Open)')
        self.btn_open.setFixedHeight(40)
        self.btn_open.clicked.connect(self.open_files)
        btn_layout.addWidget(self.btn_open)
        
        self.btn_rename = QPushButton('이름 변환 (Rename)')
        self.btn_rename.setFixedHeight(40)
        self.btn_rename.clicked.connect(self.process_files)
        btn_layout.addWidget(self.btn_rename)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # 드래그 앤 드롭 이벤트 처리
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.add_file(file_path)

    # 파일 열기 버튼 클릭 이벤트
    def open_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "PDF 파일 선택", "", "PDF Files (*.pdf)")
        for f in files:
            self.add_file(f)

    def add_file(self, file_path):
        if file_path not in self.file_paths:
            self.file_paths.append(file_path)
            self.listbox.addItem(os.path.basename(file_path))

    # 이름 변환 버튼 클릭 이벤트
    def process_files(self):
        if not self.file_paths:
            QMessageBox.warning(self, "경고", "처리할 PDF 파일이 없습니다.")
            return

        today_str = datetime.now().strftime("%Y.%m.%d")
        success_count = 0

        for file_path in self.file_paths:
            try:
                dir_name = os.path.dirname(file_path)
                original_name = os.path.basename(file_path)

                # 1. ori 폴더 생성 및 원본 백업
                ori_dir = os.path.join(dir_name, "ori")
                if not os.path.exists(ori_dir):
                    os.makedirs(ori_dir)
                
                backup_path = os.path.join(ori_dir, original_name)
                # 덮어쓰기 방지를 위해 파일이 없을 때만 복사
                if not os.path.exists(backup_path):
                    shutil.copy2(file_path, backup_path)

                # 2. PDF 문서 로드 및 분석
                doc = fitz.open(file_path)
                total_pages = len(doc)
                new_name = ""
                
                # 6페이지 (인덱스 5) 정보 확인
                has_page6 = (total_pages >= 6)
                page6_has_text = False
                
                if has_page6:
                    page6_text = doc[5].get_text().strip()
                    if len(page6_text) > 0:
                        page6_has_text = True
                
                # [조건 1] 6페이지에 텍스트가 있거나, 6페이지 자체가 없는 경우
                if page6_has_text or not has_page6:
                    div_num = total_pages // 4
                    new_name = f"{today_str}-50DS-4PG[{div_num}]-{original_name}"
                
                # [조건 2] 6페이지가 빈 페이지인 경우 (텍스트 없음)
                elif has_page6 and not page6_has_text:
                    if total_pages >= 3:
                        page3_text = doc[2].get_text()
                        first_line = ""
                        
                        # 첫 번째 유효한 줄 가져오기
                        for line in page3_text.splitlines():
                            trimmed_line = line.strip()
                            if len(trimmed_line) > 0:
                                first_line = trimmed_line
                                break
                        
                        div_num6 = total_pages // 6
                        if first_line.startswith("1-800"):
                            new_name = f"{today_str}-50DS-6PG[{div_num6}]-1ST-{original_name}"
                        elif first_line.startswith("Armenian"):
                            new_name = f"{today_str}-50DS-6PG[{div_num6}]-APRPT-{original_name}"
                
                doc.close()

                # 3. 이름 변경 실행
                if new_name:
                    new_path = os.path.join(dir_name, new_name)
                    os.rename(file_path, new_path)
                    success_count += 1

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        QMessageBox.information(self, "완료", f"총 {success_count}개의 파일 변환 및 백업이 완료되었습니다.")
        self.file_paths.clear()
        self.listbox.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFRenamerApp()
    ex.show()
    sys.exit(app.exec_())