import json
from tkinter import *
import base64
import re
def decode_story_id(story_id):
    """
    Giải mã `story_id` từ Base64 để lấy `owner_id` và `post_number`.
    """
    try:
        decoded_data = base64.b64decode(story_id).decode("utf-8")
        match = re.search(r'I(\d+):VK:(\d+)', decoded_data)
        if match:
            owner_id, post_number = match.groups()
            #return f"{owner_id}_{post_number}"
            return post_number
        return "❌ Không thể trích xuất post_id từ story_id"
    except Exception as e:
        return f"❌ Lỗi giải mã Base64: {str(e)}"


def parse_facebook_response(response_text):
    """
    Phân tích phản hồi từ `post_to_facebook_group` để lấy `post_id`, nhưng KHÔNG kiểm tra live.
    """
    try:
        response_data = json.loads(response_text)

        # Kiểm tra nếu có `story_id`
        story_data = response_data.get("data", {}).get("story_create", {})
        story_id = story_data.get("story_id")

        if story_id:
            post_id = decode_story_id(story_id)  # Giải mã `story_id` từ Base64
            return ("✅ Thành công", post_id)

        # Kiểm tra nếu có lỗi
        errors = response_data.get("errors", [])
        if errors:
            error_message = errors[0].get("message", "Lỗi không xác định")
            return ("❌ Lỗi", error_message)

    except json.JSONDecodeError:
        return ("❌ Lỗi", "Phản hồi không hợp lệ")

    return ("❌ Lỗi", "Không có `story_id` và không có lỗi rõ ràng")