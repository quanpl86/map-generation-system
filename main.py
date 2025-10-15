# main.py

# Import hàm main từ script nghiệp vụ thực sự.
# Chúng ta đổi tên nó thành 'generate_all_maps_main' để tránh nhầm lẫn
# với hàm 'main' của chính file này.
from scripts.generate_all_maps import main as generate_all_maps_main

def main():
    """
    Hàm chính của chương trình, đóng vai trò là điểm khởi chạy.
    Nó gọi đến logic sinh map thực sự nằm trong thư mục scripts.
    """
    print("============================================")
    print("=== KHỞI CHẠY TỪ ĐIỂM ĐẦU VÀO CHÍNH (main.py) ===")
    print("============================================")
    
    # Gọi hàm đã được import để bắt đầu quy trình sinh map
    generate_all_maps_main()
    
    print("\n============================================")
    print("=== KẾT THÚC TÁC VỤ TỪ main.py ===")
    print("============================================")


if __name__ == "__main__":
    # Dòng này đảm bảo rằng hàm main() chỉ được chạy khi file này
    # được thực thi trực tiếp, không phải khi nó được import bởi một file khác.
    main()