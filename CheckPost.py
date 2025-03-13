import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import requests
import re
import os
import queue

# 🎨 Cấu hình giao diện
BG_COLOR = "#F8F9FA"  # Màu nền
BTN_COLOR = "#007BFF"  # Màu nút
FONT = ("Arial", 10)
# Hàng đợi các bài post cần kiểm tra
task_queue = queue.Queue()
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


def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not file_path:
        return
    
    entry_file.delete(0, tk.END)
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


# 🛠 Cập nhật số live/tổng số bài viết liên tục
def update_status():
    total = len(tree.get_children())
    live_count = sum(1 for item in tree.get_children() if "✅" in tree.item(item, "values")[3])
    lbl_status.config(text=f"📊 Live: {live_count} / {total}")
def save_group_ids(group_ids):
    file_name = output_file
    if not file_name:
        file_name = "group_ids"

    file_path = f"{file_name}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for group_id in set(group_ids):  # Tránh trùng lặp
            f.write(group_id + "\n")
# 🛠 Worker xử lý bài post trong hàng đợi
def worker():
    while not task_queue.empty():
        item = task_queue.get()
        values = tree.item(item, "values")
        stt, post_url, post_id, _ = values

        status, group_id = check_facebook_post_status(post_url, post_id)

        tree.item(item, values=(stt, post_url, post_id, status))

        # Lưu group_id nếu bài viết còn live
        print(f"🛠 Đang kiểm tra: {post_id} - Trạng thái: {status}")
        if status.startswith("✅ Live"):
            print(f"📝 Ghi {group_id} vào {output_file}")
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(group_id + "\n")
                print(f"📂 Đã ghi group_id {group_id} vào file {output_file}")

        # 🛠 Cập nhật số lượng live liên tục
        root.after(0, update_status)
        task_queue.task_done()

# 🛠 Hàm chạy kiểm tra đa luồng
def check_live():
    num_threads = int(entry_threads.get())

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

    update_status()  # Đảm bảo cập nhật sau khi chạy xong

    # 🛠 Thông báo hoàn thành
    messagebox.showinfo("Hoàn thành", f"✅ Kiểm tra xong! Kết quả lưu tại: {output_file}")
def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not file_path:
        return
    
    entry_file.delete(0, tk.END)
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


# 🛠 Giao diện Tkinter
root = tk.Tk()
root.title("📌 Facebook Post Checker")
root.geometry("800x600")
root.configure(bg=BG_COLOR)

# 📂 Chọn file
frame_top = tk.Frame(root, bg=BG_COLOR)
frame_top.pack(pady=10)

tk.Label(frame_top, text="📂 Chọn file:", font=FONT, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)
entry_file = tk.Entry(frame_top, font=FONT, width=50)
entry_file.pack(side=tk.LEFT, padx=5)
btn_browse = tk.Button(frame_top, text="🔍 Tải lên", font=FONT, command=load_file, bg=BTN_COLOR, fg="white")
btn_browse.pack(side=tk.LEFT, padx=5)

# 🌲 Treeview
frame_tree = tk.Frame(root)
frame_tree.pack(pady=10, fill=tk.BOTH, expand=True)

tree_scroll_y = tk.Scrollbar(frame_tree, orient=tk.VERTICAL)
tree_scroll_x = tk.Scrollbar(frame_tree, orient=tk.HORIZONTAL)

tree = ttk.Treeview(frame_tree, columns=("STT", "Post URL", "Post ID", "Status"), show="headings",
                     yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

tree_scroll_y.config(command=tree.yview)
tree_scroll_x.config(command=tree.xview)

tree.heading("STT", text="🔢 STT")
tree.heading("Post URL", text="📌 Post URL")
tree.heading("Post ID", text="🆔 Post ID")
tree.heading("Status", text="📊 Trạng thái")

tree.column("STT", width=50, anchor="center")
tree.column("Post URL", width=350)
tree.column("Post ID", width=120, anchor="center")
tree.column("Status", width=150, anchor="center")

tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
tree.pack(fill=tk.BOTH, expand=True)

# 🔢 Nhập số luồng
frame_bottom = tk.Frame(root, bg=BG_COLOR)
frame_bottom.pack(pady=5)

tk.Label(frame_bottom, text="⏳ Số luồng:", font=FONT, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)
entry_threads = tk.Entry(frame_bottom, font=FONT, width=5)
entry_threads.insert(0, "5")
entry_threads.pack(side=tk.LEFT, padx=5)

# 🎯 Nút kiểm tra live
btn_check = tk.Button(root, text="📌 Check Live", font=FONT, command=lambda: threading.Thread(target=check_live).start(), 
                      bg="#28A745", fg="white", width=15)
btn_check.pack(pady=10)

# 📊 Hiển thị số live
lbl_status = tk.Label(root, text="📊 Live: 0 / 0", font=("Arial", 14, "bold"), bg=BG_COLOR)
lbl_status.pack(pady=5)

root.mainloop()