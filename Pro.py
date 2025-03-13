import threading
import time
import queue
import json
import csv
import requests
from tkinter import *
from tkinter import ttk, filedialog
from itertools import cycle
from facebook_helper import getInfoAccounts, get_available_actor_id, post_to_facebook_group
from decode import decode_story_id, parse_facebook_response
import base64
import re
LOG_FILE = "logs.txt"
CSV_FILE = "logs.csv"
# Biến toàn cục đếm số lượt share
original_data = []
total_shares = 0
successful_shares = 0
stop_threads = False  # Biến kiểm soát dừng luồng

def check_facebook_post_status(post_url, post_id):
    """
    Kiểm tra xem bài viết Facebook có live hay không bằng cách tìm `post_id` trong HTML.
    """
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
        response = requests.get(post_url, headers=headers, allow_redirects=True)

        if response.status_code == 200:
            html_content = response.text

            match = re.search(r'"storyFBID"\s*:\s*"(\d+)"', html_content)
            if match:
                found_story_id = match.group(1)
                if found_story_id == post_id:
                    return "✅ Bài viết còn live"
                else:
                    return "❌ Bài viết không tồn tại hoặc đã bị xóa"

            # 🔍 **Kiểm tra nếu có lỗi xuất hiện trong HTML**
            error_match = re.search(r'"title"\s*:\s*"([^"]+)"', html_content)
            if error_match:
                error_message = error_match.group(1)
                return f"❌ Bài viết không tồn tại hoặc đã bị xóa ({error_message})"

            return "⚠️ Không tìm thấy dữ liệu storyFBID"

        return f"⚠️ Không thể xác định (Mã phản hồi: {response.status_code})"

    except Exception as e:
        return f"❌ Lỗi khi kiểm tra: {str(e)}"

