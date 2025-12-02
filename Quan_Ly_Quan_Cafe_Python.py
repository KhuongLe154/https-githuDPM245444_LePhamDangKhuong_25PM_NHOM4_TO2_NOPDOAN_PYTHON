# ======================================================================
# ======================== IMPORT THƯ VIỆN ============================
# ======================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyodbc
from datetime import datetime
import pandas as pd
import os
from tkinter import scrolledtext


# ======================================================================
# ======================== KẾT NỐI DATABASE ===========================
# ======================================================================

class DatabaseConnection:
    """Lớp xử lý kết nối và thao tác với database SQL Server"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect_db()
    
    def connect_db(self):
        """Thiết lập kết nối với SQL Server"""
        try:
            connection_string = (
                "Driver={ODBC Driver 17 for SQL Server};"
                "Server=localhost\\SQLEXPRESS;"
                "Database=QLCF;"
                "Trusted_Connection=yes;"
            )
            
            self.conn = pyodbc.connect(connection_string)
            self.cursor = self.conn.cursor()
            print("Kết nối database thành công!")
            return True
            
        except Exception as e:
            print(f"Lỗi kết nối database: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Thực thi câu query SQL"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return True
        except Exception as e:
            print(f"Lỗi thực thi query: {e}")
            return False
    
    def commit(self):
        """Lưu thay đổi vào database"""
        try:
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Lỗi commit: {e}")
            return False


# ======================================================================
# ======================== CÁC CHỨC NĂNG XỬ LÝ ========================
# ======================================================================

class CafeManagementFunctions:
    """Lớp chứa tất cả các chức năng xử lý nghiệp vụ"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    # ==================== NHÂN VIÊN ====================
    
    def them_nhanvien(self, manv, ho, telot, ten, ngaysinh, chucvu):
        """Thêm nhân viên mới vào database"""
        try:
            # Kiểm tra mã nhân viên đã tồn tại chưa
            self.db.execute_query("SELECT COUNT(*) FROM NHANVIEN WHERE MANV = ?", (manv,))
            if self.db.cursor.fetchone()[0] > 0:
                return False, "Mã nhân viên đã tồn tại!"
            
            # Thêm nhân viên mới
            query = """
                INSERT INTO NHANVIEN (MANV, HO, TELOT, TEN, NGAYSINH)
                VALUES (?, ?, ?, ?, ?)
            """
            if self.db.execute_query(query, (manv, ho, telot, ten, ngaysinh)):
                # Nếu có chọn chức vụ, thêm vào bảng LƯƠNG
                if chucvu:
                    self._them_luong_macdinh(manv, ten, chucvu)
                
                self.db.commit()
                return True, "Thêm nhân viên thành công!"
            else:
                return False, "Lỗi khi thêm nhân viên!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def sua_nhanvien(self, manv, ho, telot, ten, ngaysinh, chucvu):
        """Cập nhật thông tin nhân viên"""
        try:
            query = """
                UPDATE NHANVIEN 
                SET HO = ?, TELOT = ?, TEN = ?, NGAYSINH = ? 
                WHERE MANV = ?
            """
            if self.db.execute_query(query, (ho, telot, ten, ngaysinh, manv)):
                # Cập nhật chức vụ nếu có
                if chucvu:
                    self._capnhat_chucvu_nhanvien(manv, ten, chucvu)
                
                self.db.commit()
                return True, "Cập nhật nhân viên thành công!"
            else:
                return False, "Lỗi khi cập nhật nhân viên!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def xoa_nhanvien(self, manv):
        """Xóa nhân viên khỏi database"""
        try:
            # Xóa từ bảng LUONG trước (do ràng buộc khóa ngoại)
            self.db.execute_query("DELETE FROM LUONG WHERE MANV = ?", (manv,))
            # Xóa từ bảng NHANVIEN
            self.db.execute_query("DELETE FROM NHANVIEN WHERE MANV = ?", (manv,))
            
            self.db.commit()
            return True, "Xóa nhân viên thành công!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def _them_luong_macdinh(self, manv, ten, chucvu):
        """Thêm thông tin lương mặc định cho nhân viên mới"""
        try:
            # Lấy mã công việc từ chức vụ
            self.db.execute_query("SELECT MACV FROM CONGVIEC WHERE CHUCVU = ?", (chucvu,))
            result = self.db.cursor.fetchone()
            if result:
                macv = result[0]
                
                # Lấy giá trị mặc định từ nhân viên khác cùng chức vụ
                self.db.execute_query("""
                    SELECT TOP 1 NGAYCONG, GIOLAM, LUONG 
                    FROM LUONG WHERE MACV = ?
                """, (macv,))
                default_values = self.db.cursor.fetchone()
                
                if default_values:
                    ngaycong, giolam, luong = default_values
                else:
                    # Giá trị mặc định nếu không có mẫu
                    ngaycong, giolam, luong = 22, 8, 3000000
                
                # Thêm vào bảng LUONG
                query = """
                    INSERT INTO LUONG (MANV, MACV, TEN, NGAYCONG, GIOLAM, LUONG) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                self.db.execute_query(query, (manv, macv, ten, ngaycong, giolam, luong))
                
        except Exception as e:
            print(f"Lỗi thêm lương mặc định: {e}")
    
    def _capnhat_chucvu_nhanvien(self, manv, ten, chucvu):
        """Cập nhật chức vụ cho nhân viên"""
        try:
            # Lấy mã công việc từ chức vụ
            self.db.execute_query("SELECT MACV FROM CONGVIEC WHERE CHUCVU = ?", (chucvu,))
            result = self.db.cursor.fetchone()
            if result:
                macv = result[0]
                
                # Kiểm tra xem đã có trong bảng LƯƠNG chưa
                self.db.execute_query("SELECT COUNT(*) FROM LUONG WHERE MANV = ?", (manv,))
                if self.db.cursor.fetchone()[0] > 0:
                    # Cập nhật chức vụ
                    self.db.execute_query("UPDATE LUONG SET MACV = ?, TEN = ? WHERE MANV = ?", 
                                        (macv, ten, manv))
                else:
                    # Thêm mới nếu chưa có
                    self._them_luong_macdinh(manv, ten, chucvu)
                    
        except Exception as e:
            print(f"Lỗi cập nhật chức vụ: {e}")
    
    # ==================== CÔNG VIỆC ====================
    
    def them_congviec(self, macv, chucvu, khuvuc):
        """Thêm công việc mới vào database"""
        try:
            # Kiểm tra mã công việc đã tồn tại chưa
            self.db.execute_query("SELECT COUNT(*) FROM CONGVIEC WHERE MACV = ?", (macv,))
            if self.db.cursor.fetchone()[0] > 0:
                return False, "Mã công việc đã tồn tại!"
            
            query = """
                INSERT INTO CONGVIEC (MACV, CHUCVU, KHUVUC)
                VALUES (?, ?, ?)
            """
            if self.db.execute_query(query, (macv, chucvu, khuvuc)):
                self.db.commit()
                return True, "Thêm công việc thành công!"
            else:
                return False, "Lỗi khi thêm công việc!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def sua_congviec(self, macv, chucvu, khuvuc):
        """Cập nhật thông tin công việc"""
        try:
            query = """
                UPDATE CONGVIEC 
                SET CHUCVU = ?, KHUVUC = ? 
                WHERE MACV = ?
            """
            if self.db.execute_query(query, (chucvu, khuvuc, macv)):
                self.db.commit()
                return True, "Cập nhật công việc thành công!"
            else:
                return False, "Lỗi khi cập nhật công việc!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def xoa_congviec(self, macv):
        """Xóa công việc khỏi database"""
        try:
            # Kiểm tra xem có nhân viên nào đang làm công việc này không
            self.db.execute_query("SELECT COUNT(*) FROM LUONG WHERE MACV = ?", (macv,))
            if self.db.cursor.fetchone()[0] > 0:
                return False, "Không thể xóa! Có nhân viên đang làm công việc này."
            
            self.db.execute_query("DELETE FROM CONGVIEC WHERE MACV = ?", (macv,))
            self.db.commit()
            return True, "Xóa công việc thành công!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    # ==================== MENU ====================
    
    def them_mon(self, mam, tenmon, loai, chucvu, gia):
        """Thêm món mới vào menu"""
        try:
            # Kiểm tra mã món đã tồn tại chưa
            self.db.execute_query("SELECT COUNT(*) FROM MENU WHERE MAM = ?", (mam,))
            if self.db.cursor.fetchone()[0] > 0:
                return False, "Mã món đã tồn tại!"
            
            query = """
                INSERT INTO MENU (MAM, TENMON, LOAI, CHUCVU, GIA)
                VALUES (?, ?, ?, ?, ?)
            """
            if self.db.execute_query(query, (mam, tenmon, loai, chucvu, gia)):
                self.db.commit()
                return True, "Thêm món thành công!"
            else:
                return False, "Lỗi khi thêm món!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def sua_mon(self, mam, tenmon, loai, chucvu, gia):
        """Cập nhật thông tin món"""
        try:
            query = """
                UPDATE MENU 
                SET TENMON = ?, LOAI = ?, CHUCVU = ?, GIA = ? 
                WHERE MAM = ?
            """
            if self.db.execute_query(query, (tenmon, loai, chucvu, gia, mam)):
                self.db.commit()
                return True, "Cập nhật món thành công!"
            else:
                return False, "Lỗi khi cập nhật món!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def xoa_mon(self, mam):
        """Xóa món khỏi menu"""
        try:
            self.db.execute_query("DELETE FROM MENU WHERE MAM = ?", (mam,))
            self.db.commit()
            return True, "Xóa món thành công!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    # ==================== LƯƠNG ====================
    
    def them_luong(self, manv, macv, ten, ngaycong, giolam, luong):
        """Thêm thông tin lương"""
        try:
            # Kiểm tra đã tồn tại chưa
            self.db.execute_query("SELECT COUNT(*) FROM LUONG WHERE MANV = ? AND MACV = ?", (manv, macv))
            if self.db.cursor.fetchone()[0] > 0:
                return False, "Thông tin lương đã tồn tại!"
            
            query = """
                INSERT INTO LUONG (MANV, MACV, TEN, NGAYCONG, GIOLAM, LUONG)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            if self.db.execute_query(query, (manv, macv, ten, ngaycong, giolam, luong)):
                self.db.commit()
                return True, "Thêm thông tin lương thành công!"
            else:
                return False, "Lỗi khi thêm thông tin lương!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def sua_luong(self, manv, macv, ten, ngaycong, giolam, luong):
        """Cập nhật thông tin lương"""
        try:
            query = """
                UPDATE LUONG 
                SET TEN = ?, NGAYCONG = ?, GIOLAM = ?, LUONG = ? 
                WHERE MANV = ? AND MACV = ?
            """
            if self.db.execute_query(query, (ten, ngaycong, giolam, luong, manv, macv)):
                self.db.commit()
                return True, "Cập nhật lương thành công!"
            else:
                return False, "Lỗi khi cập nhật lương!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def xoa_luong(self, manv, macv):
        """Xóa thông tin lương"""
        try:
            self.db.execute_query("DELETE FROM LUONG WHERE MANV = ? AND MACV = ?", (manv, macv))
            self.db.commit()
            return True, "Xóa thông tin lương thành công!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    # ==================== XUẤT EXCEL ====================
    
       # ==================== XUẤT EXCEL ====================
    
    def xuat_excel_nhanvien(self, filepath):
        """Xuất danh sách nhân viên ra Excel"""
        try:
            data = self.load_nhanvien()
            if data:
                # Chuyển đổi dữ liệu từ tuple sang list và định dạng ngày sinh
                formatted_data = []
                for row in data:
                    ngaysinh = row[4].strftime("%d/%m/%Y") if row[4] else ""
                    formatted_row = list(row[:4]) + [ngaysinh] + [row[5] if row[5] else "Chưa phân công"]
                    formatted_data.append(formatted_row)
                
                df = pd.DataFrame(formatted_data, columns=['Mã NV', 'Họ', 'Tên lót', 'Tên', 'Ngày sinh', 'Chức vụ'])
                df.to_excel(filepath, index=False)
                return True, f"Xuất Excel thành công! File: {os.path.basename(filepath)}"
            else:
                return False, "Không có dữ liệu để xuất"
        except Exception as e:
            return False, f"Lỗi xuất Excel: {str(e)}"
    
    def xuat_excel_congviec(self, filepath):
        """Xuất danh sách công việc ra Excel"""
        try:
            data = self.load_congviec()
            if data:
                # Chuyển đổi dữ liệu từ tuple sang list
                formatted_data = [list(row) for row in data]
                df = pd.DataFrame(formatted_data, columns=['Mã CV', 'Chức vụ', 'Khu vực'])
                df.to_excel(filepath, index=False)
                return True, f"Xuất Excel thành công! File: {os.path.basename(filepath)}"
            else:
                return False, "Không có dữ liệu để xuất"
        except Exception as e:
            return False, f"Lỗi xuất Excel: {str(e)}"
    
    def xuat_excel_menu(self, filepath):
        """Xuất danh sách menu ra Excel"""
        try:
            data = self.load_menu()
            if data:
                # Chuyển đổi dữ liệu từ tuple sang list
                formatted_data = []
                for row in data:
                    formatted_row = list(row[:4]) + [int(row[4])]  # Chuyển giá thành int
                    formatted_data.append(formatted_row)
                
                df = pd.DataFrame(formatted_data, columns=['Mã món', 'Tên món', 'Loại', 'Chức vụ pha chế', 'Giá'])
                df.to_excel(filepath, index=False)
                return True, f"Xuất Excel thành công! File: {os.path.basename(filepath)}"
            else:
                return False, "Không có dữ liệu để xuất"
        except Exception as e:
            return False, f"Lỗi xuất Excel: {str(e)}"
    
    def xuat_excel_luong(self, filepath):
        """Xuất danh sách lương ra Excel"""
        try:
            data = self.load_luong()
            if data:
                # Chuyển đổi dữ liệu từ tuple sang list
                formatted_data = []
                for row in data:
                    formatted_row = list(row[:5]) + [int(row[5])]  # Chuyển lương thành int
                    formatted_data.append(formatted_row)
                
                df = pd.DataFrame(formatted_data, columns=['Mã NV', 'Mã CV', 'Tên', 'Ngày công', 'Giờ làm', 'Lương'])
                df.to_excel(filepath, index=False)
                return True, f"Xuất Excel thành công! File: {os.path.basename(filepath)}"
            else:
                return False, "Không có dữ liệu để xuất"
        except Exception as e:
            return False, f"Lỗi xuất Excel: {str(e)}"
    
    # ==================== TÍNH TIỀN & GỌI MÓN ====================
    
    def load_menu_for_order(self):
        """Tải menu để gọi món"""
        try:
            self.db.execute_query("SELECT MAM, TENMON, GIA FROM MENU ORDER BY LOAI, TENMON")
            return self.db.cursor.fetchall()
        except Exception as e:
            print(f"Lỗi tải menu cho gọi món: {e}")
            return []
    
    def them_don_hang(self, ban_so, danh_sach_mon, tong_tien):
        """Thêm đơn hàng vào database"""
        try:
            # Tạo mã đơn hàng
            ma_don = f"DH{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Thêm vào bảng DONHANG
            query_donhang = """
                INSERT INTO DONHANG (MADON, BANSO, NGAYTAO, TONGTIEN, TRANGTHAI)
                VALUES (?, ?, ?, ?, ?)
            """
            ngay_tao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.db.execute_query(query_donhang, (ma_don, ban_so, ngay_tao, tong_tien, 'Đang xử lý')):
                # Thêm chi tiết đơn hàng
                for mon in danh_sach_mon:
                    query_chitiet = """
                        INSERT INTO CHITIETDONHANG (MADON, MAMON, TENMON, SOLUONG, DONGIA, THANHTIEN)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """
                    thanh_tien = mon['soluong'] * mon['gia']
                    self.db.execute_query(query_chitiet, (ma_don, mon['mamon'], mon['tenmon'], 
                                                         mon['soluong'], mon['gia'], thanh_tien))
                
                self.db.commit()
                return True, f"Thêm đơn hàng thành công! Mã đơn: {ma_don}"
            else:
                return False, "Lỗi khi thêm đơn hàng!"
                
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    # ==================== TẢI DỮ LIỆU ====================
    
    def load_nhanvien(self):
        """Tải danh sách nhân viên từ database"""
        try:
            query = """
            SELECT nv.MANV, nv.HO, nv.TELOT, nv.TEN, 
                   nv.NGAYSINH, cv.CHUCVU
            FROM NHANVIEN nv
            LEFT JOIN LUONG l ON nv.MANV = l.MANV
            LEFT JOIN CONGVIEC cv ON l.MACV = cv.MACV
            ORDER BY nv.MANV
            """
            self.db.execute_query(query)
            return self.db.cursor.fetchall()
        except Exception as e:
            print(f"Lỗi tải nhân viên: {e}")
            return []
    
    def load_congviec(self):
        """Tải danh sách công việc từ database"""
        try:
            self.db.execute_query("SELECT MACV, CHUCVU, KHUVUC FROM CONGVIEC ORDER BY MACV")
            return self.db.cursor.fetchall()
        except Exception as e:
            print(f"Lỗi tải công việc: {e}")
            return []
    
    def load_menu(self):
        """Tải danh sách menu từ database"""
        try:
            self.db.execute_query("SELECT MAM, TENMON, LOAI, CHUCVU, GIA FROM MENU ORDER BY MAM")
            return self.db.cursor.fetchall()
        except Exception as e:
            print(f"Lỗi tải menu: {e}")
            return []
    
    def load_luong(self):
        """Tải danh sách lương từ database"""
        try:
            self.db.execute_query("SELECT MANV, MACV, TEN, NGAYCONG, GIOLAM, LUONG FROM LUONG ORDER BY MANV")
            return self.db.cursor.fetchall()
        except Exception as e:
            print(f"Lỗi tải lương: {e}")
            return []
    
    def load_chucvu(self):
        """Tải danh sách chức vụ từ database"""
        try:
            self.db.execute_query("SELECT DISTINCT CHUCVU FROM CONGVIEC ORDER BY CHUCVU")
            results = self.db.cursor.fetchall()
            return [row[0] for row in results] if results else []
        except Exception as e:
            print(f"Lỗi tải chức vụ: {e}")
            return []
    
    def load_manv(self):
        """Tải danh sách mã nhân viên từ database"""
        try:
            self.db.execute_query("SELECT MANV FROM NHANVIEN ORDER BY MANV")
            results = self.db.cursor.fetchall()
            return [row[0] for row in results] if results else []
        except Exception as e:
            print(f"Lỗi tải mã NV: {e}")
            return []
    
    def load_macv(self):
        """Tải danh sách mã công việc từ database"""
        try:
            self.db.execute_query("SELECT MACV FROM CONGVIEC ORDER BY MACV")
            results = self.db.cursor.fetchall()
            return [row[0] for row in results] if results else []
        except Exception as e:
            print(f"Lỗi tải mã CV: {e}")
            return []


