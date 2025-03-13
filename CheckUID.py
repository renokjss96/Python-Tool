import threading
import queue
import requests
import os
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import re
import queue

# Hàng đợi các bài post cần kiểm tra
task_queue = queue.Queue()
update_queue = queue.Queue()
output_file = None  # File lưu kết quả
# 🛠 Hàm kiểm tra trạng thái bài viết Facebook
def check_facebook_post_status(post_url, post_id):
    headers = {
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.facebook.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",  # Do Not Track
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(post_url, headers=headers, timeout=10)

        if response.status_code == 200:
            html_content = response.text

            match = re.search(r'"storyFBID"\s*:\s*"(\d+)"', html_content)
            if match:
                found_story_id = match.group(1)
                if found_story_id == post_id:
                    group_match = re.search(r'"groupID"\s*:\s*"(\d+)"', html_content)
                    if group_match:
                        group_id = group_match.group(1)
                        return f"✅ Live | Group ID: {group_id}", group_id
                    else:
                        return "✅ Live (No Group ID)", None
                else:
                    return "❌ Deleted/Not Found", None

            error_match = re.search(r'"title"\s*:\s*"([^"]+)"', html_content)
            if error_match:
                return f"❌ Deleted ({error_match.group(1)})", None

            return "⚠️ No Data Found", None

        return f"⚠️ HTTP Error: {response.status_code}", None

    except Exception as e:
        return f"❌ Error: {str(e)}", None
# 🛠 Worker xử lý bài post trong hàng đợi
def worker():
    while not task_queue.empty():
        item = task_queue.get()
        values = tree.item(item, "values")
        stt, post_url, post_id, _ = values

        status, group_id = check_facebook_post_status(post_url, post_id)

        #tree.item(item, values=(stt, post_url, post_id, status))
        # Đẩy kết quả vào hàng đợi thay vì cập nhật trực tiếp
        update_queue.put((item, (stt, post_url, post_id, status)))

        if status.startswith("✅ Live"):

            with open(output_file, "a", encoding="utf-8") as f:
                f.write(group_id + "\n")
        task_queue.task_done()
def update_ui():
    """Cập nhật UI từ hàng đợi để tránh đơ."""
    while not update_queue.empty():
        item, new_values = update_queue.get()
        tree.item(item, values=new_values)
    update_status()
    root.after(100, update_ui)  # Lặp lại sau 100ms để cập nhật tiếp


# 🛠 Hàm chạy kiểm tra đa luồng
def check_live():
    num_threads = int(threads_entry.get())

    # Đưa tất cả bài post vào hàng đợi
    for item in tree.get_children():
        task_queue.put(item)

    # Khởi chạy các luồng worker
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()

    root.after(100, update_ui)  # Bắt đầu cập nhật UI liên tục

    # 🛠 Thông báo hoàn thành
    messagebox.showinfo("Hoàn thành", f"✅ Kiểm tra xong! Kết quả lưu tại: {output_file}")
def on_treeview_click(event):
    """ Xác định ô được click trong Treeview """
    item = tree.identify_row(event.y)  # Lấy ID hàng
    column = tree.identify_column(event.x)  # Lấy ID cột (dạng '#1', '#2', ...)
    
    if item and column:
        global selected_cell
        selected_cell = (item, column)  # Lưu lại ô đã chọn

def copy_selected(event):
    """ Sao chép nội dung của ô được chọn """
    if selected_cell:
        item, column = selected_cell
        column_index = int(column[1:]) - 1  # Chuyển '#2' -> 1 (index-based)
        values = tree.item(item, "values")
        
        if column_index < len(values):  # Kiểm tra nếu cột hợp lệ
            copied_text = values[column_index]
            root.clipboard_clear()
            root.clipboard_append(copied_text)
            root.update()
def sort_treeview_column(col, reverse):
    """ Sắp xếp dữ liệu trong Treeview khi click vào tiêu đề """
    data = []
    
    for item in tree.get_children(""):
        value = tree.set(item, col)  # Lấy giá trị của cột
        try:
            value = float(value) if value.replace(".", "", 1).isdigit() else value  # Chuyển thành số nếu có thể
        except ValueError:
            pass  # Giữ nguyên nếu không thể chuyển đổi

        data.append((value, item))

    # **Sắp xếp với điều kiện kiểu dữ liệu**
    data.sort(key=lambda x: (isinstance(x[0], str), x[0]), reverse=reverse)

    # Cập nhật thứ tự hiển thị trong Treeview
    for index, (_, item) in enumerate(data):
        tree.move(item, "", index)

    # Đảo chiều sắp xếp cho lần click tiếp theo
    tree.heading(col, command=lambda: sort_treeview_column(col, not reverse))
def update_status():
    total = len(tree.get_children())
    live_count = sum(1 for item in tree.get_children() if "✅" in tree.item(item, "values")[3])
    lbl_status.config(text=f"Live: {live_count} / Tổng Số: {total}")

def clear_treeview():
    """Xóa toàn bộ dữ liệu trong Treeview"""
    for item in tree.get_children():
        tree.delete(item)
def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not file_path:
        return
    
    entry_file.delete(0, END)
    entry_file.insert(0, file_path)

    # Tạo tên file kết quả tự động
    global output_file
    output_file = file_path.replace(".txt", "_checked.txt")
    if not os.path.exists(output_file):
        open(output_file, "w", encoding="utf-8").close()

    # Xóa dữ liệu cũ trong Treeview
    for row in tree.get_children():
        tree.delete(row)

    # Đọc file và hiển thị lên Treeview
    with open(file_path, "r", encoding="utf-8") as file:
        for idx, line in enumerate(file, start=1):
            post_url = line.strip()
            if post_url:
                post_id = post_url.split("/")[-1]
                tree.insert("", "end", values=(idx, post_url, post_id, "⏳ Chưa kiểm tra"))
    update_status()

BG_COLOR = "#F0F0F0"  # Màu nền
BTN_COLOR = "#007BFF"  # Màu nút
FONT = ("Arial", 10)
# **Tạo giao diện Tkinter**
root = Tk()
root.title("ADz Tool - Quét UID - Smarttraffic.App")
root.geometry("1200x700")
root.configure(bg="#F0F0F0")

# Khu vực nhập thông tin
frame_top = Frame(root, bg="#F0F0F0")
frame_top.pack(fill="x", padx=10, pady=5)

Label(frame_top, text="Chọn file:", font=FONT, bg=BG_COLOR).pack(side=LEFT, padx=5)
entry_file = Entry(frame_top, font=FONT, width=50)
entry_file.pack(side=LEFT, padx=5)
btn_browse = Button(frame_top, text="Tải lên", font=FONT, command=load_file, bg=BTN_COLOR, fg="white")
btn_browse.pack(side=LEFT, padx=5)

# Khu vực cài đặt
frame_settings = Frame(root, bg="#F0F0F0")
frame_settings.pack(fill="x", padx=10, pady=5)



Label(frame_settings, text="Số Luồng", font=("Arial", 10), bg="#F0F0F0").grid(row=0, column=2, padx=5, sticky="w")
threads_entry = Entry(frame_settings, width=10)
threads_entry.insert(0, "50")
threads_entry.grid(row=0, column=3, padx=5)
# Label hiển thị số lượt share
lbl_status = Label(root, text="Live: 0 / Tổng Số: 0", font=("Arial", 10), bg="#F0F0F0")
lbl_status.pack(pady=5)

# **Frame chứa bảng**
frame_logs = Frame(root, bg="#F0F0F0")
frame_logs.pack(fill="both", expand=True, padx=10, pady=5)

# **Thanh cuộn**
scrollbar_y = Scrollbar(frame_logs, orient=VERTICAL)
scrollbar_y.pack(side=RIGHT, fill=Y)

scrollbar_x = Scrollbar(frame_logs, orient=HORIZONTAL)
scrollbar_x.pack(side=BOTTOM, fill=X)

# **Tạo Treeview với kiểu bảng**
tree = ttk.Treeview(frame_logs, columns=("STT", "Post URL", "Post ID", "Status"),
                    show="headings", yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

tree.pack(fill="both", expand=True)

# **Liên kết thanh cuộn với Treeview**
scrollbar_y.config(command=tree.yview)
scrollbar_x.config(command=tree.xview)

# **Định nghĩa cột**
tree.heading("STT", text="STT")
tree.heading("Post URL", text="Post URL")
tree.heading("Post ID", text="Post ID")
tree.heading("Status", text="Status")

tree.column("STT", width=20, anchor=CENTER)
tree.column("Post URL", width=250, anchor=W)
tree.column("Post ID", width=150, anchor=CENTER)
tree.column("Status", width=150, anchor=W)

# **Style để tạo đường kẻ**
style = ttk.Style()
style.configure("Treeview", rowheight=25, background="#F8F8F8", borderwidth=1, relief="solid")
style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#E0E0E0", relief="raised")
style.map("Treeview", background=[("selected", "#C0C0C0")])

# **Thêm hiệu ứng kẻ dòng xen kẽ**
tree.tag_configure("oddrow", background="#EAEAEA")  # Màu xám nhạt
tree.tag_configure("evenrow", background="#FFFFFF")  # Màu trắng

# Gán sự kiện click vào tiêu đề để sắp xếp
columns = ("STT", "Post URL", "Post ID", "Status")
for col in columns:
    tree.heading(col, text=col, command=lambda c=col: sort_treeview_column(c, False))

# Biến lưu ô đã chọn
selected_cell = None

# Gán sự kiện click chuột để chọn ô
tree.bind("<ButtonRelease-1>", on_treeview_click)

# Gán Ctrl + C để copy nội dung của ô
tree.bind("<Control-c>", copy_selected)
# Gán sự kiện click vào tiêu đề để sắp xếp
columns = ("STT", "Post URL", "Post ID", "Status")
for col in columns:
    tree.heading(col, text=col, command=lambda c=col: sort_treeview_column(c, False))
# **Nút điều khiển**
button_frame = Frame(root, bg="#F0F0F0")
button_frame.pack(pady=10)

# **Thêm nút `Kiểm Tra Live Post` vào button_frame**
check_live_button = Button(button_frame, text="Kiểm Tra Live Post", font=("Arial", 12),command=lambda: threading.Thread(target=check_live).start(), bg="Orange", fg="white", width=20)
check_live_button.grid(row=0, column=3, padx=10)

root.mainloop()