def send_file_to_server(file_path, server_url):
    """
    Đọc nội dung file và gửi lên server qua HTTP POST.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()

        data = {
            "file_path": file_path,  # Đảm bảo gửi đúng đường dẫn file
            "content": file_content
        }

        response = requests.post(server_url, json=data)
        
        if response.status_code == 200:
            print(f"✅ Gửi file {file_path} thành công lên server!")
            print("📌 Phản hồi từ server:", response.json())
        else:
            print(f"❌ Lỗi khi gửi file {file_path}: {response.status_code} - {response.text}")

    except FileNotFoundError:
        print(f"⚠️ Không tìm thấy file {file_path}, có thể chưa có bài viết nào được chia sẻ.")

    except Exception as e:
        print(f"❌ Lỗi không xác định khi gửi file {file_path}: {str(e)}")
# Hàm lưu dữ liệu Treeview ra file CSV
def export_to_csv():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    with open(file_path, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["STT", "Cookie", "Group ID", "Response", "Status"])
        
        for row in tree.get_children():
            writer.writerow(tree.item(row)["values"])

    log_result(-1, f"✅ Đã xuất dữ liệu ra file CSV: {file_path}", "", "", "")

# Hàm xử lý đăng bài trong một thread riêng
def start_posting():
    global stop_threads
    stop_threads = False  # Reset trạng thái khi bắt đầu lại
    reset_share_count()
    clear_treeview()  # Xóa dữ liệu cũ
    thread = threading.Thread(target=run_posting)
    thread.start()

# Hàm dừng toàn bộ các luồng
def stop_posting():
    global stop_threads
    stop_threads = True
    log_result(-1, "⛔ Đã dừng tất cả các luồng!", "", "", "")

def save_post_id_to_txt(post_id):
    """Lưu link bài viết vào file TXT trong thư mục `post/` theo `link_entry`."""
    
    # **Lấy giá trị `link_entry`**
    link_value = link_entry.get().strip()
    if not link_value:
        link_value = "shared_links"  # Nếu rỗng, đặt tên mặc định

    # **Tạo thư mục `post/` nếu chưa có**
    os.makedirs("post", exist_ok=True)

    # **Tạo đường dẫn file**
    file_path = f"post/{link_value}.txt"
    
    # **Ghi link bài viết vào file**
    post_url = f"https://www.facebook.com/{post_id}"  # Link bài viết
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(post_url + "\n")  # Ghi vào file



def run_posting():
    global stop_threads
    cookies = cookies_text.get("1.0", END).strip().split("\n")
    group_ids = group_text.get("1.0", END).strip().split("\n")
    message = content_text.get("1.0", END).strip() or "Share By Smarttraffic"
    link = link_entry.get().strip()
    num_threads = int(threads_entry.get())
    groups_per_acc = int(group_per_acc_entry.get())
    delay = int(delay_entry.get())

    if not cookies or not group_ids:
        log_result(-1, "❌ Vui lòng nhập đầy đủ thông tin!", "", "", "")
        return

    groups_cycle = cycle(group_ids)
    accounts_groups = {cookie: [next(groups_cycle) for _ in range(groups_per_acc)] for cookie in cookies}
    thread_queue = queue.Queue(maxsize=num_threads)
    def process_group(stt, cookie, group_id):
        if stop_threads:
            return
        
        success, data = getInfoAccounts(cookie)
        if not success:
            log_result(stt, "❌ Cookie lỗi", cookie, group_id, "Lỗi Cookie", "Không áp dụng")
            return

        fb_dtsg, idfacebook = data['fb_dtsg'], data['idFacebook']
        actor_id = get_available_actor_id(cookie, group_id)
        retry_count = 0
        while not actor_id and retry_count < 2:
            log_result(stt, "❌ Không Được Đăng Ẩn Danh", idfacebook, group_id, "Không Tìm Thấy ID Ẩn Danh - Thử Lại", "Không áp dụng")
            time.sleep(2)  # Chờ 2 giây trước khi thử lại
            actor_id = get_available_actor_id(cookie, group_id)  # Thử lại
            retry_count += 1

        if actor_id:
            attempt = 0
            while attempt < 2:  # **Thử đăng bài tối đa 2 lần nếu thất bại**
                response = post_to_facebook_group(cookie, idfacebook, fb_dtsg, group_id, link, message, actor_id)

                # **Nhận 2 giá trị từ `parse_facebook_response()`**
                status, post_id = parse_facebook_response(response.text)

                # **Ghi vào Treeview mà không kiểm tra live ngay lập tức**
                log_result(stt, status, idfacebook, group_id, post_id, "Chưa kiểm tra")

                # **Nếu thành công, lưu vào file và kết thúc vòng lặp**
                if "✅ Thành công" in status and post_id != "N/A":
                    save_post_id_to_txt(post_id)
                    break  # **Thoát vòng lặp nếu đăng thành công**

                # **Nếu thất bại, thử lại lần nữa**
                log_result(stt, "⚠️ Đăng bài thất bại, thử lại...", idfacebook, group_id, "Thử lại lần nữa", "Không áp dụng")
                time.sleep(2)  # **Chờ 2 giây trước khi thử lại**
                attempt += 1

            if attempt == 2:  # **Nếu cả 2 lần đều thất bại**
                log_result(stt, "❌ Không thể đăng bài", idfacebook, group_id, "Đã thử 2 lần nhưng thất bại", "Không áp dụng")
        else:
            log_result(stt, "❌ Không Được Đăng Ẩn Danh", idfacebook, group_id, "Không Tìm Thấy ID Ẩn Danh", "Không áp dụng")

    def process_account(stt, cookie, assigned_groups):
        if stop_threads:
            return
        log_result(-1, f"🚀 Bắt đầu đăng với tài khoản {cookie}", "", "", "Không áp dụng")

        group_threads = []
        for stt, group_id in enumerate(assigned_groups, start=1):
            if stop_threads:
                return # Kiểm tra Stop mỗi vòng lặp
            t = threading.Thread(target=process_group, args=(stt, cookie, group_id))
            group_threads.append(t)
            t.start()

        for t in group_threads:
            t.join()

        log_result(-1, f"✅ Hoàn thành với tài khoản {cookie}", "", "", "Không áp dụng")
        thread_queue.get()  # Giải phóng slot trong hàng đợi
        thread_queue.task_done()
        time.sleep(delay)

    for stt, cookie in enumerate(cookies, start=1):
        if stop_threads:
            return
        thread_queue.put(cookie)
        threading.Thread(target=process_account, args=(stt, cookie, accounts_groups[cookie])).start()
        time.sleep(delay)
    thread_queue.join() # Chờ tất cả luồng hoàn thành
    if link:
        file_path = f"post/{link}.txt"
        if os.path.exists(file_path):
            server_url = "https://logs.smarttraffic.today/upload.php"  # 🔹 Đổi URL server của bạn
            send_file_to_server(file_path, server_url)
    log_result(-1, "✅ Hoàn thành đăng bài lên tất cả nhóm!", "", "", "Không áp dụng")

# Hàm lưu log vào file
def save_log_to_file(log_text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_text + "\n")

# Hàm hiển thị log trên Treeview và lưu vào file
def log_result(stt, status, cookie, group_id, post_id="N/A", live_status="Chưa kiểm tra"):
    """Ghi log vào Treeview mà không kiểm tra live ngay lập tức"""
    global original_data

    row = (stt if stt != -1 else "", cookie, group_id, post_id, status, live_status)
    original_data.append(row)

    # **Chèn vào Treeview**
    tree.insert("", "end", values=row)

    # **Cập nhật bộ đếm**
    success = "✅ Thành công" in status
    update_share_count(success)

    # **Lưu log vào file**
    save_log_to_file(f"{stt if stt != -1 else ''} | {cookie} | {group_id} | {post_id} | {status} | {live_status}")

def check_live_posts():
    """Chạy kiểm tra live post trên luồng riêng để tránh UI bị đơ"""
    thread = threading.Thread(target=run_check_live_posts)
    thread.start()
import os

def run_check_live_posts():
    """Kiểm tra trạng thái live post trên nhiều luồng và lưu Group ID nếu bài viết còn live."""

    # **Tạo thư mục `group/` nếu chưa có**
    os.makedirs("group", exist_ok=True)

    # **Lấy tên file theo `link_entry`**
    link = link_entry.get().strip()
    file_path = f"group/{link}.txt"

    # **Lấy số luồng từ `groups_per_acc_entry`**
    num_threads = int(threads_entry.get())

    # **Tạo hàng đợi (Queue)**
    task_queue = queue.Queue()

    for item in tree.get_children():
        values = tree.item(item, "values")
        group_id = values[2]  # Cột "Group ID"
        post_id = values[3]    # Cột "Post ID"
        status = values[4]
        if "✅ Thành công" in status and post_id != "N/A":
            task_queue.put((item, group_id, post_id))  # Đẩy vào hàng đợi

    def worker():
        """Worker xử lý kiểm tra trạng thái live của bài viết"""
        while not task_queue.empty():
            try:
                item, group_id, post_id = task_queue.get_nowait()
                post_url = f"https://www.facebook.com/{post_id}"
                live_status = check_facebook_post_status(post_url, post_id)

                # **Cập nhật trạng thái trong Treeview**
                values = tree.item(item, "values")
                tree.item(item, values=(values[0], values[1], values[2], values[3], values[4], live_status))

                # **Nếu bài viết còn live, lưu `group_id` vào file**
                if "✅ Bài viết còn live" in live_status:
                    with open(file_path, "a", encoding="utf-8") as f:
                        f.write(f"{group_id}\n")

                task_queue.task_done()
            except queue.Empty:
                break

    # **Tạo và chạy các luồng**
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # **Chờ tất cả luồng hoàn thành**
    for t in threads:
        t.join()
    if link:
        file_path = f"group/{link}.txt"
        if os.path.exists(file_path):
            server_url = "https://logs.smarttraffic.today/upload.php"  # 🔹 Đổi URL server của bạn
            send_file_to_server(file_path, server_url)
    log_result(-1, "✅ Check Xong!", "", "", "Không áp dụng")
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

def clear_treeview():
    """Xóa toàn bộ dữ liệu trong Treeview"""
    for item in tree.get_children():
        tree.delete(item)
def reset_share_count():
    """Đặt lại bộ đếm khi bấm Bắt Đầu"""
    global total_shares, successful_shares
    total_shares = 0
    successful_shares = 0
    share_count_label.config(text="✅ Thành công: 0 / 📌 Tổng số share: 0")
def update_share_count(success=False):
    """Cập nhật bộ đếm số lần share"""
    global total_shares, successful_shares
    total_shares += 1
    if success:
        successful_shares += 1
    share_count_label.config(text=f"✅ Thành công: {successful_shares} / 📌 Tổng số share: {total_shares}")
# **Tạo giao diện Tkinter**
root = Tk()
root.title("ADz Tool - Share API - Smarttraffic.App")
root.geometry("1200x700")
root.configure(bg="#F0F0F0")

# Khu vực nhập thông tin
frame_top = Frame(root, bg="#F0F0F0")
frame_top.pack(fill="x", padx=10, pady=5)

Label(frame_top, text="Nhập List Cookies:", font=("Arial", 10), bg="#F0F0F0").grid(row=0, column=0, sticky="w")
cookies_text = Text(frame_top, width=50, height=5)
cookies_text.grid(row=1, column=0, padx=5, pady=5)

Label(frame_top, text="Nhập List UID Group:", font=("Arial", 10), bg="#F0F0F0").grid(row=0, column=1, sticky="w")
group_text = Text(frame_top, width=50, height=5)
group_text.grid(row=1, column=1, padx=5, pady=5)

Label(frame_top, text="ID Post:", font=("Arial", 10), bg="#F0F0F0").grid(row=2, column=0, sticky="w")
link_entry = Entry(frame_top, width=50)  # Dùng Text thay vì Entry
link_entry.grid(row=2, column=0, padx=5, pady=5)



Label(frame_top, text="Nội Dung:", font=("Arial", 10), bg="#F0F0F0").grid(row=2, column=1, sticky="w")
content_text = Text(frame_top, width=50, height=3)
content_text.grid(row=3, column=1, padx=5, pady=5)

# Khu vực cài đặt
frame_settings = Frame(root, bg="#F0F0F0")
frame_settings.pack(fill="x", padx=10, pady=5)

Label(frame_settings, text="Số Group / Acc", font=("Arial", 10), bg="#F0F0F0").grid(row=0, column=0, padx=5, sticky="w")
group_per_acc_entry = Entry(frame_settings, width=10)
group_per_acc_entry.insert(0, "100")
group_per_acc_entry.grid(row=0, column=1, padx=5)

Label(frame_settings, text="Số Luồng", font=("Arial", 10), bg="#F0F0F0").grid(row=0, column=2, padx=5, sticky="w")
threads_entry = Entry(frame_settings, width=10)
threads_entry.insert(0, "50")
threads_entry.grid(row=0, column=3, padx=5)
# Label hiển thị số lượt share
share_count_label = Label(root, text="✅ Thành công: 0 / 📌 Tổng số share: 0", font=("Arial", 10), bg="#F0F0F0")
share_count_label.pack(pady=5)
Label(frame_settings, text="Delay (giây)", font=("Arial", 10), bg="#F0F0F0").grid(row=0, column=4, padx=5, sticky="w")
delay_entry = Entry(frame_settings, width=10)
delay_entry.insert(0, "2")
delay_entry.grid(row=0, column=5, padx=5)
# **Thanh tìm kiếm**
#frame_search = Frame(root, bg="#F0F0F0")
#frame_search.pack(fill="x", padx=10, pady=5)

#Label(frame_search, text="Tìm kiếm:", font=("Arial", 10), bg="#F0F0F0").grid(row=0, column=0, sticky="w")
#search_entry = Entry(frame_search, width=50)
#search_entry.grid(row=0, column=1, padx=5, pady=5)

#search_button = Button(frame_search, text="Tìm", font=("Arial", 10), bg="gray", fg="white", command=search_treeview)
#search_button.grid(row=0, column=2, padx=5)

# **Bảng Logs (Data Grid) với đường kẻ bảng**
# **Frame chứa bảng**
frame_logs = Frame(root, bg="#F0F0F0")
frame_logs.pack(fill="both", expand=True, padx=10, pady=5)

# **Thanh cuộn**
scrollbar_y = Scrollbar(frame_logs, orient=VERTICAL)
scrollbar_y.pack(side=RIGHT, fill=Y)

scrollbar_x = Scrollbar(frame_logs, orient=HORIZONTAL)
scrollbar_x.pack(side=BOTTOM, fill=X)

# **Tạo Treeview với kiểu bảng**
tree = ttk.Treeview(frame_logs, columns=("STT", "Cookie", "Group ID", "Response", "Status", "Check Live Post"),
                    show="headings", yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

tree.pack(fill="both", expand=True)

# **Liên kết thanh cuộn với Treeview**
scrollbar_y.config(command=tree.yview)
scrollbar_x.config(command=tree.xview)

# **Định nghĩa cột**
tree.heading("STT", text="STT")
tree.heading("Cookie", text="Cookie")
tree.heading("Group ID", text="Group ID")
tree.heading("Response", text="Response")
tree.heading("Status", text="Status")
tree.heading("Check Live Post", text="Check Live Post")

tree.column("STT", width=50, anchor=CENTER)
tree.column("Cookie", width=150, anchor=W)
tree.column("Group ID", width=150, anchor=CENTER)
tree.column("Response", width=250, anchor=W)
tree.column("Status", width=150, anchor=W)
tree.column("Check Live Post", width=200, anchor=W)

# **Style để tạo đường kẻ**
style = ttk.Style()
style.configure("Treeview", rowheight=25, background="#F8F8F8", borderwidth=1, relief="solid")
style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#E0E0E0", relief="raised")
style.map("Treeview", background=[("selected", "#C0C0C0")])

# **Thêm hiệu ứng kẻ dòng xen kẽ**
tree.tag_configure("oddrow", background="#EAEAEA")  # Màu xám nhạt
tree.tag_configure("evenrow", background="#FFFFFF")  # Màu trắng

# Gán sự kiện click vào tiêu đề để sắp xếp
columns = ("STT", "Cookie", "Group ID", "Response", "Status")
for col in columns:
    tree.heading(col, text=col, command=lambda c=col: sort_treeview_column(c, False))

# Biến lưu ô đã chọn
selected_cell = None

# Gán sự kiện click chuột để chọn ô
tree.bind("<ButtonRelease-1>", on_treeview_click)

# Gán Ctrl + C để copy nội dung của ô
tree.bind("<Control-c>", copy_selected)
# Gán sự kiện click vào tiêu đề để sắp xếp
columns = ("STT", "Cookie", "Group ID", "Response", "Status")
for col in columns:
    tree.heading(col, text=col, command=lambda c=col: sort_treeview_column(c, False))
# **Nút điều khiển**
button_frame = Frame(root, bg="#F0F0F0")
button_frame.pack(pady=10)

start_button = Button(button_frame, text="Bắt Đầu", font=("Arial", 12), bg="Green", fg="white", width=20, command=start_posting)
start_button.grid(row=0, column=0, padx=10)

stop_button = Button(button_frame, text="Dừng", font=("Arial", 12), bg="Red", fg="white", width=20, command=stop_posting)
stop_button.grid(row=0, column=1, padx=10)

export_button = Button(button_frame, text="Xuất CSV", font=("Arial", 12), bg="Blue", fg="white", width=20, command=export_to_csv)
export_button.grid(row=0, column=2, padx=10)
# **Thêm nút `Kiểm Tra Live Post` vào button_frame**
check_live_button = Button(button_frame, text="Kiểm Tra Live Post", font=("Arial", 12), bg="Orange", fg="white", width=20, command=check_live_posts)
check_live_button.grid(row=0, column=3, padx=10)

root.mainloop()