# ======================================================================
# =========================== GIAO DIỆN ===============================
# ======================================================================

class CafeManagementApp:
    """Lớp chính tạo giao diện người dùng"""
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_database()
        self.setup_colors()
        self.setup_styles()
        
        # Khởi tạo biến cho tính tiền
        self.danh_sach_mon_order = []
        self.tong_tien_order = 0
        
        if self.db.conn:
            self.create_main_interface()
            self.load_employees()  # Tải dữ liệu ngay khi khởi tạo
            self.refresh_all_comboboxes()
        else:
            self.show_error_screen()
    
    def setup_window(self):
        """Thiết lập cửa sổ chính"""
        self.root.title("ROYAL CAFE - HỆ THỐNG QUẢN LÝ")
        self.root.geometry("1400x850")
        self.root.configure(bg='#2C1810')
    
    def setup_database(self):
        """Khởi tạo kết nối database và các chức năng"""
        self.db = DatabaseConnection()
        self.functions = CafeManagementFunctions(self.db)
    
    def setup_colors(self):
        """Thiết lập bảng màu cho giao diện"""
        self.colors = {
            'primary': '#8B4513',        # Nâu saddle - màu cafe đậm
            'secondary': '#D2691E',      # Nâu chocolate
            'accent': '#CD853F',         # Nâu peru
            'gold': '#D4AF37',           # Vàng đồng sang trọng
            'light_gold': '#F5E6C8',     # Vàng nhạt
            'dark_brown': '#2C1810',     # Nâu đậm
            'medium_brown': '#5D4037',   # Nâu trung
            'light_brown': '#8D6E63',    # Nâu nhạt
            'cream': '#FFF8E1',          # Kem nhẹ
            'text_light': '#FFFFFF',     # Chữ trắng
            'text_dark': '#3E2723',      # Chữ nâu đậm
            'success': '#27AE60',        # Xanh thành công
            'warning': '#E67E22',        # Cam cảnh báo
            'error': '#E74C3C'           # Đỏ lỗi
        }
    
    def setup_styles(self):
        """Thiết lập styles cho các widget"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Font chữ Times New Roman
        self.font_normal = ('Times New Roman', 10)
        self.font_bold = ('Times New Roman', 10, 'bold')
        self.font_title = ('Times New Roman', 18, 'bold')
        self.font_tab = ('Times New Roman', 11, 'bold')
        
        # Configure các style
        self._configure_styles(style)
    
    def _configure_styles(self, style):
        """Cấu hình chi tiết các style"""
        # Main frames
        style.configure('Main.TFrame', background=self.colors['dark_brown'])
        
        # Notebook
        style.configure('Custom.TNotebook', background=self.colors['dark_brown'], borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                       background=self.colors['medium_brown'],
                       foreground=self.colors['cream'],
                       padding=[20, 10],
                       font=self.font_tab)
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', self.colors['gold'])])
        
        # Labelframes
        style.configure('Royal.TLabelframe',
                       background=self.colors['dark_brown'],
                       foreground=self.colors['gold'],
                       bordercolor=self.colors['gold'],
                       borderwidth=2,
                       font=self.font_bold)
        
        # Labels
        style.configure('Royal.TLabel',
                       background=self.colors['dark_brown'],
                       foreground=self.colors['cream'],
                       font=self.font_normal)
        
        # Entries
        style.configure('Royal.TEntry',
                       fieldbackground=self.colors['cream'],
                       foreground=self.colors['text_dark'],
                       font=self.font_normal)
        
        # Comboboxes
        style.configure('Royal.TCombobox',
                       fieldbackground=self.colors['cream'],
                       background=self.colors['cream'],
                       foreground=self.colors['text_dark'],
                       font=self.font_normal)
        
        # Buttons
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground=self.colors['text_light'],
                       font=self.font_bold,
                       padding=[15, 8])
        style.map('Primary.TButton',
                 background=[('active', self.colors['secondary']),
                           ('pressed', self.colors['accent'])])
        
        style.configure('Gold.TButton',
                       background=self.colors['gold'],
                       foreground=self.colors['text_dark'],
                       font=self.font_bold,
                       padding=[15, 8])
        style.map('Gold.TButton',
                 background=[('active', self.colors['light_gold']),
                           ('pressed', self.colors['accent'])])
        
        # Treeview
        style.configure('Royal.Treeview',
                       background=self.colors['cream'],
                       foreground=self.colors['text_dark'],
                       fieldbackground=self.colors['cream'],
                       rowheight=25,
                       font=self.font_normal)
        style.configure('Royal.Treeview.Heading',
                       background=self.colors['primary'],
                       foreground=self.colors['gold'],
                       font=self.font_bold)
        style.map('Royal.Treeview',
                 background=[('selected', self.colors['accent'])],
                 foreground=[('selected', self.colors['text_light'])])
    
    def show_error_screen(self):
        """Hiển thị màn hình lỗi khi không kết nối được database"""
        error_frame = tk.Frame(self.root, bg=self.colors['dark_brown'])
        error_frame.pack(expand=True, fill='both')
        
        error_label = tk.Label(error_frame, 
                             text="KHÔNG THỂ KẾT NỐI DATABASE!\nVui lòng kiểm tra SQL Server và thử lại.",
                             font=("Times New Roman", 14, "bold"), 
                             fg=self.colors['error'], 
                             bg=self.colors['dark_brown'],
                             pady=20)
        error_label.pack(expand=True)
        
        retry_button = tk.Button(error_frame, text="Thử kết nối lại",
                               command=self.retry_connection,
                               font=("Times New Roman", 12, "bold"), 
                               bg=self.colors['gold'], 
                               fg=self.colors['text_dark'],
                               padx=20,
                               pady=10)
        retry_button.pack(pady=10)
    
    def retry_connection(self):
        """Thử kết nối lại database"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.setup_database()
        if self.db.conn:
            self.create_main_interface()
            self.refresh_all_comboboxes()
        else:
            self.show_error_screen()
    
    def refresh_all_comboboxes(self):
        """Làm mới tất cả combobox"""
        self.refresh_chucvu_comboboxes()
        self.refresh_manv_combobox()
        self.refresh_macv_combobox()
    
    def refresh_chucvu_comboboxes(self):
        """Làm mới combobox chức vụ"""
        chucvu_list = self.functions.load_chucvu()
        # Cập nhật cho cả combobox ở tab nhân viên và menu
        if hasattr(self, 'chucvu_combobox'):
            self.chucvu_combobox['values'] = chucvu_list
        if hasattr(self, 'chucvu_menu_combobox'):
            self.chucvu_menu_combobox['values'] = chucvu_list
    
    def refresh_manv_combobox(self):
        """Làm mới combobox mã nhân viên"""
        manv_list = self.functions.load_manv()
        if hasattr(self, 'manv_luong_combobox'):
            self.manv_luong_combobox['values'] = manv_list
    
    def refresh_macv_combobox(self):
        """Làm mới combobox mã công việc"""
        macv_list = self.functions.load_macv()
        if hasattr(self, 'macv_luong_combobox'):
            self.macv_luong_combobox['values'] = macv_list
    
    def create_main_interface(self):
        """Tạo giao diện chính"""
        self.create_header()
        self.create_notebook()
        self.create_status_bar()
    
    def create_header(self):
        """Tạo header của ứng dụng"""
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Tiêu đề chính
        title_label = tk.Label(header_frame, 
                              text="☕ ZEN CAFE - HỆ THỐNG QUẢN LÝ", 
                              font=("Times New Roman", 20, "bold"), 
                              bg=self.colors['primary'], 
                              fg=self.colors['gold'],
                              pady=20)
        title_label.pack(expand=True)
        
        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                 text="Lê Phạm Đăng Khương - Cao Phương Ngân",
                                 font=("Times New Roman", 12, "italic"),
                                 bg=self.colors['primary'],
                                 fg=self.colors['light_gold'])
        subtitle_label.pack()
    
    def create_notebook(self):
        """Tạo notebook với các tab"""
        self.notebook = ttk.Notebook(self.root, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Tạo các frame cho từng tab
        self.nhanvien_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.congviec_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.menu_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.luong_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.order_frame = ttk.Frame(self.notebook, style='Main.TFrame')  # Tab mới: Gọi món & Tính tiền
        
        # Thêm các tab vào notebook
        self.notebook.add(self.nhanvien_frame, text="👥 QUẢN LÝ NHÂN VIÊN")
        self.notebook.add(self.congviec_frame, text="💼 QUẢN LÝ CÔNG VIỆC")
        self.notebook.add(self.menu_frame, text="☕ QUẢN LÝ MENU")
        self.notebook.add(self.luong_frame, text="💰 QUẢN LÝ LƯƠNG")
        self.notebook.add(self.order_frame, text="📋 GỌI MÓN & TÍNH TIỀN")
        
        # Tạo nội dung cho từng tab
        self.create_nhanvien_tab()
        self.create_congviec_tab()
        self.create_menu_tab()
        self.create_luong_tab()
        self.create_order_tab()  # Tạo tab gọi món
        
        # Bind sự kiện chuyển tab
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_status_bar(self):
        """Tạo thanh trạng thái"""
        status_frame = tk.Frame(self.root, bg=self.colors['primary'], height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        status_label = tk.Label(status_frame, 
                               text="Hệ thống ROYAL CAFE - Sẵn sàng hoạt động | Đồng bộ dữ liệu real-time",
                               font=("Times New Roman", 9),
                               bg=self.colors['primary'],
                               fg=self.colors['light_gold'])
        status_label.pack(side=tk.LEFT, padx=10)
        
        time_label = tk.Label(status_frame,
                             text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                             font=("Times New Roman", 9),
                             bg=self.colors['primary'],
                             fg=self.colors['light_gold'])
        time_label.pack(side=tk.RIGHT, padx=10)
    
    def on_tab_changed(self, event):
        """Xử lý sự kiện khi chuyển tab"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            self.load_employees()
        elif current_tab == 1:
            self.load_congviec()
        elif current_tab == 2:
            self.load_menu()
        elif current_tab == 3:
            self.load_luong()
        elif current_tab == 4:
            self.load_menu_for_order()
    
    # ==================== TAB NHÂN VIÊN ====================
    
    def create_nhanvien_tab(self):
        """Tạo tab quản lý nhân viên"""
        main_frame = ttk.Frame(self.nhanvien_frame, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Frame bên trái - form nhập liệu
        left_frame = ttk.LabelFrame(main_frame, text="📋 THÔNG TIN NHÂN VIÊN", 
                                   style='Royal.TLabelframe', padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Frame bên phải - danh sách
        right_frame = ttk.LabelFrame(main_frame, text="👥 DANH SÁCH NHÂN VIÊN", 
                                    style='Royal.TLabelframe', padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_nhanvien_form(left_frame)
        self.create_nhanvien_list(right_frame)
        self.create_nhanvien_buttons(left_frame)
    
    def create_nhanvien_form(self, parent):
        """Tạo form nhập thông tin nhân viên"""
        # Mã nhân viên
        ttk.Label(parent, text="Mã nhân viên:", style='Royal.TLabel').grid(row=0, column=0, sticky='w', pady=8)
        self.manv_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.manv_entry.grid(row=0, column=1, pady=8, padx=(10, 0))
        
        # Họ
        ttk.Label(parent, text="Họ:", style='Royal.TLabel').grid(row=1, column=0, sticky='w', pady=8)
        self.ho_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.ho_entry.grid(row=1, column=1, pady=8, padx=(10, 0))
        
        # Tên lót
        ttk.Label(parent, text="Tên lót:", style='Royal.TLabel').grid(row=2, column=0, sticky='w', pady=8)
        self.telot_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.telot_entry.grid(row=2, column=1, pady=8, padx=(10, 0))
        
        # Tên
        ttk.Label(parent, text="Tên:", style='Royal.TLabel').grid(row=3, column=0, sticky='w', pady=8)
        self.ten_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.ten_entry.grid(row=3, column=1, pady=8, padx=(10, 0))
        
        # Giới tính
        ttk.Label(parent, text="Giới tính:", style='Royal.TLabel').grid(row=4, column=0, sticky='w', pady=8)
        self.gender_var = tk.StringVar(value="Nam")
        gender_frame = ttk.Frame(parent, style='Main.TFrame')
        gender_frame.grid(row=4, column=1, sticky='w', pady=8, padx=(10, 0))
        
        # Radio button Nam
        tk.Radiobutton(gender_frame, text="Nam", variable=self.gender_var, 
                      value="Nam", bg=self.colors['dark_brown'], fg=self.colors['cream'],
                      selectcolor=self.colors['primary'], font=self.font_normal).pack(side=tk.LEFT, padx=(0, 10))
        # Radio button Nữ
        tk.Radiobutton(gender_frame, text="Nữ", variable=self.gender_var, 
                      value="Nữ", bg=self.colors['dark_brown'], fg=self.colors['cream'],
                      selectcolor=self.colors['primary'], font=self.font_normal).pack(side=tk.LEFT)
        
        # Ngày sinh
        ttk.Label(parent, text="Ngày sinh:", style='Royal.TLabel').grid(row=5, column=0, sticky='w', pady=8)
        self.ngaysinh_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.ngaysinh_entry.grid(row=5, column=1, pady=8, padx=(10, 0))
        self.ngaysinh_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        # Chức vụ
        ttk.Label(parent, text="Chức vụ:", style='Royal.TLabel').grid(row=6, column=0, sticky='w', pady=8)
        self.chucvu_combobox = ttk.Combobox(parent, width=22, state="readonly", 
                                           style='Royal.TCombobox', font=self.font_normal)
        self.chucvu_combobox.grid(row=6, column=1, pady=8, padx=(10, 0))
    
    def create_nhanvien_list(self, parent):
        """Tạo danh sách nhân viên dạng bảng"""
        columns = ("Mã NV", "Họ", "Tên lót", "Tên", "Giới tính", "Ngày sinh", "Chức vụ")
        self.nhanvien_tree = ttk.Treeview(parent, columns=columns, show="headings", 
                                         height=18, style='Royal.Treeview')
        
        # Thiết lập tiêu đề cột
        for col in columns:
            self.nhanvien_tree.heading(col, text=col)
            self.nhanvien_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.nhanvien_tree.yview)
        self.nhanvien_tree.configure(yscrollcommand=scrollbar.set)
        
        self.nhanvien_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind sự kiện chọn item
        self.nhanvien_tree.bind('<<TreeviewSelect>>', self.on_nhanvien_select)
    
    def create_nhanvien_buttons(self, parent):
        """Tạo các nút chức năng cho tab nhân viên"""
        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.grid(row=7, column=0, columnspan=2, pady=25)
        
        buttons = [
            ("➕ Thêm", self.them_nhanvien, 'Gold.TButton'),
            ("💾 Lưu", self.luu_nhanvien, 'Primary.TButton'),
            ("✏️ Sửa", self.sua_nhanvien, 'Gold.TButton'),
            ("❌ Hủy", self.huy_bo_nhanvien, 'Primary.TButton'),
            ("🗑️ Xóa", self.xoa_nhanvien, 'Gold.TButton'),
            ("📊 Xuất Excel", self.xuat_excel_nhanvien, 'Primary.TButton'),
        ]
        
        for text, command, style in buttons:
            ttk.Button(button_frame, text=text, command=command, style=style).pack(side=tk.LEFT, padx=5)
    
    def load_employees(self):
        """Tải danh sách nhân viên lên treeview"""
        try:
            # Xóa dữ liệu cũ
            for item in self.nhanvien_tree.get_children():
                self.nhanvien_tree.delete(item)
            
            # Tải dữ liệu mới
            data = self.functions.load_nhanvien()
            for row in data:
                ngaysinh_formatted = row[4].strftime("%d/%m/%Y") if row[4] else ""
                gioitinh = "Nữ" if row[0][-1] in ['2','4','6','8','0'] else "Nam"
                
                self.nhanvien_tree.insert("", tk.END, values=(
                    row[0], row[1], row[2], row[3], gioitinh, 
                    ngaysinh_formatted, row[5] or "Chưa phân công"
                ))
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách nhân viên: {str(e)}")
    
    def on_nhanvien_select(self, event):
        """Xử lý sự kiện khi chọn nhân viên từ danh sách"""
        try:
            selected_item = self.nhanvien_tree.selection()
            if selected_item:
                item = self.nhanvien_tree.item(selected_item[0])
                values = item['values']
                
                # Điền dữ liệu vào form
                self.manv_entry.delete(0, tk.END)
                self.manv_entry.insert(0, values[0])
                self.ho_entry.delete(0, tk.END)
                self.ho_entry.insert(0, values[1])
                self.telot_entry.delete(0, tk.END)
                self.telot_entry.insert(0, values[2])
                self.ten_entry.delete(0, tk.END)
                self.ten_entry.insert(0, values[3])
                self.gender_var.set(values[4])
                self.ngaysinh_entry.delete(0, tk.END)
                self.ngaysinh_entry.insert(0, values[5])
                if values[6] and values[6] != "Chưa phân công":
                    self.chucvu_combobox.set(values[6])
        except Exception as e:
            print(f"Lỗi khi chọn nhân viên: {e}")
    
    def them_nhanvien(self):
        """Xử lý chức năng thêm nhân viên"""
        self.clear_nhanvien_form()
        self.manv_entry.focus()
    
    def luu_nhanvien(self):
        """Xử lý chức năng lưu nhân viên"""
        try:
            # Lấy dữ liệu từ form
            manv = self.manv_entry.get().strip()
            ho = self.ho_entry.get().strip()
            telot = self.telot_entry.get().strip()
            ten = self.ten_entry.get().strip()
            ngaysinh = self.ngaysinh_entry.get().strip()
            chucvu = self.chucvu_combobox.get().strip()
            
            # Validate dữ liệu
            if not all([manv, ho, telot, ten, ngaysinh]):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
                return
            
            if not manv.startswith('KN0'):
                messagebox.showwarning("Cảnh báo", "Mã nhân viên phải bắt đầu bằng 'KN0'!")
                return
            
            # Chuyển đổi ngày sinh
            try:
                ngaysinh_sql = datetime.strptime(ngaysinh, "%d/%m/%Y").strftime("%Y-%m-%d")
            except:
                messagebox.showerror("Lỗi", "Định dạng ngày sinh không hợp lệ! (dd/mm/yyyy)")
                return
            
            # Kiểm tra xem là thêm mới hay cập nhật
            self.db.execute_query("SELECT COUNT(*) FROM NHANVIEN WHERE MANV = ?", (manv,))
            nhanvien_exists = self.db.cursor.fetchone()[0] > 0
            
            if nhanvien_exists:
                # Cập nhật nhân viên
                success, message = self.functions.sua_nhanvien(manv, ho, telot, ten, ngaysinh_sql, chucvu)
            else:
                # Thêm nhân viên mới
                success, message = self.functions.them_nhanvien(manv, ho, telot, ten, ngaysinh_sql, chucvu)
            
            if success:
                messagebox.showinfo("Thành công", message)
                self.load_employees()
                self.refresh_all_comboboxes()
            else:
                messagebox.showerror("Lỗi", message)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu thông tin: {str(e)}")
    
    def sua_nhanvien(self):
        """Xử lý chức năng sửa nhân viên"""
        if not self.nhanvien_tree.selection():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nhân viên cần sửa!")
            return
        self.luu_nhanvien()
    
    def xoa_nhanvien(self):
        """Xử lý chức năng xóa nhân viên"""
        selected_item = self.nhanvien_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nhân viên cần xóa!")
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa nhân viên này?"):
            try:
                manv = self.manv_entry.get().strip()
                success, message = self.functions.xoa_nhanvien(manv)
                
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.clear_nhanvien_form()
                    self.load_employees()
                    self.refresh_all_comboboxes()
                else:
                    messagebox.showerror("Lỗi", message)
                    
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa nhân viên: {str(e)}")
    
    def huy_bo_nhanvien(self):
        """Xử lý chức năng hủy bỏ thao tác"""
        self.clear_nhanvien_form()
    
    def xuat_excel_nhanvien(self):
        """Xuất danh sách nhân viên ra Excel"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile="DanhSachNhanVien.xlsx"
            )
            if filepath:
                success, message = self.functions.xuat_excel_nhanvien(filepath)
                if success:
                    messagebox.showinfo("Thành công", message)
                else:
                    messagebox.showerror("Lỗi", message)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất Excel: {str(e)}")
    
    def clear_nhanvien_form(self):
        """Xóa dữ liệu trong form nhân viên"""
        self.manv_entry.delete(0, tk.END)
        self.ho_entry.delete(0, tk.END)
        self.telot_entry.delete(0, tk.END)
        self.ten_entry.delete(0, tk.END)
        self.gender_var.set("Nam")
        self.ngaysinh_entry.delete(0, tk.END)
        self.ngaysinh_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        if self.chucvu_combobox['values']:
            self.chucvu_combobox.set('')
    
    # ==================== TAB CÔNG VIỆC ====================
    
    def create_congviec_tab(self):
        """Tạo tab quản lý công việc"""
        main_frame = ttk.Frame(self.congviec_frame, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left_frame = ttk.LabelFrame(main_frame, text="💼 THÔNG TIN CÔNG VIỆC", 
                                   style='Royal.TLabelframe', padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        right_frame = ttk.LabelFrame(main_frame, text="📊 DANH SÁCH CÔNG VIỆC", 
                                    style='Royal.TLabelframe', padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_congviec_form(left_frame)
        self.create_congviec_list(right_frame)
        self.create_congviec_buttons(left_frame)
    
    def create_congviec_form(self, parent):
        """Tạo form nhập thông tin công việc"""
        ttk.Label(parent, text="Mã công việc:", style='Royal.TLabel').grid(row=0, column=0, sticky='w', pady=10)
        self.macv_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.macv_entry.grid(row=0, column=1, pady=10, padx=(10, 0))
        
        ttk.Label(parent, text="Chức vụ:", style='Royal.TLabel').grid(row=1, column=0, sticky='w', pady=10)
        self.chucvu_cv_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.chucvu_cv_entry.grid(row=1, column=1, pady=10, padx=(10, 0))
        
        ttk.Label(parent, text="Khu vực:", style='Royal.TLabel').grid(row=2, column=0, sticky='w', pady=10)
        self.khuvuc_combobox = ttk.Combobox(parent, width=22, 
                                           values=["Lầu 1", "Lầu 2", "Lầu 3", "Quầy thu ngân", "Kho", "Quầy bar"],
                                           style='Royal.TCombobox', font=self.font_normal)
        self.khuvuc_combobox.grid(row=2, column=1, pady=10, padx=(10, 0))
    
    def create_congviec_list(self, parent):
        """Tạo danh sách công việc"""
        columns = ("Mã CV", "Chức vụ", "Khu vực")
        self.congviec_tree = ttk.Treeview(parent, columns=columns, show="headings", height=18, style='Royal.Treeview')
        
        for col in columns:
            self.congviec_tree.heading(col, text=col)
            self.congviec_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.congviec_tree.yview)
        self.congviec_tree.configure(yscrollcommand=scrollbar.set)
        
        self.congviec_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.congviec_tree.bind('<<TreeviewSelect>>', self.on_congviec_select)
    
    def create_congviec_buttons(self, parent):
        """Tạo các nút chức năng cho tab công việc"""
        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.grid(row=3, column=0, columnspan=2, pady=25)
        
        buttons = [
            ("➕ Thêm", self.them_congviec, 'Gold.TButton'),
            ("💾 Lưu", self.luu_congviec, 'Primary.TButton'),
            ("✏️ Sửa", self.sua_congviec, 'Gold.TButton'),
            ("❌ Hủy", self.huy_bo_congviec, 'Primary.TButton'),
            ("🗑️ Xóa", self.xoa_congviec, 'Gold.TButton'),
            ("📊 Xuất Excel", self.xuat_excel_congviec, 'Primary.TButton'),
        ]
        
        for text, command, style in buttons:
            ttk.Button(button_frame, text=text, command=command, style=style).pack(side=tk.LEFT, padx=5)
    
    def load_congviec(self):
        """Tải danh sách công việc"""
        try:
            for item in self.congviec_tree.get_children():
                self.congviec_tree.delete(item)
            
            data = self.functions.load_congviec()
            for row in data:
                self.congviec_tree.insert("", tk.END, values=row)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách công việc: {str(e)}")
    
    def on_congviec_select(self, event):
        """Xử lý sự kiện chọn công việc"""
        try:
            selected_item = self.congviec_tree.selection()
            if selected_item:
                item = self.congviec_tree.item(selected_item[0])
                values = item['values']
                
                self.macv_entry.delete(0, tk.END)
                self.macv_entry.insert(0, values[0])
                self.chucvu_cv_entry.delete(0, tk.END)
                self.chucvu_cv_entry.insert(0, values[1])
                self.khuvuc_combobox.set(values[2])
        except Exception as e:
            print(f"Lỗi khi chọn công việc: {e}")
    
    def them_congviec(self):
        """Xử lý thêm công việc"""
        self.clear_congviec_form()
        self.macv_entry.focus()
    
    def luu_congviec(self):
        """Xử lý lưu công việc"""
        try:
            macv = self.macv_entry.get().strip()
            chucvu = self.chucvu_cv_entry.get().strip()
            khuvuc = self.khuvuc_combobox.get().strip()
            
            if not all([macv, chucvu, khuvuc]):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
                return
            
            # Kiểm tra thêm mới hay cập nhật
            self.db.execute_query("SELECT COUNT(*) FROM CONGVIEC WHERE MACV = ?", (macv,))
            congviec_exists = self.db.cursor.fetchone()[0] > 0
            
            if congviec_exists:
                success, message = self.functions.sua_congviec(macv, chucvu, khuvuc)
            else:
                success, message = self.functions.them_congviec(macv, chucvu, khuvuc)
            
            if success:
                messagebox.showinfo("Thành công", message)
                self.load_congviec()
                self.refresh_all_comboboxes()
            else:
                messagebox.showerror("Lỗi", message)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu thông tin: {str(e)}")
    
    def sua_congviec(self):
        """Xử lý sửa công việc"""
        if not self.congviec_tree.selection():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn công việc cần sửa!")
            return
        self.luu_congviec()
    
    def xoa_congviec(self):
        """Xử lý xóa công việc"""
        selected_item = self.congviec_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn công việc cần xóa!")
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa công việc này?"):
            try:
                macv = self.macv_entry.get().strip()
                success, message = self.functions.xoa_congviec(macv)
                
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.clear_congviec_form()
                    self.load_congviec()
                    self.refresh_all_comboboxes()
                else:
                    messagebox.showerror("Lỗi", message)
                    
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa công việc: {str(e)}")
    
    def huy_bo_congviec(self):
        """Hủy bỏ thao tác công việc"""
        self.clear_congviec_form()
    
    def xuat_excel_congviec(self):
        """Xuất danh sách công việc ra Excel"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile="DanhSachCongViec.xlsx"
            )
            if filepath:
                success, message = self.functions.xuat_excel_congviec(filepath)
                if success:
                    messagebox.showinfo("Thành công", message)
                else:
                    messagebox.showerror("Lỗi", message)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất Excel: {str(e)}")
    
    def clear_congviec_form(self):
        """Xóa form công việc"""
        self.macv_entry.delete(0, tk.END)
        self.chucvu_cv_entry.delete(0, tk.END)
        self.khuvuc_combobox.set('')
    
    # ==================== TAB MENU ====================
    
    def create_menu_tab(self):
        """Tạo tab quản lý menu"""
        main_frame = ttk.Frame(self.menu_frame, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left_frame = ttk.LabelFrame(main_frame, text="☕ THÔNG TIN MÓN", 
                                   style='Royal.TLabelframe', padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        right_frame = ttk.LabelFrame(main_frame, text="📋 DANH SÁCH MENU", 
                                    style='Royal.TLabelframe', padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_menu_form(left_frame)
        self.create_menu_list(right_frame)
        self.create_menu_buttons(left_frame)
    
    def create_menu_form(self, parent):
        """Tạo form nhập thông tin menu"""
        ttk.Label(parent, text="Mã món:", style='Royal.TLabel').grid(row=0, column=0, sticky='w', pady=8)
        self.mamon_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.mamon_entry.grid(row=0, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Tên món:", style='Royal.TLabel').grid(row=1, column=0, sticky='w', pady=8)
        self.tenmon_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.tenmon_entry.grid(row=1, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Loại:", style='Royal.TLabel').grid(row=2, column=0, sticky='w', pady=8)
        self.loai_combobox = ttk.Combobox(parent, width=22, 
                                         values=["Thức uống", "Topping", "Bánh ngọt", "Đồ ăn nhanh", "Tráng miệng"],
                                         style='Royal.TCombobox', font=self.font_normal)
        self.loai_combobox.grid(row=2, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Chức vụ pha chế:", style='Royal.TLabel').grid(row=3, column=0, sticky='w', pady=8)
        self.chucvu_menu_combobox = ttk.Combobox(parent, width=22, state="readonly", 
                                                style='Royal.TCombobox', font=self.font_normal)
        self.chucvu_menu_combobox.grid(row=3, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Giá (VNĐ):", style='Royal.TLabel').grid(row=4, column=0, sticky='w', pady=8)
        self.gia_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.gia_entry.grid(row=4, column=1, pady=8, padx=(10, 0))
    
    def create_menu_list(self, parent):
        """Tạo danh sách menu"""
        columns = ("Mã món", "Tên món", "Loại", "Chức vụ", "Giá")
        self.menu_tree = ttk.Treeview(parent, columns=columns, show="headings", height=18, style='Royal.Treeview')
        
        for col in columns:
            self.menu_tree.heading(col, text=col)
            self.menu_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.menu_tree.yview)
        self.menu_tree.configure(yscrollcommand=scrollbar.set)
        
        self.menu_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.menu_tree.bind('<<TreeviewSelect>>', self.on_menu_select)
    
    def create_menu_buttons(self, parent):
        """Tạo các nút chức năng cho tab menu"""
        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.grid(row=5, column=0, columnspan=2, pady=25)
        
        buttons = [
            ("➕ Thêm", self.them_mon, 'Gold.TButton'),
            ("💾 Lưu", self.luu_mon, 'Primary.TButton'),
            ("✏️ Sửa", self.sua_mon, 'Gold.TButton'),
            ("❌ Hủy", self.huy_bo_mon, 'Primary.TButton'),
            ("🗑️ Xóa", self.xoa_mon, 'Gold.TButton'),
            ("📊 Xuất Excel", self.xuat_excel_menu, 'Primary.TButton'),
        ]
        
        for text, command, style in buttons:
            ttk.Button(button_frame, text=text, command=command, style=style).pack(side=tk.LEFT, padx=5)
    
    def load_menu(self):
        """Tải danh sách menu"""
        try:
            for item in self.menu_tree.get_children():
                self.menu_tree.delete(item)
            
            data = self.functions.load_menu()
            for row in data:
                gia_formatted = f"{int(row[4]):,} VNĐ"
                self.menu_tree.insert("", tk.END, values=(
                    row[0], row[1], row[2], row[3], gia_formatted
                ))
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách menu: {str(e)}")
    
    def on_menu_select(self, event):
        """Xử lý sự kiện chọn menu"""
        try:
            selected_item = self.menu_tree.selection()
            if selected_item:
                item = self.menu_tree.item(selected_item[0])
                values = item['values']
                
                self.mamon_entry.delete(0, tk.END)
                self.mamon_entry.insert(0, values[0])
                self.tenmon_entry.delete(0, tk.END)
                self.tenmon_entry.insert(0, values[1])
                self.loai_combobox.set(values[2])
                self.chucvu_menu_combobox.set(values[3])
                self.gia_entry.delete(0, tk.END)
                # Loại bỏ " VNĐ" và dấu phẩy khi hiển thị lại trong form
                gia_value = values[4].replace(" VNĐ", "").replace(",", "")
                self.gia_entry.insert(0, gia_value)
        except Exception as e:
            print(f"Lỗi khi chọn menu: {e}")
    
    def them_mon(self):
        """Xử lý thêm món"""
        self.clear_menu_form()
        self.mamon_entry.focus()
    
    def luu_mon(self):
        """Xử lý lưu món"""
        try:
            mam = self.mamon_entry.get().strip()
            tenmon = self.tenmon_entry.get().strip()
            loai = self.loai_combobox.get().strip()
            chucvu = self.chucvu_menu_combobox.get().strip()
            gia = self.gia_entry.get().strip()
            
            if not all([mam, tenmon, loai, chucvu, gia]):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
                return
            
            # Loại bỏ dấu phẩy phân cách hàng nghìn nếu có
            gia = gia.replace(",", "")
            
            if not gia.isdigit():
                messagebox.showwarning("Cảnh báo", "Giá phải là số!")
                return
            
            # Kiểm tra thêm mới hay cập nhật
            self.db.execute_query("SELECT COUNT(*) FROM MENU WHERE MAM = ?", (mam,))
            menu_exists = self.db.cursor.fetchone()[0] > 0
            
            if menu_exists:
                success, message = self.functions.sua_mon(mam, tenmon, loai, chucvu, int(gia))
            else:
                success, message = self.functions.them_mon(mam, tenmon, loai, chucvu, int(gia))
            
            if success:
                messagebox.showinfo("Thành công", message)
                self.load_menu()
            else:
                messagebox.showerror("Lỗi", message)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu thông tin: {str(e)}")
    
    def sua_mon(self):
        """Xử lý sửa món"""
        if not self.menu_tree.selection():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn món cần sửa!")
            return
        self.luu_mon()
    
    def xoa_mon(self):
        """Xử lý xóa món"""
        selected_item = self.menu_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn món cần xóa!")
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa món này?"):
            try:
                mam = self.mamon_entry.get().strip()
                success, message = self.functions.xoa_mon(mam)
                
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.clear_menu_form()
                    self.load_menu()
                else:
                    messagebox.showerror("Lỗi", message)
                    
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa món: {str(e)}")
    
    def huy_bo_mon(self):
        """Hủy bỏ thao tác menu"""
        self.clear_menu_form()
    
    def xuat_excel_menu(self):
        """Xuất danh sách menu ra Excel"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile="DanhSachMenu.xlsx"
            )
            if filepath:
                success, message = self.functions.xuat_excel_menu(filepath)
                if success:
                    messagebox.showinfo("Thành công", message)
                else:
                    messagebox.showerror("Lỗi", message)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất Excel: {str(e)}")
    
    def clear_menu_form(self):
        """Xóa form menu"""
        self.mamon_entry.delete(0, tk.END)
        self.tenmon_entry.delete(0, tk.END)
        self.loai_combobox.set('')
        if self.chucvu_menu_combobox['values']:
            self.chucvu_menu_combobox.set('')
        self.gia_entry.delete(0, tk.END)
    
    # ==================== TAB LƯƠNG ====================
    
    def create_luong_tab(self):
        """Tạo tab quản lý lương"""
        main_frame = ttk.Frame(self.luong_frame, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left_frame = ttk.LabelFrame(main_frame, text="💰 THÔNG TIN LƯƠNG", 
                                   style='Royal.TLabelframe', padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        right_frame = ttk.LabelFrame(main_frame, text="📈 DANH SÁCH LƯƠNG", 
                                    style='Royal.TLabelframe', padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_luong_form(left_frame)
        self.create_luong_list(right_frame)
        self.create_luong_buttons(left_frame)
    
    def create_luong_form(self, parent):
        """Tạo form nhập thông tin lương"""
        ttk.Label(parent, text="Mã nhân viên:", style='Royal.TLabel').grid(row=0, column=0, sticky='w', pady=8)
        self.manv_luong_combobox = ttk.Combobox(parent, width=22, state="readonly", 
                                               style='Royal.TCombobox', font=self.font_normal)
        self.manv_luong_combobox.grid(row=0, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Mã công việc:", style='Royal.TLabel').grid(row=1, column=0, sticky='w', pady=8)
        self.macv_luong_combobox = ttk.Combobox(parent, width=22, state="readonly", 
                                               style='Royal.TCombobox', font=self.font_normal)
        self.macv_luong_combobox.grid(row=1, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Tên nhân viên:", style='Royal.TLabel').grid(row=2, column=0, sticky='w', pady=8)
        self.ten_luong_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.ten_luong_entry.grid(row=2, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Ngày công:", style='Royal.TLabel').grid(row=3, column=0, sticky='w', pady=8)
        self.ngaycong_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.ngaycong_entry.grid(row=3, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Giờ làm:", style='Royal.TLabel').grid(row=4, column=0, sticky='w', pady=8)
        self.giolam_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.giolam_entry.grid(row=4, column=1, pady=8, padx=(10, 0))
        
        ttk.Label(parent, text="Lương (VNĐ):", style='Royal.TLabel').grid(row=5, column=0, sticky='w', pady=8)
        self.luong_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.luong_entry.grid(row=5, column=1, pady=8, padx=(10, 0))
    
    def create_luong_list(self, parent):
        """Tạo danh sách lương"""
        columns = ("Mã NV", "Mã CV", "Tên", "Ngày công", "Giờ làm", "Lương")
        self.luong_tree = ttk.Treeview(parent, columns=columns, show="headings", height=18, style='Royal.Treeview')
        
        for col in columns:
            self.luong_tree.heading(col, text=col)
            self.luong_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.luong_tree.yview)
        self.luong_tree.configure(yscrollcommand=scrollbar.set)
        
        self.luong_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.luong_tree.bind('<<TreeviewSelect>>', self.on_luong_select)
    
    def create_luong_buttons(self, parent):
        """Tạo các nút chức năng cho tab lương"""
        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.grid(row=6, column=0, columnspan=2, pady=25)
        
        buttons = [
            ("➕ Thêm", self.them_luong, 'Gold.TButton'),
            ("💾 Lưu", self.luu_luong, 'Primary.TButton'),
            ("✏️ Sửa", self.sua_luong, 'Gold.TButton'),
            ("❌ Hủy", self.huy_bo_luong, 'Primary.TButton'),
            ("🗑️ Xóa", self.xoa_luong, 'Gold.TButton'),
            ("📊 Xuất Excel", self.xuat_excel_luong, 'Primary.TButton'),
        ]
        
        for text, command, style in buttons:
            ttk.Button(button_frame, text=text, command=command, style=style).pack(side=tk.LEFT, padx=5)
    
    def load_luong(self):
        """Tải danh sách lương"""
        try:
            for item in self.luong_tree.get_children():
                self.luong_tree.delete(item)
            
            data = self.functions.load_luong()
            for row in data:
                luong_formatted = f"{int(row[5]):,} VNĐ"
                self.luong_tree.insert("", tk.END, values=(
                    row[0], row[1], row[2], row[3], row[4], luong_formatted
                ))
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách lương: {str(e)}")
    
    def on_luong_select(self, event):
        """Xử lý sự kiện chọn lương"""
        try:
            selected_item = self.luong_tree.selection()
            if selected_item:
                item = self.luong_tree.item(selected_item[0])
                values = item['values']
                
                self.manv_luong_combobox.set(values[0])
                self.macv_luong_combobox.set(values[1])
                self.ten_luong_entry.delete(0, tk.END)
                self.ten_luong_entry.insert(0, values[2])
                self.ngaycong_entry.delete(0, tk.END)
                self.ngaycong_entry.insert(0, values[3])
                self.giolam_entry.delete(0, tk.END)
                self.giolam_entry.insert(0, values[4])
                self.luong_entry.delete(0, tk.END)
                # Loại bỏ " VNĐ" và dấu phẩy khi hiển thị lại trong form
                luong_value = values[5].replace(" VNĐ", "").replace(",", "")
                self.luong_entry.insert(0, luong_value)
        except Exception as e:
            print(f"Lỗi khi chọn lương: {e}")
    
    def them_luong(self):
        """Xử lý thêm lương"""
        self.clear_luong_form()
        self.manv_luong_combobox.focus()
    
    def luu_luong(self):
        """Xử lý lưu lương"""
        try:
            manv = self.manv_luong_combobox.get().strip()
            macv = self.macv_luong_combobox.get().strip()
            ten = self.ten_luong_entry.get().strip()
            ngaycong = self.ngaycong_entry.get().strip()
            giolam = self.giolam_entry.get().strip()
            luong = self.luong_entry.get().strip()
            
            if not all([manv, macv, ten, ngaycong, giolam, luong]):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
                return
            
            # Loại bỏ dấu phẩy phân cách hàng nghìn nếu có
            luong = luong.replace(",", "")
            
            if not all([ngaycong.isdigit(), giolam.isdigit(), luong.isdigit()]):
                messagebox.showwarning("Cảnh báo", "Ngày công, giờ làm và lương phải là số!")
                return
            
            # Kiểm tra thêm mới hay cập nhật
            self.db.execute_query("SELECT COUNT(*) FROM LUONG WHERE MANV = ? AND MACV = ?", (manv, macv))
            luong_exists = self.db.cursor.fetchone()[0] > 0
            
            if luong_exists:
                success, message = self.functions.sua_luong(manv, macv, ten, int(ngaycong), int(giolam), int(luong))
            else:
                success, message = self.functions.them_luong(manv, macv, ten, int(ngaycong), int(giolam), int(luong))
            
            if success:
                messagebox.showinfo("Thành công", message)
                self.load_luong()
            else:
                messagebox.showerror("Lỗi", message)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu thông tin: {str(e)}")
    
    def sua_luong(self):
        """Xử lý sửa lương"""
        if not self.luong_tree.selection():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thông tin lương cần sửa!")
            return
        self.luu_luong()
    
    def xoa_luong(self):
        """Xử lý xóa lương"""
        selected_item = self.luong_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thông tin lương cần xóa!")
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa thông tin lương này?"):
            try:
                manv = self.manv_luong_combobox.get().strip()
                macv = self.macv_luong_combobox.get().strip()
                success, message = self.functions.xoa_luong(manv, macv)
                
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.clear_luong_form()
                    self.load_luong()
                else:
                    messagebox.showerror("Lỗi", message)
                    
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa thông tin lương: {str(e)}")
    
    def huy_bo_luong(self):
        """Hủy bỏ thao tác lương"""
        self.clear_luong_form()
    
    def xuat_excel_luong(self):
        """Xuất danh sách lương ra Excel"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile="DanhSachLuong.xlsx"
            )
            if filepath:
                success, message = self.functions.xuat_excel_luong(filepath)
                if success:
                    messagebox.showinfo("Thành công", message)
                else:
                    messagebox.showerror("Lỗi", message)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất Excel: {str(e)}")
    
    def clear_luong_form(self):
        """Xóa form lương"""
        self.manv_luong_combobox.set('')
        self.macv_luong_combobox.set('')
        self.ten_luong_entry.delete(0, tk.END)
        self.ngaycong_entry.delete(0, tk.END)
        self.giolam_entry.delete(0, tk.END)
        self.luong_entry.delete(0, tk.END)
    
    # ==================== TAB GỌI MÓN & TÍNH TIỀN ====================
    
    def create_order_tab(self):
        """Tạo tab gọi món và tính tiền"""
        main_frame = ttk.Frame(self.order_frame, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Frame bên trái - danh sách món
        left_frame = ttk.LabelFrame(main_frame, text="☕ DANH SÁCH MÓN", 
                                   style='Royal.TLabelframe', padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Frame bên phải - đơn hàng và tính tiền
        right_frame = ttk.LabelFrame(main_frame, text="📋 ĐƠN HÀNG & TÍNH TIỀN", 
                                    style='Royal.TLabelframe', padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_order_menu_list(left_frame)
        self.create_order_form(right_frame)
        self.create_order_buttons(right_frame)
    
    def create_order_menu_list(self, parent):
        """Tạo danh sách món để gọi"""
        columns = ("Mã món", "Tên món", "Giá")
        self.order_tree = ttk.Treeview(parent, columns=columns, show="headings", height=20, style='Royal.Treeview')
        
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        
        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind sự kiện double click để thêm món
        self.order_tree.bind('<Double-Button-1>', self.on_order_item_double_click)
    
    def create_order_form(self, parent):
        """Tạo form nhập thông tin đơn hàng"""
        # Số bàn
        ttk.Label(parent, text="Số bàn:", style='Royal.TLabel').grid(row=0, column=0, sticky='w', pady=8)
        self.ban_so_entry = ttk.Entry(parent, width=25, style='Royal.TEntry', font=self.font_normal)
        self.ban_so_entry.grid(row=0, column=1, pady=8, padx=(10, 0))
        self.ban_so_entry.insert(0, "1")
        
        # Món đã chọn
        ttk.Label(parent, text="Món đã chọn:", style='Royal.TLabel').grid(row=1, column=0, sticky='w', pady=8)
        
        # Text area để hiển thị món đã chọn
        self.order_text = scrolledtext.ScrolledText(parent, width=40, height=10, 
                                                   font=self.font_normal,
                                                   bg=self.colors['cream'],
                                                   fg=self.colors['text_dark'])
        self.order_text.grid(row=1, column=1, rowspan=3, pady=8, padx=(10, 0), sticky='nsew')
        
        # Tổng tiền
        ttk.Label(parent, text="Tổng tiền:", style='Royal.TLabel').grid(row=4, column=0, sticky='w', pady=8)
        self.tong_tien_label = ttk.Label(parent, text="0 VNĐ", style='Royal.TLabel', 
                                        font=("Times New Roman", 12, "bold"),
                                        foreground=self.colors['gold'])
        self.tong_tien_label.grid(row=4, column=1, sticky='w', pady=8, padx=(10, 0))
        
        # Số lượng
        ttk.Label(parent, text="Số lượng:", style='Royal.TLabel').grid(row=5, column=0, sticky='w', pady=8)
        self.soluong_spinbox = tk.Spinbox(parent, from_=1, to=20, width=10,
                                         font=self.font_normal,
                                         bg=self.colors['cream'],
                                         fg=self.colors['text_dark'])
        self.soluong_spinbox.grid(row=5, column=1, sticky='w', pady=8, padx=(10, 0))
        self.soluong_spinbox.delete(0, tk.END)
        self.soluong_spinbox.insert(0, "1")
    
    def create_order_buttons(self, parent):
        """Tạo các nút chức năng cho tab gọi món"""
        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        buttons = [
            ("➕ Thêm món", self.them_mon_order, 'Gold.TButton'),
            ("➖ Xóa món", self.xoa_mon_order, 'Primary.TButton'),
            ("🧹 Xóa tất cả", self.xoa_tat_ca_mon, 'Gold.TButton'),
            ("💳 Thanh toán", self.thanh_toan, 'Primary.TButton'),
            ("📄 In hóa đơn", self.in_hoa_don, 'Gold.TButton'),
        ]
        
        for text, command, style in buttons:
            ttk.Button(button_frame, text=text, command=command, style=style).pack(side=tk.LEFT, padx=5, pady=5)
    
    def load_menu_for_order(self):
        """Tải danh sách món lên treeview cho tab gọi món"""
        try:
            # Xóa dữ liệu cũ
            for item in self.order_tree.get_children():
                self.order_tree.delete(item)
            
            # Tải dữ liệu mới
            data = self.functions.load_menu_for_order()
            for row in data:
                gia_formatted = f"{int(row[2]):,} VNĐ"
                self.order_tree.insert("", tk.END, values=(
                    row[0], row[1], gia_formatted
                ))
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách món: {str(e)}")
    
    def on_order_item_double_click(self, event):
        """Xử lý sự kiện double click để thêm món vào đơn hàng"""
        selected_item = self.order_tree.selection()
        if selected_item:
            item = self.order_tree.item(selected_item[0])
            values = item['values']
            
            # Lấy thông tin món
            mamon = values[0]
            tenmon = values[1]
            gia = int(values[2].replace(" VNĐ", "").replace(",", ""))
            soluong = int(self.soluong_spinbox.get())
            
            # Thêm vào danh sách
            mon_da_co = False
            for mon in self.danh_sach_mon_order:
                if mon['mamon'] == mamon:
                    mon['soluong'] += soluong
                    mon['thanhtien'] = mon['soluong'] * mon['gia']
                    mon_da_co = True
                    break
            
            if not mon_da_co:
                self.danh_sach_mon_order.append({
                    'mamon': mamon,
                    'tenmon': tenmon,
                    'gia': gia,
                    'soluong': soluong,
                    'thanhtien': gia * soluong
                })
            
            # Cập nhật hiển thị và tổng tiền
            self.cap_nhat_don_hang()
    
    def them_mon_order(self):
        """Thêm món vào đơn hàng từ danh sách"""
        selected_item = self.order_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn món từ danh sách!")
            return
        
        self.on_order_item_double_click(None)
    
    def xoa_mon_order(self):
        """Xóa món khỏi đơn hàng"""
        try:
            # Lấy nội dung trong text area
            content = self.order_text.get("1.0", tk.END).strip()
            lines = content.split('\n')
            
            if not lines or len(lines) < 2:
                messagebox.showwarning("Cảnh báo", "Không có món nào để xóa!")
                return
            
            # Hiển thị dialog để chọn món cần xóa
            mon_list = []
            for line in lines[1:]:  # Bỏ qua dòng tiêu đề
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        mon_list.append(f"{parts[1].strip()} - Số lượng: {parts[2].strip()}")
            
            if not mon_list:
                return
            
            # Tạo dialog chọn món
            dialog = tk.Toplevel(self.root)
            dialog.title("Chọn món cần xóa")
            dialog.geometry("300x200")
            dialog.configure(bg=self.colors['dark_brown'])
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="Chọn món cần xóa:", 
                    bg=self.colors['dark_brown'], fg=self.colors['cream'],
                    font=self.font_normal).pack(pady=10)
            
            listbox = tk.Listbox(dialog, height=6, 
                                bg=self.colors['cream'], fg=self.colors['text_dark'],
                                font=self.font_normal)
            listbox.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
            
            for mon in mon_list:
                listbox.insert(tk.END, mon)
            
            def xoa_mon_da_chon():
                selected_index = listbox.curselection()
                if selected_index:
                    index = selected_index[0]
                    # Xóa món khỏi danh sách
                    if index < len(self.danh_sach_mon_order):
                        del self.danh_sach_mon_order[index]
                        self.cap_nhat_don_hang()
                    dialog.destroy()
                else:
                    messagebox.showwarning("Cảnh báo", "Vui lòng chọn món cần xóa!", parent=dialog)
            
            button_frame = tk.Frame(dialog, bg=self.colors['dark_brown'])
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="Xóa", command=xoa_mon_da_chon,
                     bg=self.colors['primary'], fg=self.colors['text_light'],
                     font=self.font_normal).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Hủy", command=dialog.destroy,
                     bg=self.colors['light_brown'], fg=self.colors['text_light'],
                     font=self.font_normal).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa món: {str(e)}")
    
    def xoa_tat_ca_mon(self):
        """Xóa tất cả món khỏi đơn hàng"""
        if not self.danh_sach_mon_order:
            messagebox.showwarning("Cảnh báo", "Đơn hàng đang trống!")
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa tất cả món khỏi đơn hàng?"):
            self.danh_sach_mon_order = []
            self.cap_nhat_don_hang()
    
    def cap_nhat_don_hang(self):
        """Cập nhật hiển thị đơn hàng và tổng tiền"""
        # Xóa nội dung cũ
        self.order_text.delete("1.0", tk.END)
        
        if not self.danh_sach_mon_order:
            self.order_text.insert(tk.END, "Đơn hàng đang trống...")
            self.tong_tien_order = 0
        else:
            # Hiển thị tiêu đề
            self.order_text.insert(tk.END, "STT | Tên món | SL | Đơn giá | Thành tiền\n")
            self.order_text.insert(tk.END, "-" * 60 + "\n")
            
            # Hiển thị từng món
            tong_tien = 0
            for i, mon in enumerate(self.danh_sach_mon_order, 1):
                thanh_tien = mon['soluong'] * mon['gia']
                tong_tien += thanh_tien
                
                line = f"{i:3d} | {mon['tenmon'][:20]:20s} | {mon['soluong']:2d} | {mon['gia']:8,d} | {thanh_tien:10,d}\n"
                self.order_text.insert(tk.END, line)
            
            self.tong_tien_order = tong_tien
        
        # Cập nhật tổng tiền
        self.tong_tien_label.config(text=f"{self.tong_tien_order:,} VNĐ")
    
    def thanh_toan(self):
        """Xử lý thanh toán đơn hàng"""
        if not self.danh_sach_mon_order:
            messagebox.showwarning("Cảnh báo", "Đơn hàng đang trống!")
            return
        
        ban_so = self.ban_so_entry.get().strip()
        if not ban_so:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập số bàn!")
            return
        
        try:
            # Thêm đơn hàng vào database
            success, message = self.functions.them_don_hang(ban_so, self.danh_sach_mon_order, self.tong_tien_order)
            
            if success:
                messagebox.showinfo("Thành công", message)
                # Reset đơn hàng
                self.danh_sach_mon_order = []
                self.cap_nhat_don_hang()
                self.ban_so_entry.delete(0, tk.END)
                self.ban_so_entry.insert(0, str(int(ban_so) + 1 if ban_so.isdigit() else "1"))
            else:
                messagebox.showerror("Lỗi", message)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thanh toán: {str(e)}")
    
    def in_hoa_don(self):
        """In hóa đơn"""
        if not self.danh_sach_mon_order:
            messagebox.showwarning("Cảnh báo", "Đơn hàng đang trống!")
            return
        
        ban_so = self.ban_so_entry.get().strip()
        if not ban_so:
            ban_so = "Takeaway"
        
        # Tạo nội dung hóa đơn
        hoa_don = "=" * 50 + "\n"
        hoa_don += " " * 15 + "ZEN CAFE\n"
        hoa_don += "=" * 50 + "\n"
        hoa_don += f"Bàn số: {ban_so}\n"
        hoa_don += f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        hoa_don += "-" * 50 + "\n"
        hoa_don += "STT  Tên món                SL   Đơn giá    Thành tiền\n"
        hoa_don += "-" * 50 + "\n"
        
        for i, mon in enumerate(self.danh_sach_mon_order, 1):
            thanh_tien = mon['soluong'] * mon['gia']
            hoa_don += f"{i:3d}  {mon['tenmon'][:20]:20s}  {mon['soluong']:2d}  {mon['gia']:8,d}  {thanh_tien:10,d}\n"
        
        hoa_don += "-" * 50 + "\n"
        hoa_don += f"TỔNG CỘNG: {self.tong_tien_order:>36,d} VNĐ\n"
        hoa_don += "=" * 50 + "\n"
        hoa_don += "Cảm ơn quý khách!\n"
        hoa_don += "Hẹn gặp lại!\n"
        hoa_don += "=" * 50 + "\n"
        
        # Hiển thị hóa đơn trong dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("HÓA ĐƠN")
        dialog.geometry("500x600")
        dialog.configure(bg=self.colors['dark_brown'])
        dialog.transient(self.root)
        
        # Text area hiển thị hóa đơn
        text_area = scrolledtext.ScrolledText(dialog, width=60, height=30,
                                             font=("Courier New", 10),
                                             bg='white', fg='black')
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, hoa_don)
        text_area.config(state='disabled')
        
        # Nút in và đóng
        button_frame = tk.Frame(dialog, bg=self.colors['dark_brown'])
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="In hóa đơn", 
                 command=lambda: self.thuc_hien_in_hoa_don(hoa_don),
                 bg=self.colors['primary'], fg=self.colors['text_light'],
                 font=self.font_normal).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Đóng", command=dialog.destroy,
                 bg=self.colors['light_brown'], fg=self.colors['text_light'],
                 font=self.font_normal).pack(side=tk.LEFT, padx=5)
    
    def thuc_hien_in_hoa_don(self, hoa_don):
        """Thực hiện in hóa đơn ra file"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"HoaDon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(hoa_don)
                messagebox.showinfo("Thành công", f"Đã lưu hóa đơn thành công!\nFile: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu hóa đơn: {str(e)}")


# ======================================================================
# =========================== CHẠY ỨNG DỤNG ============================
# ======================================================================

def main():
    """Hàm chính khởi chạy ứng dụng"""
    try:
        root = tk.Tk()
        app = CafeManagementApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Lỗi chương trình: {e}")
        input("Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()